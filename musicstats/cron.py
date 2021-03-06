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


import math
import tempfile
from datetime import datetime
import requests
from requests.exceptions import RequestException
from django.conf import settings
from django.core.files import File
from django_cron import CronJobBase, Schedule
from musicstats.epg import OnAir2Parser, ProRadioParser, EpgSynchroniser
from musicstats.presenters import (
    PresenterSynchroniser,
    WordpressPresenterImage,
    WordpressPresenterParser,
)
from musicstats.models import (
    ProRadioDataSource,
    Song,
    Artist,
    Station,
    EpgEntry,
    OnAir2DataSource,
    PresenterDataSource,
    WordpressPresenterDataSource,
)


class CronUtil(object):
    """
    Utility methods for cron jobs.
    """

    HTTP_SUCCESS = 200

    def download_image(self, url):
        """
        Downloads an image from a specific URL
        """

        # Attempt the actual download

        print(f"Downloading {url}...")

        try:
            download_request = requests.get(url)
            if download_request.status_code != self.HTTP_SUCCESS:
                print(f"Failed to download {url}.")
                print(f"Reason: {download_request.text}")
                return None
        except RequestException:
            print(f"Ran into a problem downloading from {url}.")
            return None

        # Write it to a temp file

        file_name = url.split("/")[-1]
        temp = tempfile.NamedTemporaryFile()

        for block in download_request.iter_content(1024 * 8):
            if not block:
                break
            temp.write(block)

        # Supply it back

        response = {"file_name": file_name, "temp_file": temp}

        return response


class LastFmArtistSync(CronJobBase):
    """
    Last.FM artist sync
    """

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = "no-mbid-available"
    LFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = "musicstats.cron.lastfmartist"

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        """
        Perform the sync
        """

        util = CronUtil()

        # Find the artists we've not synced yet

        artists = Artist.objects.filter(musicbrainz_id="")
        for artist in artists:

            # Find the artist in last.fm

            print(f"Accessing last.fm data for artist {artist.name}.")

            artists_payload = {
                "method": "artist.getinfo",
                "artist": artist.name,
                "api_key": settings.LAST_FM["KEY"],
                "format": "json",
            }

            artist_request = requests.get(self.LFM_API_URL, params=artists_payload)
            if artist_request.status_code != self.HTTP_SUCCESS:
                print(f"Failed to get the last.fm data for artist {artist.name}.")
                print(f"Reason: {artist_request.text}")
                continue

            json = artist_request.json()

            # Pull out and test the musicbrainz ID

            if ("error" in json) or (not "mbid" in json["artist"]):
                artist.musicbrainz_id = self.BLANK_MBID
                artist.save()
                continue
            else:
                mbid = json["artist"]["mbid"]
                artist.musicbrainz_id = mbid

            # Pull out the images

            for image in json["artist"]["image"]:
                if image["size"] == "small":
                    small_image = util.download_image(image["#text"])
                elif image["size"] == "extralarge":
                    large_image = util.download_image(image["#text"])

            if small_image:
                artist.thumbnail.save(
                    small_image["file_name"], File(small_image["temp_file"])
                )
            if large_image:
                artist.image.save(
                    large_image["file_name"], File(large_image["temp_file"])
                )

            # Bio/wiki

            if "bio" in json["artist"]:
                artist.wiki_content = json["artist"]["bio"]["content"]

            # Write everything back to the database

            artist.save()


class LastFmSongSync(CronJobBase):
    """
    Last.FM Song Sync
    """

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = "no-mbid-available"
    LFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
    ITUNES_API_URL = "https://itunes.apple.com/search"
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = "musicstats.cron.lastfmsong"

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        """
        Perform the sync
        """

        util = CronUtil()

        # Find the artists we've not synced yet

        songs = Song.objects.filter(musicbrainz_id="")
        for song in songs:

            # Find the song in last.fm

            print("Accessing last.fm data for song {}.".format(song))

            song_payload = {
                "method": "track.getinfo",
                "artist": song.display_artist,
                "track": song.title,
                "api_key": settings.LAST_FM["KEY"],
                "format": "json",
            }

            song_request = requests.get(self.LFM_API_URL, params=song_payload)
            if song_request.status_code != self.HTTP_SUCCESS:
                print(f"Failed to get the last.fm data for song {song}.")
                print(f"Reason: {song_request.text}")
                continue

            json = song_request.json()

            # Obtain the iTunes URL

            self.getItunesUrl(song)

            # Pull out and test the musicbrainz ID

            if ("error" in json) or (not "mbid" in json["track"]):
                song.musicbrainz_id = self.BLANK_MBID
                song.save()
                continue
            else:
                mbid = json["track"]["mbid"]
                song.musicbrainz_id = mbid

            # Pull out the images

            small_image = None
            large_image = None

            if "album" in json["track"]:
                for image in json["track"]["album"]["image"]:
                    if image["size"] == "small":
                        small_image = util.download_image(image["#text"])
                    elif image["size"] == "extralarge":
                        large_image = util.download_image(image["#text"])
            else:
                print(
                    "No album art found for {} - {}".format(
                        song.display_artist, song.title
                    )
                )

            if small_image:
                song.thumbnail.save(
                    small_image["file_name"], File(small_image["temp_file"])
                )
            if large_image:
                song.image.save(
                    large_image["file_name"], File(large_image["temp_file"])
                )

            # Wiki

            if "wiki" in json["track"]:
                song.wiki_content = json["track"]["wiki"]["content"]

            # Write everything back to the database

            song.save()

    def getItunesUrl(self, song):
        """
        Obtain the iTunes URL for a song
        """

        # Search for the song

        itunes_payload = {
            "term": f"{song.display_artist} - {song.title}",
            "country": "GB",
            "media": "music",
        }

        itunes_request = requests.get(self.ITUNES_API_URL, params=itunes_payload)
        if itunes_request.status_code != self.HTTP_SUCCESS:
            print(f"Failed to get the iTunes URL for song {song}.")
            print(f"Reason: {itunes_request.text}")
            return

        json = itunes_request.json()

        # Check we got a song back

        if json["resultCount"] == 0:
            print(f"No iTunes URL found for {song}.")
            return

        # Look for the first song and URL

        for result in json["results"]:
            if result["wrapperType"] == "track":
                song.itunes_url = result["trackViewUrl"]
                print(f"The iTunes URL for {song} is {song.itunes_url}")
                return


class EpgUpdater(CronJobBase):
    """
    Updates the EPG (as appropriate) from the upstream sources
    """

    # Settings

    RUN_INTERVAL = 86400  # 24 Hours

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = "musicstats.cron.epg"

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        """
        Performs the actual updates.
        """

        synchroniser = EpgSynchroniser()

        # Cycle through each of our stations
        # Look for EPG updates needed

        for station in Station.objects.all():

            # Does the station have an EPG

            if station.epg:

                # Let's go and update that EPG

                if isinstance(station.epg, OnAir2DataSource):

                    new_epg = None

                    # Read in the HTML and the EPG

                    try:
                        result = requests.get(station.epg.schedule_url)
                        result.raise_for_status()
                        new_epg = OnAir2Parser().parse(result.text)
                    except requests.exceptions.RequestException as ex:
                        print(
                            f"Failed to get EPG data from {station.epg.schedule_url}. Reason: {ex}"
                        )

                if isinstance(station.epg, ProRadioDataSource):

                    # Read in the HTML and the EPG

                    try:
                        result = requests.get(station.epg.schedule_url)
                        result.raise_for_status()
                        new_epg = ProRadioParser().parse(result.text)
                    except requests.exceptions.RequestException as ex:
                        print(
                            f"Failed to get EPG data from {station.epg.schedule_url}. Reason: {ex}"
                        )

                # Error out if we didn't get an EPG entry

                if new_epg:
                    synchroniser.synchronise(station, new_epg)
                    print(f"Syncrhonised EPG for {station}.")
                if not new_epg:
                    print(f"Failed to get a new EPG entry for {station}.")
                    continue


class PresenterSynchroniserJob(CronJobBase):
    """Synchronises presenters into the database."""

    # Settings

    RUN_INTERVAL = 86400  # 24 Hours

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = "musicstats.cron.presenters"

    def do(self):
        """Executes the synchronisation."""

        for station in Station.objects.all():

            # Check what data source to use

            if station.presenters:
                if isinstance(station.presenters, WordpressPresenterDataSource):

                    # Wordpress as a source

                    presenters = []

                    try:
                        result = requests.get(station.presenters.presenter_list_url)
                        result.raise_for_status()
                        presenters = WordpressPresenterParser().parse(
                            result.text, station
                        )
                    except requests.exceptions.RequestException as ex:
                        print(
                            f"Failed to get presenter list from {station.presenters.presenter_list_url}. Reason: {ex}"
                        )
                        continue

                    # Sanity check

                    if not presenters:
                        print(
                            f"Extracted no presenters from {station.presenters.presenter_list_url}."
                        )
                        continue

                    # Get image URLs for each presenter

                    image_url_parser = WordpressPresenterImage()

                    for presenter in presenters:
                        try:
                            result = requests.get(presenter.url)
                            result.raise_for_status()
                            presenter.image = image_url_parser.parse(result.text)
                        except requests.exceptions.RequestException as ex:
                            print(
                                f"Failed to extract presenter image from {presenter.url}. Reason: {ex}"
                            )
                            continue

                    # Synchronise

                    PresenterSynchroniser().synchronise(station, presenters)
