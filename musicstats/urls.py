from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from musicstats.views import ArtistViewSet, SongViewSet, index, log_song_play, song_play_recent

# Router for REST API

router = DefaultRouter()
router.register(r'artist', ArtistViewSet)
router.register(r'song', SongViewSet)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/logsongplay/?', log_song_play),
    url(r'^api/songplay/(?P<station_name>[^/.]+)/(?P<start_time>[0-9]+)/(?P<end_time>[0-9]+)/?', song_play_recent),
    url(r'^api/songplay/(?P<station_name>[^/.]+)/?', song_play_recent),
    url(r'^api/', include(router.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
