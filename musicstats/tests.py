'''
MusicStats unit tests
'''

import json
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import Station, Artist, Song

class TestIndex(APITestCase):
    '''
    Tests we can access the index.
    '''

    def test_index(self):
        '''
        Checks the index returns the static content
        '''

        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.content, b'Hello from the musicstats index.')

class StationTestCase(APITestCase):
    '''
    Tests station API endpoints.
    '''

    username = "station_test"
    password = "testcase_01"
    email = "test@example.com"
    station_name = "Test FM"
    station_slogan = "Testing your ears... for something!"
    colour = '#FFFFFF'
    stream_url = 'https://example.com/stream'

    def setUp(self):
        '''
        Create a test station ready for the next stage.
        '''

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

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
            liner_ratio=0.1
        )

    def test_station_create(self):
        '''
        Tests we can create the station and access it correctly
        '''

        self.station.save()

        url = reverse('station-detail', kwargs={'name': self.station_name})
        response = self.client.get(url)
        json_response = json.loads(response.content)
        
        self.assertEqual(json_response['name'], self.station.name)
        self.assertEqual(json_response['slogan'], self.station.slogan)
        self.assertEqual(json_response['primary_colour'], self.station.primary_colour)
        self.assertEqual(json_response['text_colour'], self.station.text_colour)
        self.assertEqual(json_response['stream_aac_high'], self.station.stream_aac_high)
        self.assertEqual(json_response['stream_aac_low'], self.station.stream_aac_low)
        self.assertEqual(json_response['stream_mp3_high'], self.station.stream_mp3_high)
        self.assertEqual(json_response['stream_mp3_low'], self.station.stream_mp3_low)
        self.assertEqual(json_response['use_liners'], self.station.use_liners)
        self.assertEqual(float(json_response['liner_ratio']), self.station.liner_ratio)

        self.station.delete()

class LogSongplayTest(APITestCase):
    '''
    Tests the log songplay functionality
    '''

    valid_username = 'real_station_user'
    valid_password = 'P@55w0rd!'
    valid_email = 'valid@user.creds'
    invalid_username = 'fake_station_user'
    invalid_password = 'SuperSecr3t!'
    invalid_email = 'invalid@user.creds'
    station_name = "Logging FM"
    station_slogan = "More wood cutting variety!"
    colour = '#FFFFFF'
    stream_url = 'https://example.com/stream'

    def setUp(self):
        '''
        Required setup for the test case.
        '''

        valid_user = User.objects.create_user(
            self.valid_username,
            self.valid_email,
            self.valid_password
        )
        invalid_user = User.objects.create_user(
            self.invalid_username,
            self.invalid_email,
            self.invalid_password
        )

        self.valid_token = Token.objects.create(user=valid_user)
        self.invalid_token = Token.objects.create(user=invalid_user)

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
            update_account=valid_user
        )

        station.save()

    def test_log_songplay(self):
        '''
        Tests we can successfully log a songplay.
        '''

        # Work out the URL and use valid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.valid_token}')

        # Post and check our valid songplay

        songplay = {
            'song': {
                'display_artist': 'The Singers and Lord Voldemort',
                'artists': ['Lord Voldemort', 'The Singers'],
                'title': 'Songy McSongFace'
            },
            'station': self.station_name
        }

        response = self.client.post(url, songplay, format='json')
        response_json = json.loads(response.content)

        self.assertEqual(
            response_json['song']['display_artist'],
            songplay['song']['display_artist']
        )
        self.assertEqual(response_json['song']['artists'], songplay['song']['artists'])
        self.assertEqual(response_json['song']['title'], songplay['song']['title'])
        self.assertEqual(response_json['station'], self.station_name)

    def test_invalid_station(self):
        '''
        Tests we can't log against an invalid station.
        '''

        # Work out the URL and use valid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.valid_token}')

        # Post and check our valid songplay

        songplay = {
            'song': {
                'display_artist': 'Invalid Singer',
                'artists': ['Invalid Singer'],
                'title': 'Invalid Song'
            },
            'station': 'Invalid FM'
        }

        response = self.client.post(url, songplay, format='json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_user(self):
        '''
        Checks an invalid user can't log against a valid station.
        '''

        # Work out the URL and use invalid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.invalid_token}')

        # Attempt the request

        songplay = {
            'song': {
                'display_artist': 'Valid Singer',
                'artists': ['Valid Singer'],
                'title': 'Valid Song'
            },
            'station': self.station_name
        }

        response = self.client.post(url, songplay, format='json')
        self.assertEqual(response.status_code, 401)

    def test_song_sequence(self):
        '''
        Checks we can't play the same song back to back.
        Though we do allow it later.
        '''

        # Work out the URL and use invalid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.valid_token}')

        # The songs we'll be using

        songplays = [
            {
                'song': {
                    'display_artist': 'Singer 0',
                    'artists': ['Singer 0'],
                    'title': 'Song 0'
                },
                'station': self.station_name
            },
            {
                'song': {
                    'display_artist': 'Singer 1',
                    'artists': ['Singer 1'],
                    'title': 'Song 1'
                },
                'station': self.station_name
            }
        ]

        # Our first song will be allowed

        response = self.client.post(url, songplays[0], format='json')
        self.assertEqual(response.status_code, 200)

        # Don't let us repeat it

        response = self.client.post(url, songplays[0], format='json')
        self.assertEqual(response.status_code, 400)

        # But allow a second song then come back

        response = self.client.post(url, songplays[1], format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, songplays[0], format='json')
        self.assertEqual(response.status_code, 200)

    def test_repeat_artist(self):
        '''
        Test the re-use of artists.
        '''

        # Work out the URL and use invalid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.valid_token}')

        # The songs we'll be using

        songplays = [
            {
                'song': {
                    'display_artist': 'Singer A',
                    'artists': ['Singer A'],
                    'title': 'Song A'
                },
                'station': self.station_name
            },
            {
                'song': {
                    'display_artist': 'Singer A',
                    'artists': ['Singer A'],
                    'title': 'Song B'
                },
                'station': self.station_name
            }
        ]

        # Our first song will be allowed

        response = self.client.post(url, songplays[0], format='json')
        self.assertEqual(response.status_code, 200)

        # And also allowed with the same artist

        response = self.client.post(url, songplays[1], format='json')
        self.assertEqual(response.status_code, 200)

    def test_invalid_songplay(self):
        '''
        Checks invalid songplays don't get logged.
        '''

        # Work out the URL and use valid creds

        url = reverse('song_play_log')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.valid_token}')

        # Post and check our valid songplay

        songplay = {
            'song': {
                'display_artist': 'Artist of the Week',
                'artists': ['Artist of the Week']
            },
            'station': self.station_name
        }

        response = self.client.post(url, songplay, format='json')
        self.assertEqual(response.status_code, 400)

class SongTestCase(APITestCase):
    '''
    Song related tests.
    '''

    username = 'song_test'
    password = 'S0ngT3st!'
    email = 'song@example.com'
    artist = 'Song Test Artist/Singer'
    title = 'Song Test Title'

    def setUp(self):
        '''
        Setup basic auth, dummy artist and song.
        '''

        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create the artist

        artist = Artist(
            name=self.artist
        )

        artist.save()

        # Create the song

        song = Song(
            title=self.title,
            display_artist=self.artist
        )

        song.save()

        # Map them

        song.artists.add(artist)
        song.save()

    def test_get_song(self):
        '''
        Tests we can successfully pull a song through the API.
        '''

        # Grab the song

        url = reverse('song-detail', kwargs={'song': f'{self.artist} - {self.title}'})
        response = self.client.get(url)
        json_response = json.loads(response.content)

        # Check it's the right one

        self.assertEqual(json_response['display_artist'], self.artist)
        self.assertEqual(json_response['title'], self.title)

    def test_nonexist_song(self):
        '''
        Tests the retrieval of a non-existant song.
        '''

        url = reverse('song-detail', kwargs={'song': 'Nonsense Artist - Nonsense Song'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_badly_formatted_url(self):
        '''
        Tests a badly formatted song URL
        '''

        url = reverse('song-detail', kwargs={'song': 'Nonsense Artist by Nonsense Song'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
