'''
Admin Section
'''

from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from musicstats.models import Artist, Song, Station, OnAir2DataSource, EpgEntry, MarketingLiner, WordpressPresenterDataSource, Presenter

admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Station)
admin.site.register(OnAir2DataSource)
admin.site.register(EpgEntry)
admin.site.register(MarketingLiner)
admin.site.register(WordpressPresenterDataSource)
admin.site.register(Presenter)

TokenAdmin.raw_id_fields = ['user']
