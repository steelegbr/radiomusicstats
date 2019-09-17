'''
Admin Section
'''

from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from musicstats.models import Artist
from musicstats.models import Song
from musicstats.models import Station

admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Station)

TokenAdmin.raw_id_fields = ['user']
