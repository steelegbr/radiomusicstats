'''
MusicStats unit tests
'''

import json
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.urls import reverse
from musicstats.models import Station

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
