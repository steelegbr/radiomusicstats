'''
    MusicStats Cron Tasks
'''


import math
import tempfile
from datetime import datetime
import requests
from requests.exceptions import RequestException
from django.conf import settings
from django.core.files import File
from django_cron import CronJobBase, Schedule
from musicstats.epg import OnAir2
from musicstats.models import Song, Artist, Station, EpgEntry, OnAir2DataSource

class CronUtil(object):
    '''
    Utility methods for cron jobs.
    '''

    HTTP_SUCCESS = 200

    def download_image(self, url):
        '''
        Downloads an image from a specific URL
        '''

        # Attempt the actual download

        print(f'Downloading {url}...')

        try:
            download_request = requests.get(url)
            if download_request.status_code != self.HTTP_SUCCESS:
                print(f'Failed to download {url}.')
                print(f'Reason: {download_request.text}')
                return None
        except RequestException:
            print(f'Ran into a problem downloading from {url}.')
            return None

        # Write it to a temp file

        file_name = url.split('/')[-1]
        temp = tempfile.NamedTemporaryFile()

        for block in download_request.iter_content(1024 * 8):
            if not block:
                break
            temp.write(block)

        # Supply it back

        response = {
            'file_name': file_name,
            'temp_file': temp
        }

        return response

class LastFmArtistSync(CronJobBase):
    '''
    Last.FM artist sync
    '''

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = 'no-mbid-available'
    LFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = 'musicstats.cron.lastfmartist'

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        '''
        Perform the sync
        '''

        util = CronUtil()

        # Find the artists we've not synced yet

        artists = Artist.objects.filter(musicbrainz_id='')
        for artist in artists:

            # Find the artist in last.fm

            print(f"Accessing last.fm data for artist {artist.name}.")

            artists_payload = {
                'method': 'artist.getinfo',
                'artist': artist.name,
                'api_key': settings.LAST_FM['KEY'],
                'format': 'json'
            }

            artist_request = requests.get(self.LFM_API_URL, params=artists_payload)
            if artist_request.status_code != self.HTTP_SUCCESS:
                print(f"Failed to get the last.fm data for artist {artist.name}.")
                print(f"Reason: {artist_request.text}")
                continue

            json = artist_request.json()

            # Pull out and test the musicbrainz ID

            if (('error' in json) or (not 'mbid' in json['artist'])):
                artist.musicbrainz_id = self.BLANK_MBID
                artist.save()
                continue
            else:
                mbid = json['artist']['mbid']
                artist.musicbrainz_id = mbid

            # Pull out the images

            for image in json['artist']['image']:
                if image['size'] == 'small':
                    small_image = util.download_image(image['#text'])
                elif image['size'] == 'extralarge':
                    large_image = util.download_image(image['#text'])

            if small_image:
                artist.thumbnail.save(small_image['file_name'], File(small_image['temp_file']))
            if large_image:
                artist.image.save(large_image['file_name'], File(large_image['temp_file']))

            # Bio/wiki

            if 'bio' in json['artist']:
                artist.wiki_content = json['artist']['bio']['content']

            # Write everything back to the database

            artist.save()

class LastFmSongSync(CronJobBase):
    '''
    Last.FM Song Sync
    '''

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = 'no-mbid-available'
    LFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
    ITUNES_API_URL = 'https://itunes.apple.com/search'
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = 'musicstats.cron.lastfmsong'

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        '''
        Perform the sync
        '''

        util = CronUtil()

        # Find the artists we've not synced yet

        songs = Song.objects.filter(musicbrainz_id='')
        for song in songs:

            # Find the song in last.fm

            print("Accessing last.fm data for song {}.".format(song))

            song_payload = {
                'method': 'track.getinfo',
                'artist': song.display_artist,
                'track': song.title,
                'api_key': settings.LAST_FM['KEY'],
                'format': 'json'
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

            if (('error' in json) or (not 'mbid' in json['track'])):
                song.musicbrainz_id = self.BLANK_MBID
                song.save()
                continue
            else:
                mbid = json['track']['mbid']
                song.musicbrainz_id = mbid

            # Pull out the images

            small_image = None
            large_image = None

            if 'album' in json['track']:
                for image in json['track']['album']['image']:
                    if image['size'] == 'small':
                        small_image = util.download_image(image['#text'])
                    elif image['size'] == 'extralarge':
                        large_image = util.download_image(image['#text'])
            else:
                print('No album art found for {} - {}'.format(song.display_artist, song.title))

            if small_image:
                song.thumbnail.save(small_image['file_name'], File(small_image['temp_file']))
            if large_image:
                song.image.save(large_image['file_name'], File(large_image['temp_file']))

            # Wiki

            if 'wiki' in json['track']:
                song.wiki_content = json['track']['wiki']['content']

            # Write everything back to the database

            song.save()

    def getItunesUrl(self, song):
        '''
        Obtain the iTunes URL for a song
        '''

        # Search for the song

        itunes_payload = {
            'term': f'{song.display_artist} - {song.title}',
            'country': 'GB',
            'media': 'music'
        }

        itunes_request = requests.get(self.ITUNES_API_URL, params=itunes_payload)
        if itunes_request.status_code != self.HTTP_SUCCESS:
            print(f"Failed to get the iTunes URL for song {song}.")
            print(f"Reason: {itunes_request.text}")
            return

        json = itunes_request.json()

        # Check we got a song back

        if json['resultCount'] == 0:
            print(f"No iTunes URL found for {song}.")
            return

        # Look for the first song and URL

        for result in json['results']:
            if result['wrapperType'] == 'track':
                song.itunes_url = result['trackViewUrl']
                print(f"The iTunes URL for {song} is {song.itunes_url}")
                return

class EpgUpdater(CronJobBase):
    '''
    Updates the EPG (as appropriate) from the upstream sources
    '''

    # Settings

    RUN_INTERVAL = 10

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = 'musicstats.cron.epg'

    # pylint: disable=invalid-name
    # It's not proper snake case but part of the API

    def do(self):
        '''
        Performs the actual updates.
        '''

        # Cycle through each of our stations
        # Look for EPG updates needed

        for station in Station.objects.all():

            # Does the station have an EPG

            if station.epg:

                # Work out when our EPG window starts

                now = datetime.now()
                start_mins = math.floor(
                    now.minute / station.epg.granularity_mins
                ) * station.epg.granularity_mins

                # Check if we've updated since then

                current_epg = EpgEntry.objects \
                    .filter(station=station) \
                        .order_by('-last_updated') \
                            .first()
                if current_epg \
                    and current_epg.start.hour == now.hour \
                        and current_epg.start.minute > start_mins:
                    print(f'EPG already up to date for {station}.')
                    continue

                # Let's go and update that EPG

                if isinstance(station.epg, OnAir2DataSource):
                    new_epg = OnAir2(station.epg).get_current_epg()

                # Error out if we didn't get an EPG entry

                if not new_epg:
                    print(f'Failed to get a new EPG entry for {station}.')
                    continue

                # Check if the EPG entry is new

                if not current_epg or \
                    new_epg.title != current_epg.title or \
                    new_epg.description != current_epg.description or \
                    new_epg.image != current_epg.image or \
                    new_epg.start != current_epg.start:

                    # The EPG entry is new save it

                    new_epg.station = station
                    new_epg.save()
                    print(f'Found new EPG entry - {new_epg}')

                else:

                    # The old EPG entry is still valid
                    # Save it instead

                    current_epg.save()
                    print(f'Updated timestamp on EPG entry - {current_epg}')
