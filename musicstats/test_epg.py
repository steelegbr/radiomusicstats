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
    EpgEntry,
)
from musicstats.epg import OnAir2Parser, EpgSynchroniser


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
