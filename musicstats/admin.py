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

from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from musicstats.models import (
    Artist,
    Song,
    Station,
    OnAir2DataSource,
    ProRadioDataSource,
    EpgEntry,
    MarketingLiner,
    WordpressPresenterDataSource,
    Presenter,
)

admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Station)
admin.site.register(OnAir2DataSource)
admin.site.register(ProRadioDataSource)
admin.site.register(EpgEntry)
admin.site.register(MarketingLiner)
admin.site.register(WordpressPresenterDataSource)
admin.site.register(Presenter)

TokenAdmin.raw_id_fields = ["user"]
