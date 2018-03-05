'''
    Websocket Consumers
'''

from channels import Group
from channels.sessions import channel_session
from musicstats.models import Station, SongPlay
from musicstats.serializers import SongPlaySerializer
from asgiref.inmemory import channel_layer
import logging
import json

logger = logging.getLogger(__name__)

# Sends the now playing

def send_now_playing(station):
    
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
    
    logger.debug('Sending now playing for {}.'.format(station))
    Group('station-{}'.format(station.id)).send({'text': json.dumps(song_play_serial.data)})

@channel_session
def ws_connect(message):

    # Get the station name from the URL
    
    try:
    
        prefix, name = message['path'].strip('/').split('/')
        if prefix != 'nowplaying':
            logger.debug('Invalid websocket path: {}'.format(prefix))
            return
        
        station = Station.objects.get(name=name)
        
    except ValueError:
        logger.debug('Invalid websocket path: {}'.format(prefix))
        return
    
    except Station.DoesNotExist:
        logger.debug('Station named {} does not exists.'.format(name))
        return
    
    # Add the user to the group
    
    logger.debug('Connecting client {}:{} to now playing for {}'.format(message['client'][0], message['client'][1], name))    
    Group('station-{}'.format(station.id)).add(message.reply_channel)
    message.channel_session['station'] = name
    
    # Send the latest now playing to the channel
    
    send_now_playing(station)
    
@channel_session
def ws_receive(message):
    logger.debug('Received message from user: {}'.format(message['text']))
    
@channel_session
def ws_disconnect(message):
    
    try:
        name = message.channel_session['station']
        station = Station.objects.get(name=name)
        Group('station-{}'.format(station.id), channel_layer=message.channel_layer).discard(message.reply_channel)
        
    except (KeyError, Station.DoesNotExist):
        if (name):
            logger.debug('Failed to get a valid station ({}) from the disconnecting user.'.format(name))
        else:
            logger.debug('Unable to disconnect client as no station was supplied.')