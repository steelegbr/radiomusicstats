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

from django.urls import re_path, include
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
    re_path(r"^$", index, name="index"),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^api/logsongplay/?", log_song_play, name="song_play_log"),
    re_path(
        r"^api/songplay/(?P<station_name>[^/.]+)/(?P<start_time>[0-9]+)/(?P<end_time>[0-9]+)/?",
        SongPlayList.as_view(),
        name="song_play_specific",
    ),
    re_path(
        r"^api/songplay/(?P<station_name>[^/.]+)/?",
        SongPlayList.as_view(),
        name="song_play_recent",
    ),
    re_path(
        r"^api/epg/(?P<station_name>[^/.]+)/current/?",
        EpgCurrent.as_view(),
        name="epg_current",
    ),
    re_path(r"^api/epg/(?P<station_name>[^/.]+)/?", EpgDay.as_view(), name="epg_day"),
    re_path(
        r"^api/liners/(?P<station_name>[^/.]+)/?",
        MarketingLinerList.as_view(),
        name="marketing_liners",
    ),
    re_path(
        r"^api/presenters/(?P<station_name>[^/.]+)/?",
        PresenterList.as_view(),
        name="presenters",
    ),
    re_path(
        r"^api/nowplaying/(?P<station_name>[^/.]+)/?",
        NowPlayingPlain.as_view(),
        name="now_playing_plain",
    ),
    re_path(r"^api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
