'''
    MusicStats Cron Tasks
'''

from django.conf import settings
from models import Song, Artist
from django_cron import CronJobBase, Schedule
from django.core.files import File
import requests
import tempfile

# Last.fm Artist Synchronisation

class LastFmArtistSync(CronJobBase):

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = 'no-mbid-available'
    LFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = 'musicstats.cron.lastfmartist'

    # Perform the synchronisation

    def do(self):

        # Find the artists we've not synced yet

        artists = Artist.objects.filter(musicbrainz_id='')
        for artist in artists:

            # Find the artist in last.fm

            print("Accessing last.fm data for artist {}.".format(artist.name))

            artists_payload = {
                    'method': 'artist.getinfo',
                    'artist': artist.name,
                    'api_key': settings.LAST_FM['KEY'],
                    'format': 'json'
            }

            artist_request = requests.get(self.LFM_API_URL, params=artists_payload)
            if (artist_request.status_code != self.HTTP_SUCCESS):
                print("Failed to get the last.fm data for artist {}.".format(artist.name))
                print("Reason: {}".format(artist_request.text))
                continue

            json = artist_request.json()

            # Pull out and test the musicbrainz ID

            mbid = json['artist']['mbid']
            if (not mbid):
                artist.musicbrainz_id = self.BLANK_MBID
                continue
            else:
                artist.musicbrainz_id = mbid

            # Pull out the images

            for image in json['artist']['image']:
                if image['size'] == 'small':
                    small_image = self.downloadImage(image['#text'])
                elif image['size'] == 'extralarge':
                    large_image = self.downloadImage(image['#text'])

            if (small_image):
                artist.thumbnail.save(small_image['file_name'], File(small_image['temp_file']))
            if (large_image):
                artist.image.save(large_image['file_name'], File(large_image['temp_file']))

            # Bio/wiki

            artist.wiki_content = json['artist']['bio']['content']

            # Write everything back to the database

            artist.save()

    # Downloads an image from a specific URL

    def downloadImage(self, url):

        # Attempt the actual download

        print('Downloading {}...'.format(url))
        download_request = requests.get(url)
        if (download_request.status_code != self.HTTP_SUCCESS):
            print('Failed to download {}.'.format(url))
            print('Reason: {}'.format(download_request.text))
            return None

        # Write it to a temp file

        file_name = url.split('/')[-1]
        temp = tempfile.NamedTemporaryFile()

        for block in download_request.iter_content(1024 * 8):
            if (not block):
                break
            temp.write(block)

        # Supply it back

        response = {
                'file_name': file_name,
                'temp_file': temp
        }

        return response

