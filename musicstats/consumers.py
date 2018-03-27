'''
    Websocket Consumers
'''

from channels.generic.websocket import WebsocketConsumer
from musicstats.models import Station, SongPlay
from musicstats.serializers import SongPlaySerializer
import logging
import json
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class NowPlayingConsumer(WebsocketConsumer):
    
    # Sends the now playing

    def send_now_playing(self, station):
        
        # Sanity check
        
        if not station:
            logger.debug('A station must be supplied in order to send the now playing info.')
            return
        
        # Get the last song play
        
        play_query = SongPlay.objects.all()
        play_query = play_query.filter(station__id=station.id)
        play_query = play_query.order_by('-date_time')[:1]
        
        if len(play_query) == 0:
            logger.debug('Could not find the last song played for {}.'.format(station))
            return
        
        song_play = play_query[0]
        song_play_serial = SongPlaySerializer(song_play)
        
        # Send the message to the channel
        
        async_to_sync(self.channel_layer.group_send)(
            self.station_group,
            {
                'type': 'now_playing',
                'message': song_play_serial.data
            }    
        )
    
    def connect(self):
        
        # Check we've got a valid station
        
        try:
            
            name = self.scope['url_route']['kwargs']['station_name']
            self.station = Station.objects.get(name=name)
            self.station_group = 'nowplaying_{}'.format(self.station.id)
        
        except Station.DoesNotExist:
            logger.debug('Station named {} does not exists.'.format(name))
            return
        
        # Join the channel
        
        async_to_sync(self.channel_layer.group_add)(
            self.station_group,
            self.channel_name
        )
        
        self.accept()
        
        # Trigger the update to the channel
        
        self.send_now_playing(self.station)
        
    def disconnect(self, code):
        pass
    
    def receive(self, text_data=None, bytes_data=None):
        logger.debug('Received message from user: {}'.format(text_data))
        
    def now_playing(self, event):
        
        logger.debug('Sending now playing information.')
        message = event['message']
        self.send(text_data = json.dumps(message))
        