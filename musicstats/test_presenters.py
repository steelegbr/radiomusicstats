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
from parameterized import parameterized
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import (
    Station,
    Presenter,
)
from musicstats.presenters import (
    WordpressPresenterParser,
    WordpressPresenterImage,
    PresenterSynchroniser,
)


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

    def test_parse_null_content(self):
        """Checks we handle null content correctly."""

        # Arrange

        url = WordpressPresenterImage().parse(None)

        # Assert

        self.assertIsNone(url)

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

        # A presenter to update

        update_presenter = Presenter()
        update_presenter.name = "Marc Steele"
        update_presenter.image = "marc.png"
        update_presenter.station = self.station
        update_presenter.biography = "More coming soon!"
        update_presenter.save()

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

    @parameterized.expand([(None, []), (None, None)])
    def test_null(self, station, presenters):
        """ Checks we can handle nulls. """

        # Arrange

        # Act

        response = PresenterSynchroniser().synchronise(station, presenters)

        # Assert

        self.assertIsNone(response)


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

        presenters = Presenter.objects.all().delete()

        url = reverse("presenters", kwargs={"station_name": self.station_name})
        self.maxDiff = None

        # Act

        response = self.client.get(url)
        response_json = json.loads(response.content)

        # Assert

        self.assertEqual(response_json, [])
