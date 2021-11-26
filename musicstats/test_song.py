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
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import (
    Artist,
    Song,
)


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
