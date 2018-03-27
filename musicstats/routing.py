'''
    Websocket Channel Routing
'''

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from musicstats.consumers import NowPlayingConsumer
from channels.auth import AuthMiddlewareStack

websocket_urlpatterns = [
    url(r'^nowplaying/(?P<station_name>[^/]+)/$', NowPlayingConsumer)
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
