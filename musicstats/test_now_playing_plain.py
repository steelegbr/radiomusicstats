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

from parameterized import parameterized
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import (
    Station,
    SongPlay,
)


class NowPlayingPlainTextTest(APITestCase):
    """
    Test case for now playing in plain text.
    """

    username = "now_playing_plain"
    email = "plain@example.com"
    password = "Password1"
    station_name = "Now Playing FM"
    station_slogan = "Songs and stuff."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)

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

    def test_nowplaying_sequence(self):
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
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        for songplay in songplays:
            response = self.client.post(log_url, songplay, format="json")
            self.assertEqual(response.status_code, 200)

        # Check we get the last one in the list back

        self.client.credentials()
        url = reverse("now_playing_plain", kwargs={"station_name": self.station_name})
        response = self.client.get(url)

        # Assert

        self.assertEqual(response.content.decode(), f"Songplay Artist - Song C")

    @parameterized.expand(
        [
            ("Münchener Freiheit", ["Münchener Freiheit"], "Keeping the Dream Alive"),
            ("Beyoncé", ["Beyoncé"], "Irreplaceable"),
        ]
    )
    def test_nowplaying_characters(self, display_artist, artists, title):
        """
        Tests now playing works with various character combinations
        """

        # The songplay

        songplay = {
            "song": {
                "display_artist": display_artist,
                "artists": artists,
                "title": title,
            },
            "station": self.station_name,
        }

        # Write it to the DB

        log_url = reverse("song_play_log")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.post(log_url, songplay, format="json")

        self.assertEqual(response.status_code, 200)
        self.client.credentials()

        # Check we get the last one in the list back

        url = reverse("now_playing_plain", kwargs={"station_name": self.station_name})
        response = self.client.get(url)

        # Assert

        self.assertEqual(response.content.decode(), f"{display_artist} - {title}")

    def test_nowplaying_blank(self):
        """
        Ensures we get a sensible response when we have info.
        """

        # Delete any existing songplays

        SongPlay.objects.filter(station=self.station).delete()

        # Make sure we get a 404

        self.client.credentials()
        url = reverse("now_playing_plain", kwargs={"station_name": self.station_name})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_nowplaying_bad_station(self):
        """
        Checks we get a 404 for a non-existant station.
        """

        # Make sure we get a 404

        url = reverse(
            "now_playing_plain", kwargs={"station_name": "Does Not Exist Digital"}
        )

        self.client.credentials()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
