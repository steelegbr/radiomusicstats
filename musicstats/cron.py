'''
    MusicStats Cron Tasks
'''

from django.conf import settings
from models import Song, Artist
from django_cron import CronJobBase, Schedule
from django.core.files import File
from datetime import datetime
from xml.etree import ElementTree
import re
import requests
import tempfile
import urllib
import hmac
import hashlib
import base64

# Utility methods

class CronUtil(object):

    HTTP_SUCCESS = 200

    # Downloads an image from a specific URL

    def downloadImage(self, url):

        # Attempt the actual download

        print('Downloading {}...'.format(url))

        try:
            download_request = requests.get(url)
            if (download_request.status_code != self.HTTP_SUCCESS):
                print('Failed to download {}.'.format(url))
                print('Reason: {}'.format(download_request.text))
                return None
        except:
            print('Ran into a problem downloading from {}.'.format(url))
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

        util = CronUtil()

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
                    small_image = util.downloadImage(image['#text'])
                elif image['size'] == 'extralarge':
                    large_image = util.downloadImage(image['#text'])

            if (small_image):
                artist.thumbnail.save(small_image['file_name'], File(small_image['temp_file']))
            if (large_image):
                artist.image.save(large_image['file_name'], File(large_image['temp_file']))

            # Bio/wiki

            if ('bio' in json['artist']):
                artist.wiki_content = json['artist']['bio']['content']

            # Write everything back to the database

            artist.save()

# Last.fm Song Synchronisation

class LastFmSongSync(CronJobBase):

    # Settings

    RUN_INTERVAL = 10
    BLANK_MBID = 'no-mbid-available'
    LFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
    ITUNES_API_URL = 'https://itunes.apple.com/search'
    AMAZON_API_URL = 'https://{}/onca/xml'
    HTTP_SUCCESS = 200

    schedule = Schedule(run_every_mins=RUN_INTERVAL)
    code = 'musicstats.cron.lastfmsong'

    # Perform the synchronisation

    def do(self):

        util = CronUtil()

        # Find the artists we've not synced yet

        songs = Song.objects.filter(musicbrainz_id='')
        for song in songs:
        
            # Amazon
            
            self.getAmazonUrl(song)

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
            if (song_request.status_code != self.HTTP_SUCCESS):
                print("Failed to get the last.fm data for song {}.".format(song))
                print("Reason: {}".format(song_request.text))
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

            if ('album' in json['track']):
                for image in json['track']['album']['image']:
                    if image['size'] == 'small':
                        small_image = util.downloadImage(image['#text'])
                    elif image['size'] == 'extralarge':
                        large_image = util.downloadImage(image['#text'])
            else:
                print(json['track'])
                continue

            if (small_image):
                song.thumbnail.save(small_image['file_name'], File(small_image['temp_file']))
            if (large_image):
                song.image.save(large_image['file_name'], File(large_image['temp_file']))

            # Wiki

            if ('wiki' in json['track']):
                song.wiki_content = json['track']['wiki']['content']

            # Write everything back to the database

            song.save() 

    # Obtains the iTunes URL for a song

    def getItunesUrl(self, song):

        # Search for the song

        itunes_payload = {
                'term': '{} - {}'.format(song.display_artist, song.title),
                'country': 'GB',
                'media': 'music'
        }

        itunes_request = requests.get(self.ITUNES_API_URL, params=itunes_payload)
        if (itunes_request.status_code != self.HTTP_SUCCESS):
            print("Failed to get the iTunes URL for song {}.".format(song))
            print("Reason: {}".format(itunes_request.text))
            return

        json = itunes_request.json()

        # Check we got a song back

        if (json['resultCount'] == 0):
                print("No iTunes URL found for {}.".format(song))
                return

        # Look for the first song and URL

        for result in json['results']:
            if result['wrapperType'] == 'track':
                song.itunes_url = result['trackViewUrl']
                print("The iTunes URL for {} is {}".format(song, song.itunes_url))
                return
                
    # Obtains the Amazon affiliate URL for a song
    
    def getAmazonUrl(self, song):
    
        # Search for the song
    	
    	amazon_payload = {
    	    'Service': 'AWSECommerceService',
    	    'Operation': 'ItemSearch',
    	    'AWSAccessKeyId': settings.AMAZON['KEY_ID'],
    	    'AssociateTag': settings.AMAZON['TAG'],
    	    'SearchIndex': 'MP3Downloads',
    	    'Keywords': song.display_artist,
    	    'Title': song.title,
    	    'Timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
    	}
    	
    	# Build the partial URL and generate the signature
    	
    	querystring_parts = []
    	
    	for key in sorted(amazon_payload.keys()):
            querystring_parts.append('{}={}'.format(key, urllib.quote(amazon_payload[key], safe='')))

    	to_sign = 'GET\n{}\n/onca/xml\n{}'.format(settings.AMAZON['URL'], '&'.join(querystring_parts))
    	hmac_hash = hmac.new(settings.AMAZON['KEY_SECRET'], to_sign.encode('utf-8'), hashlib.sha256).digest()
    	base64_hash = base64.b64encode(hmac_hash).decode()
    	querystring_parts.append('Signature={}'.format(urllib.quote(base64_hash, safe='')))
    	
    	# Make the request
    	
    	amazon_request = requests.get('http://{}/onca/xml?{}'.format(settings.AMAZON['URL'], '&'.join(querystring_parts)))
        if (amazon_request.status_code != self.HTTP_SUCCESS):
            print("Failed to get the Amazon URL for song {}.".format(song))
            print("Reason: {}".format(amazon_request.text))
            return
            
        # Inflate out the XML
        # Start by obtaining the current namespace
        
        root = ElementTree.fromstring(amazon_request.content)
        match = re.match('\{.*\}', root.tag)
        if match:
            namespace = match.group(0)
        else:
            print('No namespace found with using Amazon API.')
            return
            
        # Now locate the element
        
        xpath = './{0}Items/{0}Item/{0}DetailPageURL'.format(namespace)
        item = root.find(xpath)
        
        if item is not None:
            song.amazon_url = item.text
            print('The Amazon URL for {} is {}.'.format(song, song.amazon_url))
            
    	
