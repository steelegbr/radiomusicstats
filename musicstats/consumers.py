'''
    Websocket Consumers
'''

from channels import Group
from channels.sessions import channel_session
from musicstats.models import Station
from asgiref.inmemory import channel_layer
import logging

logger = logging.getLogger(__name__)

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
    Group('station-{}'.format(station.id), channel_layer=message.channel_layer).add(message.reply_channel)
    message.channel_session['station'] = name
    
@channel_session
def ws_receive(message):
    logger.debug('Recieved message from user: {}'.format(message['text']))
    
@channel_session
def ws_disconnect(message):
    
    try:
        name = message.channel_session['station']
        station = Station.objects.get(name=name)
        Group('station-{}'.format(station.id), channel_layer=message.channel_layer).discard(message.reply_channel)
        logger.debug('Disconnected client {}:{} to now playing for {}'.format(message['client'][0], message['client'][1], name))
        
    except (KeyError, Station.DoesNotExist):
        logger.debug('Failed to get a valid station ({}) from the disconnecting user.'.format(name))