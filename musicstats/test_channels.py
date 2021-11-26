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
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.conf.urls import url
from django.test import TransactionTestCase
from musicstats.consumers import NowPlayingConsumer
from musicstats.models import Song, SongPlay, Station
from rest_framework.authtoken.models import Token


class ChannelsTest(TransactionTestCase):
    """
    Test case for web sockets / channels.
    """

    station_name = "Channels"
    station_slogan = "Songs and stuff."
    colour = "#FFFFFF"
    stream_url = "https://example.com/stream"

    def setUp(self):
        """
        Required setup for the test case.
        """

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
        )
        station.save()

        # We need a song

        song = Song(display_artist="Channels", title="WS Song")
        song.save()

        # And finally, the song play

        song_play = SongPlay(song=song, station=station)
        song_play.save()

    async def test_now_playing(self):
        """
        Makes sure the current song is returned on connection.
        """

        # Make the websocket connection

        application = URLRouter(
            [
                url(
                    r"^nowplaying/(?P<station_name>[^/]+)/$",
                    NowPlayingConsumer.as_asgi(),
                )
            ]
        )
        communicator = WebsocketCommunicator(application, "/nowplaying/Channels/")
        (connected, _) = await communicator.connect()
        self.assertTrue(connected)

        actual_response = await communicator.receive_from()
        json_response = json.loads(actual_response)
        self.assertEqual(json_response["song"]["display_artist"], "Channels")
        self.assertEqual(json_response["song"]["title"], "WS Song")
        self.assertEqual(json_response["station"], "Channels")
