'''
URL configuration for MusicStats.
'''

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from musicstats.views import ArtistViewSet, SongViewSet, index, log_song_play, song_play_recent, \
    StationViewSet, epg_current

# Router for REST API

# pylint: disable=invalid-name
router = DefaultRouter()
router.register(r'artist', ArtistViewSet)
router.register(r'song', SongViewSet)
router.register(r'station', StationViewSet)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/logsongplay/?', log_song_play),
    url(
        r'^api/songplay/(?P<station_name>[^/.]+)/(?P<start_time>[0-9]+)/(?P<end_time>[0-9]+)/?',
        song_play_recent
    ),
    url(r'^api/songplay/(?P<station_name>[^/.]+)/?', song_play_recent),
    url(r'^api/epg/(?P<station_name>[^/.]+)/current/?', epg_current),
    url(r'^api/', include(router.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
