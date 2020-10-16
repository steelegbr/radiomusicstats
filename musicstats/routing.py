"""
    Websocket Channel Routing
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url
from musicstats.consumers import NowPlayingConsumer

# pylint: disable=invalid-name

websocket_urlpatterns = [
    url(r"^nowplaying/(?P<station_name>[^/]+)/$", NowPlayingConsumer)
]

# pylint: disable=invalid-name

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
