'''
URL configuration for MusicStats.
'''

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from musicstats.views import ArtistViewSet, SongViewSet, index, log_song_play, \
    StationViewSet, EpgCurrent, SongPlayList, MarketingLinerList, EpgDay

# Router for REST API

# pylint: disable=invalid-name
router = DefaultRouter()
router.register(r'artist', ArtistViewSet)
router.register(r'song', SongViewSet)
router.register(r'station', StationViewSet)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/logsongplay/?', log_song_play, name='song_play_log'),
    url(
        r'^api/songplay/(?P<station_name>[^/.]+)/(?P<start_time>[0-9]+)/(?P<end_time>[0-9]+)/?',
        SongPlayList.as_view(),
        name='song_play_specific'
    ),
    url(
        r'^api/songplay/(?P<station_name>[^/.]+)/?',
        SongPlayList.as_view(),
        name='song_play_recent'
    ),
    url(
        r'^api/epg/(?P<station_name>[^/.]+)/current/?',
        EpgCurrent.as_view(),
        name='epg_current'
    ),
    url(
        r'^api/epg/(?P<station_name>[^/.]+)/?',
        EpgDay.as_view(),
        name='epg_day'
    ),
    url(
        r'^api/liners/(?P<station_name>[^/.]+)/?',
        MarketingLinerList.as_view(),
        name='marketing_liners'
    ),
    url(r'^api/', include(router.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
