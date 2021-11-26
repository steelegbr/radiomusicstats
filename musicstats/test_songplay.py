"""
    Radio Music Stats - Radio Music Statistics and Now Playing
    Copyright (C) 2017-2021 Marc Steele

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import json
from datetime import datetime, time
from parameterized import parameterized
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import (
    Station,
    SongPlay,
)


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

    def test_log_songplay_partial(self):
        """
        Tests we can successfully log a partial songplay.
        """

        # Work out the URL and use valid creds

        url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.valid_token}")

        # Post and check our valid songplay

        songplay = {
            "song": {
                "display_artist": "The Singers and Lord Voldemort",
                "artists": [],
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
                    "artists": [],
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
