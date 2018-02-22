'''
    ASGI Request Handler
'''

import os
import channels.asgi

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musicstats.settings")
channel_layer = channels.asgi.get_channel_layer()