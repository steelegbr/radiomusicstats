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

from datetime import datetime
from rest_framework.test import APITestCase
from parameterized import parameterized
from musicstats.models import (
    artist_thumbnail_path,
    artist_image_path,
    song_thumbnail_path,
    song_image_path,
    logo_image_path,
    logo_inverse_path,
    logo_square_path,
    Song,
    EpgDataSource,
    OnAir2DataSource,
    PresenterDataSource,
    WordpressPresenterDataSource,
    Station,
    SongPlay,
    EpgEntry,
    Podcast,
    MarketingLiner,
    Presenter,
)


class Instance:
    """Temp class for testing paths."""

    def __init__(self, id):
        self.id = id


class UtilityMethodTest(APITestCase):
    """Tests the utility methods."""

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_artist_thumbnail_path(self, instance_id, filename):
        """Checks the artist thumbnail path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = artist_thumbnail_path(instance, filename)

        # Assert

        self.assertEqual(path, f"artists/thumbnails/{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_artist_image_path(self, instance_id, filename):
        """Checks the artist image path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = artist_image_path(instance, filename)

        # Assert

        self.assertEqual(path, f"artists/images/{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_song_thumbnail_path(self, instance_id, filename):
        """Checks the song thumbnail path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = song_thumbnail_path(instance, filename)

        # Assert

        self.assertEqual(path, f"songs/thumbnails/{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_song_image_path(self, instance_id, filename):
        """Checks the song image path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = song_image_path(instance, filename)

        # Assert

        self.assertEqual(path, f"songs/images/{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_logo_image_path(self, instance_id, filename):
        """Checks the logo image path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = logo_image_path(instance, filename)

        # Assert

        self.assertEqual(path, f"logos/images/{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_logo_inverse_path(self, instance_id, filename):
        """Checks the logo inverse path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = logo_inverse_path(instance, filename)

        # Assert

        self.assertEqual(path, f"logos/images/inverse_{instance.id}_{filename}")

    @parameterized.expand([(1, "filename.png"), (2, "otherfile.jpg")])
    def test_logo_square_path(self, instance_id, filename):
        """Checks the logo square path."""

        # Arrange

        instance = Instance(instance_id)

        # Act

        path = logo_square_path(instance, filename)

        # Assert

        self.assertEqual(path, f"logos/images/square_{instance.id}_{filename}")


class TestStringRepresentation(APITestCase):
    """Tests the string representation of models."""

    @parameterized.expand([("Artist Name", "Song Title"), ("Beyoncé", "Irreplaceable")])
    def test_song_string(self, display_artist, title):
        """Tests the song string representation."""

        # Arrange

        expected = f"{display_artist} - {title}"
        song = Song()
        song.display_artist = display_artist
        song.title = title

        # Act

        actual = str(song)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("Test Source",)])
    def test_epg_data_source(self, name):
        """Tests the EPG data source string representation."""

        # Arrange

        source = EpgDataSource()
        source.name = name

        # Act

        actual = str(source)

        # Assert

        self.assertEqual(actual, name)

    @parameterized.expand([("Test Source", "http://example.com/on-air/")])
    def test_onair_data_source(self, name, url):
        """Tests the on air data source representation."""

        # Arrange

        source = OnAir2DataSource()
        source.name = name
        source.schedule_url = url
        expected = f"{name} ({url})"

        # Act

        actual = str(source)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("Test Source")])
    def test_presenter_data_source(self, name):
        """Tests the presenter data source representation."""

        # Arrange

        source = PresenterDataSource()
        source.name = name

        # Act

        actual = str(source)

        # Assert

        self.assertEqual(actual, name)

    @parameterized.expand([("Test Source", "http://example.com/on-air/")])
    def test_wordpress_presenter_source(self, name, url):
        """Tests the wordpress presenter data source representation."""

        # Arrange

        source = WordpressPresenterDataSource()
        source.name = name
        source.presenter_list_url = url
        expected = f"{name} ({url})"

        # Act

        actual = str(source)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("Test Source")])
    def test_station(self, name):
        """Tests the station representation."""

        # Arrange

        station = Station()
        station.name = name

        # Act

        actual = str(station)

        # Assert

        self.assertEqual(actual, name)

    @parameterized.expand(
        [
            (
                "Test FM",
                "Artist",
                "Title",
                1603140004,
                "Artist - Title on Test FM at 2020-10-19 21:40:04",
            )
        ]
    )
    def test_songplay(self, station_name, artist, title, timestamp, expected):
        """Tests the songplay representation."""

        # Arrange

        station = Station()
        station.name = station_name

        song = Song()
        song.display_artist = artist
        song.title = title

        songplay = SongPlay()
        songplay.song = song
        songplay.station = station
        songplay.date_time = datetime.fromtimestamp(timestamp)

        # Act

        actual = str(songplay)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand(
        [
            (
                None,
                "01:00",
                "Creeping Through the Night",
                "Old Codger AM",
                "[01:00] Creeping Through the Night on Old Codger AM",
            ),
            (
                2,
                "16:00",
                "Mahoosive Drive Home",
                "Something FM",
                "[Wednesday][16:00] Mahoosive Drive Home on Something FM",
            ),
        ]
    )
    def test_epg_entry(self, day, start, title, station_name, expected):
        """Tests the EPG entry string representation."""

        # Arrange

        station = Station()
        station.name = station_name

        entry = EpgEntry()
        entry.day = day
        entry.start = start
        entry.title = title
        entry.station = station

        # Act

        actual = str(entry)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("The Super Duper Podcast", "Station FM")])
    def test_podcast(self, name, station_name):
        """Tests the podcast string representation."""

        # Arrange

        station = Station()
        station.name = station_name

        podcast = Podcast()
        podcast.name = name
        podcast.station = station

        expected = f"{name} ({station_name})"

        # Act

        actual = str(podcast)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("Oldies AM", "Playing ancient records.")])
    def test_marketing_liner(self, station_name, line):
        """Test marketing liner representation."""

        # Arrange

        station = Station()
        station.name = station_name

        liner = MarketingLiner()
        liner.line = line
        liner.station = station

        expected = f"[{station_name}] - {line}"

        # Act

        actual = str(liner)

        # Assert

        self.assertEqual(actual, expected)

    @parameterized.expand([("Cheapest We Could Hire")])
    def test_presenter(self, name):
        """Test the presenter string representation."""

        # Arrange

        presenter = Presenter()
        presenter.name = name

        # Act

        actual = str(presenter)

        # Assert

        self.assertEqual(actual, name)
