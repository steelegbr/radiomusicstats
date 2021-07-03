"""
    Radio Music Stats - Radio Music Statistics and Now Playing
    Copyright (C) 2017-2021 Marc Steele

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from musicstats.views import (
    ArtistViewSet,
    SongViewSet,
    index,
    log_song_play,
    StationViewSet,
    EpgCurrent,
    SongPlayList,
    MarketingLinerList,
    EpgDay,
    PresenterList,
    NowPlayingPlain,
)

# Router for REST API

# pylint: disable=invalid-name
router = DefaultRouter()
router.register(r"artist", ArtistViewSet)
router.register(r"song", SongViewSet)
router.register(r"station", StationViewSet)

urlpatterns = [
    url(r"^$", index, name="index"),
    url(r"^admin/", admin.site.urls),
    url(r"^api/logsongplay/?", log_song_play, name="song_play_log"),
    url(
        r"^api/songplay/(?P<station_name>[^/.]+)/(?P<start_time>[0-9]+)/(?P<end_time>[0-9]+)/?",
        SongPlayList.as_view(),
        name="song_play_specific",
    ),
    url(
        r"^api/songplay/(?P<station_name>[^/.]+)/?",
        SongPlayList.as_view(),
        name="song_play_recent",
    ),
    url(
        r"^api/epg/(?P<station_name>[^/.]+)/current/?",
        EpgCurrent.as_view(),
        name="epg_current",
    ),
    url(r"^api/epg/(?P<station_name>[^/.]+)/?", EpgDay.as_view(), name="epg_day"),
    url(
        r"^api/liners/(?P<station_name>[^/.]+)/?",
        MarketingLinerList.as_view(),
        name="marketing_liners",
    ),
    url(
        r"^api/presenters/(?P<station_name>[^/.]+)/?",
        PresenterList.as_view(),
        name="presenters",
    ),
    url(
        r"^api/nowplaying/(?P<station_name>[^/.]+)/?",
        NowPlayingPlain.as_view(),
        name="now_playing_plain",
    ),
    url(r"^api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
