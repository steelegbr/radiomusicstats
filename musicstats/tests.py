"""
MusicStats unit tests
"""

import json
from datetime import datetime, time
from parameterized import parameterized
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from musicstats.models import (
    Station,
    Artist,
    Song,
    SongPlay,
    EpgEntry,
    MarketingLiner,
    Presenter,
)
from musicstats.epg import OnAir2Parser, EpgSynchroniser
from musicstats.presenters import (
    WordpressPresenterParser,
    WordpressPresenterImage,
    PresenterSynchroniser,
)


class TestIndex(APITestCase):
    """
    Tests we can access the index.
    """

    def test_index(self):
        """
        Checks the index returns the static content
        """

        url = reverse("index")
        response = self.client.get(url)
        self.assertEqual(response.content, b"Hello from the musicstats index.")


class StationTestCase(APITestCase):
    """
    Tests station API endpoints.
    """

    username = "station_test"
    password = "testcase_01"
    email = "test@example.com"
    station_name = "Test FM"
    station_slogan = "Testing your ears... for something!"
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Create a test station ready for the next stage.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
        )

    def test_station_create(self):
        """
        Tests we can create the station and access it correctly
        """

        self.station.save()

        url = reverse("station-detail", kwargs={"name": self.station_name})
        response = self.client.get(url)
        json_response = json.loads(response.content)

        self.assertEqual(json_response["name"], self.station.name)
        self.assertEqual(json_response["slogan"], self.station.slogan)
        self.assertEqual(json_response["primary_colour"], self.station.primary_colour)
        self.assertEqual(json_response["text_colour"], self.station.text_colour)
        self.assertEqual(json_response["stream_aac_high"], self.station.stream_aac_high)
        self.assertEqual(json_response["stream_aac_low"], self.station.stream_aac_low)
        self.assertEqual(json_response["stream_mp3_high"], self.station.stream_mp3_high)
        self.assertEqual(json_response["stream_mp3_low"], self.station.stream_mp3_low)
        self.assertEqual(json_response["use_liners"], self.station.use_liners)
        self.assertEqual(float(json_response["liner_ratio"]), self.station.liner_ratio)

        self.station.delete()


class LogSongplayTest(APITestCase):
    """
    Tests the log songplay functionality
    """

    valid_username = "real_station_user"
    valid_password = "P@55w0rd!"
    valid_email = "valid@user.creds"
    invalid_username = "fake_station_user"
    invalid_password = "SuperSecr3t!"
    invalid_email = "invalid@user.creds"
    station_name = "Logging FM"
    station_slogan = "More wood cutting variety!"
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        valid_user = User.objects.create_user(
            self.valid_username, self.valid_email, self.valid_password
        )
        invalid_user = User.objects.create_user(
            self.invalid_username, self.invalid_email, self.invalid_password
        )

        self.valid_token = Token.objects.create(user=valid_user)
        self.invalid_token = Token.objects.create(user=invalid_user)

        station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=valid_user,
        )

        station.save()

    def test_log_songplay(self):
        """
        Tests we can successfully log a songplay.
        """

        # Work out the URL and use valid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # Post and check our valid songplay

        songplay = {
            "song": {
                "display_artist": "The Singers and Lord Voldemort",
                "artists": ["Lord Voldemort", "The Singers"],
                "title": "Songy McSongFace",
            },
            "station": self.station_name,
        }

        response = self.client.post(url, songplay, format="json")
        response_json = json.loads(response.content)

        self.assertEqual(
            response_json["song"]["display_artist"], songplay["song"]["display_artist"]
        )
        self.assertEqual(response_json["song"]["artists"], songplay["song"]["artists"])
        self.assertEqual(response_json["song"]["title"], songplay["song"]["title"])
        self.assertEqual(response_json["station"], self.station_name)

    def test_invalid_station(self):
        """
        Tests we can't log against an invalid station.
        """

        # Work out the URL and use valid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # Post and check our valid songplay

        songplay = {
            "song": {
                "display_artist": "Invalid Singer",
                "artists": ["Invalid Singer"],
                "title": "Invalid Song",
            },
            "station": "Invalid FM",
        }

        response = self.client.post(url, songplay, format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_user(self):
        """
        Checks an invalid user can't log against a valid station.
        """

        # Work out the URL and use invalid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.invalid_token}")

        # Attempt the request

        songplay = {
            "song": {
                "display_artist": "Valid Singer",
                "artists": ["Valid Singer"],
                "title": "Valid Song",
            },
            "station": self.station_name,
        }

        response = self.client.post(url, songplay, format="json")
        self.assertEqual(response.status_code, 401)

    def test_song_sequence(self):
        """
        Checks we can't play the same song back to back.
        Though we do allow it later.
        """

        # Work out the URL and use invalid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # The songs we'll be using

        songplays = [
            {
                "song": {
                    "display_artist": "Singer 0",
                    "artists": ["Singer 0"],
                    "title": "Song 0",
                },
                "station": self.station_name,
            },
            {
                "song": {
                    "display_artist": "Singer 1",
                    "artists": ["Singer 1"],
                    "title": "Song 1",
                },
                "station": self.station_name,
            },
        ]

        # Our first song will be allowed

        response = self.client.post(url, songplays[0], format="json")
        self.assertEqual(response.status_code, 200)

        # Don't let us repeat it

        response = self.client.post(url, songplays[0], format="json")
        self.assertEqual(response.status_code, 400)

        # But allow a second song then come back

        response = self.client.post(url, songplays[1], format="json")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, songplays[0], format="json")
        self.assertEqual(response.status_code, 200)

    def test_repeat_artist(self):
        """
        Test the re-use of artists.
        """

        # Work out the URL and use invalid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # The songs we'll be using

        songplays = [
            {
                "song": {
                    "display_artist": "Singer A",
                    "artists": ["Singer A"],
                    "title": "Song A",
                },
                "station": self.station_name,
            },
            {
                "song": {
                    "display_artist": "Singer A",
                    "artists": ["Singer A"],
                    "title": "Song B",
                },
                "station": self.station_name,
            },
        ]

        # Our first song will be allowed

        response = self.client.post(url, songplays[0], format="json")
        self.assertEqual(response.status_code, 200)

        # And also allowed with the same artist

        response = self.client.post(url, songplays[1], format="json")
        self.assertEqual(response.status_code, 200)

    def test_invalid_songplay(self):
        """
        Checks invalid songplays don't get logged.
        """

        # Work out the URL and use valid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # Post and check our valid songplay

        songplay = {
            "song": {
                "display_artist": "Artist of the Week",
                "artists": ["Artist of the Week"],
            },
            "station": self.station_name,
        }

        response = self.client.post(url, songplay, format="json")
        self.assertEqual(response.status_code, 400)


class SongTestCase(APITestCase):
    """
    Song related tests.
    """

    username = "song_test"
    password = "S0ngT3st!"
    email = "song@example.com"
    artist = "Song Test Artist/Singer"
    title = "Song Test Title"

    def setUp(self):
        """
        Setup basic auth, dummy artist and song.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Create the artist

        artist = Artist(name=self.artist)

        artist.save()

        # Create the song

        song = Song(title=self.title, display_artist=self.artist)

        song.save()

        # Map them

        song.artists.add(artist)
        song.save()

    def test_get_song(self):
        """
        Tests we can successfully pull a song through the API.
        """

        # Grab the song

        url = reverse("song-detail", kwargs={"song": f"{self.artist} - {self.title}"})
        response = self.client.get(url)
        json_response = json.loads(response.content)

        #  Check it's the right one

        self.assertEqual(json_response["display_artist"], self.artist)
        self.assertEqual(json_response["title"], self.title)

    def test_nonexist_song(self):
        """
        Tests the retrieval of a non-existant song.
        """

        url = reverse("song-detail", kwargs={"song": "Nonsense Artist - Nonsense Song"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_badly_formatted_url(self):
        """
        Tests a badly formatted song URL
        """

        url = reverse(
            "song-detail", kwargs={"song": "Nonsense Artist by Nonsense Song"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class RetrieveSongPlay(APITestCase):
    """
    Test case for retrieving song plays.
    """

    username = "real_station_user"
    password = "P@55w0rd!"
    email = "valid@user.creds"
    station_name = "Song Play FM"
    station_slogan = "Songs and stuff."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

    def test_retrieve_songplays(self):
        """
        Makes sure we can retrieve song plays (in the right order)
        """

        # The songplays

        songplays = [
            {
                "song": {
                    "display_artist": "Songplay Artist",
                    "artists": ["Songplay Artist"],
                    "title": "Song A",
                },
                "station": self.station_name,
            },
            {
                "song": {
                    "display_artist": "Songplay Artist",
                    "artists": ["Songplay Artist"],
                    "title": "Song B",
                },
                "station": self.station_name,
            },
            {
                "song": {
                    "display_artist": "Songplay Artist",
                    "artists": ["Songplay Artist"],
                    "title": "Song C",
                },
                "station": self.station_name,
            },
        ]

        # Log them

        log_url = reverse("song_play_log")
        for songplay in songplays:
            response = self.client.post(log_url, songplay, format="json")
            self.assertEqual(response.status_code, 200)

        # Retrieve them

        url = reverse("song_play_recent", kwargs={"station_name": self.station_name})
        response = self.client.get(url)
        json_response = json.loads(response.content)

        # Check them off (reverse order)

        songplays.reverse()

        for index, songplay in enumerate(songplays):
            self.assertEqual(
                json_response[index]["song"]["title"], songplay["song"]["title"]
            )

    def test_songplay_timespan(self):
        """
        Tests pulling songplay data from specific times
        """

        # Create a songplay for testing with

        songplay = {
            "song": {
                "display_artist": "Songplay Artist",
                "artists": ["Songplay Artist"],
                "title": "Song A",
            },
            "station": self.station_name,
        }

        log_url = reverse("song_play_log")
        response = self.client.post(log_url, songplay, format="json")
        self.assertEqual(response.status_code, 200)

        # Search an empty range

        url = reverse(
            "song_play_specific",
            kwargs={
                "station_name": self.station_name,
                "start_time": 573782350,
                "end_time": 573782450,
            },
        )

        response = self.client.get(url)
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 0)

        # Search a more recent range

        url = reverse(
            "song_play_specific",
            kwargs={
                "station_name": self.station_name,
                "start_time": int(datetime.now().timestamp() - 3600),
                "end_time": int(datetime.now().timestamp() + 3600),
            },
        )

        response = self.client.get(url)
        json_response = json.loads(response.content)
        self.assertGreaterEqual(len(json_response), 1)

    def test_invalid_timespan(self):
        """
        Tests we get an error with an invalid timespan.
        """

        url = reverse(
            "song_play_specific",
            kwargs={
                "station_name": self.station_name,
                "start_time": 0,
                "end_time": 1569738775439843983915697387754398439839,
            },
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class EpgParserTest(APITestCase):
    """
    Test case for the OnAir 2 EPG parser.
    """

    username = "epg_user"
    password = "What50n?"
    email = "epg@example.com"
    station_name = "EPG AM"
    station_slogan = "Telling you what's on in the morning."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

        self.alt_station = Station(
            name="Alternate Digital",
            slogan="Another Station",
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.alt_station.save()

    def test_parse_epg(self):
        """
        Checks we can parse the EPG successfully
        """

        # Arrange

        content = open("./musicstats/test/epg.html", "r").read()

        # Act

        epg = OnAir2Parser().parse(content)

        # Assert
        # Check we've got the right number of entries

        self.assertIsNotNone(epg)
        self.assertEqual(9, len(epg[0]))
        self.assertEqual(9, len(epg[1]))
        self.assertEqual(10, len(epg[2]))
        self.assertEqual(10, len(epg[3]))
        self.assertEqual(11, len(epg[4]))
        self.assertEqual(10, len(epg[5]))
        self.assertEqual(9, len(epg[6]))

        # Sample a few of them
        # Monday Night Shift

        self.assertEqual("Night Shift", epg[0][0].title)
        self.assertEqual(
            "We don’t bore you with soppy love songs through the night shift. Instead, enjoy a great mix of songs, all night long.",
            epg[0][0].description,
        )
        self.assertEqual(
            "https://www.solidradio.co.uk/wp-content/uploads/2019/08/31548926930_f1a1103e5f_o.jpg",
            epg[0][0].image,
        )
        self.assertEqual(time(0, 0), epg[0][0].start)

        # Thursday 90s

        self.assertEqual("Solid Radio 90s", epg[3][4].title)
        self.assertEqual(
            "A solid hour of 90s songs on Solid Radio. It’s as simple as that!",
            epg[3][4].description,
        )
        self.assertEqual(
            "https://www.solidradio.co.uk/wp-content/uploads/2019/08/IMG_4543-2.jpg",
            epg[3][4].image,
        )
        self.assertEqual(time(13, 0), epg[3][4].start)

    def test_sync(self):
        """
        Tests the synchroniser does its job
        """

        # Arrange

        content = open("./musicstats/test/epg.html", "r").read()
        epg = OnAir2Parser().parse(content)

        # Act

        EpgSynchroniser().synchronise(self.station, epg)

        # Assert

        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=0).count()
        )
        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=1).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=2).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=3).count()
        )
        self.assertEqual(
            11, EpgEntry.objects.filter(station=self.station, day=4).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=5).count()
        )
        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=6).count()
        )

    def test_sync_with_delete(self):
        """
        Tests the synchroniser works with items to delete
        """

        # Arrange

        content = open("./musicstats/test/epg.html", "r").read()
        epg = OnAir2Parser().parse(content)

        odd_hour = EpgEntry()
        odd_hour.station = self.station
        odd_hour.start = time(4, 0)
        odd_hour.title = "Deleted Show"
        odd_hour.description = "Show to delete!"
        odd_hour.day = 0
        odd_hour.save()

        overlap_hour = EpgEntry()
        overlap_hour.station = self.station
        overlap_hour.start = time(10, 0)
        overlap_hour.title = "Overlap Show"
        overlap_hour.description = "GBTB"
        overlap_hour.day = 0
        overlap_hour.save()

        dead_hour = EpgEntry()
        dead_hour.station = self.station
        dead_hour.start = time(4, 0)
        dead_hour.title = "Dead Show"
        dead_hour.description = "Show that shouldn't exist!"
        dead_hour.save()

        # Act

        EpgSynchroniser().synchronise(self.station, epg)

        # Assert

        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=0).count()
        )
        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=1).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=2).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=3).count()
        )
        self.assertEqual(
            11, EpgEntry.objects.filter(station=self.station, day=4).count()
        )
        self.assertEqual(
            10, EpgEntry.objects.filter(station=self.station, day=5).count()
        )
        self.assertEqual(
            9, EpgEntry.objects.filter(station=self.station, day=6).count()
        )
        self.assertEqual(
            0, EpgEntry.objects.filter(station=self.station, day__isnull=True).count()
        )


class EpgDayView(APITestCase):
    """
    Test case for the API day view
    """

    username = "epg_user"
    password = "What50n?"
    email = "epg@example.com"
    station_name = "EPG AM"
    station_slogan = "Telling you what's on in the morning."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Create the station

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

        # And sample EPG

        content = open("./musicstats/test/epg.html", "r").read()
        epg = OnAir2Parser().parse(content)
        EpgSynchroniser().synchronise(self.station, epg)

    def test_day_view(self):
        """
        Tests we get a working day view
        """

        # Arrange

        json_raw = open("./musicstats/test/epg.json", "r").read()
        expected_json = json.loads(json_raw)

        url = reverse("epg_day", kwargs={"station_name": self.station_name})
        self.maxDiff = None

        # Act

        response = self.client.get(url)
        response_json = json.loads(response.content)

        # Assert

        self.assertEqual(response_json, expected_json)


class MarketingLinerTestCase(APITestCase):
    """
    Test case for marketing liners.
    """

    username = "marketing"
    password = "password"
    email = "marketing@example.com"
    station_name = "Marketing Sound"
    station_slogan = "Targeting demogaphics."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

    def test_marketing_liners(self):
        """
        Test we can retrieve liners.
        """

        liners = [
            "A real disaster of a station.",
            "Being too friendly for a company." "Classicly trained antagonists.",
        ]

        for liner in liners:
            liner_obj = MarketingLiner(line=liner, station=self.station)
            liner_obj.save()

        # Make the retrieval

        url = reverse("marketing_liners", kwargs={"station_name": self.station_name})
        response = self.client.get(url)
        json_response = json.loads(response.content)

        for index, liner in enumerate(liners):
            self.assertEqual(json_response[index]["line"], liner)


class WordpressPresenterParserTest(APITestCase):
    """Test case for the Wordpress Presenter Parser"""

    def test_parse_xml(self):
        """Checks we can parse the XML successfully."""

        # Arrange

        content = open("./musicstats/test/presenters.xml", "r").read()

        # Act

        presenters = WordpressPresenterParser().parse(content, None)
        names = [presenter.name for presenter in presenters]

        # Assert
        # Check we've got the right number of entries

        self.assertIsNotNone(presenters)
        self.assertEqual(8, len(presenters))

        # Check the names are all correct

        self.assertEqual(
            [
                "Tony T",
                "Rich Swales",
                "Jennifer Jones",
                "Stephen Hall",
                "Jenny Steele",
                "Marc Steele",
                "Dave Stocks",
                "Chris Brown",
            ],
            names,
        )


class WordpressPresenterImageTest(APITestCase):
    """Tests the wordpress image URL extractor."""

    def test_parse_html(self):
        """Checks we can parse the HTML successfully."""

        # Arrange

        content = open("./musicstats/test/presenter.html", "r").read()

        # Act

        url = WordpressPresenterImage().parse(content)

        # Assert

        self.assertEqual(
            url,
            "https://www.solidradio.co.uk/wp-content/uploads/2020/06/urban-1658436_640.jpg",
        )

    @parameterized.expand(
        [("./musicstats/test/epg.json",), ("./musicstats/test/presenters.xml",)]
    )
    def test_parse_failure(self, filename: str):
        """Tests HTML parsing errors.

        Args:
            filename (str): The name of the file to parse.
        """

        # Arrange

        content = open(filename, "r").read()

        # Act

        url = WordpressPresenterImage().parse(content)

        # Assert

        self.assertIsNone(url)


class PresenterSynchroniserTest(APITestCase):
    """Tests the presenter synchronisation process."""

    username = "presenter_user"
    password = "Sh0wt1m3"
    email = "presenter@example.com"
    station_name = "Ego Digital"
    station_slogan = "Stroking Our Ego"
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """Required setup for the test cases."""

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

    def test_sync(self):
        """Tests we can synchronise successfully."""

        # Arrange

        content = open("./musicstats/test/presenters.xml", "r").read()
        presenters = WordpressPresenterParser().parse(content, self.station)
        expected_names = [presenter.name for presenter in presenters]
        expected_links = [presenter.image for presenter in presenters]
        expected_bios = [presenter.biography for presenter in presenters]

        # Act

        PresenterSynchroniser().synchronise(self.station, presenters)
        db_presenters = Presenter.objects.filter(station=self.station)

        db_names = [presenter.name for presenter in presenters]
        db_links = [presenter.image for presenter in presenters]
        db_bios = [presenter.biography for presenter in presenters]

        # Assert

        self.assertEqual(len(db_presenters), len(presenters))
        self.assertEqual(sorted(db_names), sorted(expected_names))
        self.assertEqual(sorted(db_links), sorted(expected_links))
        self.assertEqual(sorted(db_bios), sorted(expected_bios))

    def test_sync_with_delete(self):
        """Tests the sync process with a delete."""

        # Arrange
        # Temp presenter to delete

        temp_presenter = Presenter()
        temp_presenter.name = "Billy No Mates"
        temp_presenter.image = "fired.png"
        temp_presenter.station = self.station
        temp_presenter.biography = "A useless presenter"
        temp_presenter.save()

        # Our imported presenters

        content = open("./musicstats/test/presenters.xml", "r").read()
        presenters = WordpressPresenterParser().parse(content, self.station)
        expected_names = [presenter.name for presenter in presenters]
        expected_links = [presenter.image for presenter in presenters]
        expected_bios = [presenter.biography for presenter in presenters]

        # Act

        PresenterSynchroniser().synchronise(self.station, presenters)
        db_presenters = Presenter.objects.filter(station=self.station)

        db_names = [presenter.name for presenter in presenters]
        db_links = [presenter.image for presenter in presenters]
        db_bios = [presenter.biography for presenter in presenters]

        # Assert

        self.assertEqual(len(db_presenters), len(presenters))
        self.assertEqual(sorted(db_names), sorted(expected_names))
        self.assertEqual(sorted(db_links), sorted(expected_links))
        self.assertEqual(sorted(db_bios), sorted(expected_bios))


class PresenterListView(APITestCase):
    """Test case for the presenter list view."""

    username = "presenter_user"
    password = "Sh0wt1m3"
    email = "presenter@example.com"
    station_name = "Ego Digital"
    station_slogan = "Stroking Our Ego"
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """Required setup for the test cases."""

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.station = Station(
            name=self.station_name,
            slogan=self.station_slogan,
            primary_colour=self.colour,
            text_colour=self.colour,
            stream_aac_high=self.stream_url,
            stream_aac_low=self.stream_url,
            stream_mp3_high=self.stream_url,
            stream_mp3_low=self.stream_url,
            use_liners=True,
            liner_ratio=0.1,
            update_account=self.user,
        )

        self.station.save()

    def test_list_view(self):
        """Tests we can synchronise successfully."""

        # Arrange

        json_raw = open("./musicstats/test/presenters.json", "r").read()
        expected_json = json.loads(json_raw)

        content = open("./musicstats/test/presenters.xml", "r").read()
        presenters = WordpressPresenterParser().parse(content, self.station)
        PresenterSynchroniser().synchronise(self.station, presenters)

        url = reverse("presenters", kwargs={"station_name": self.station_name})
        self.maxDiff = None

        # Act

        response = self.client.get(url)
        response_json = json.loads(response.content)

        # Assert

        self.assertEqual(response_json, expected_json)

    def test_empty_list_view(self):

        # Arrange

        presenters = Presenter.objects.all()
        for presenter in presenters:
            presenter.delete()

        url = reverse("presenters", kwargs={"station_name": self.station_name})
        self.maxDiff = None

        # Act

        response = self.client.get(url)
        response_json = json.loads(response.content)

        # Assert

        self.assertEqual(response_json, [])
