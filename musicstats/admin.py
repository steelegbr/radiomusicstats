from django.contrib import admin
from .models import Artist
from .models import Song
from .models import Station

admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Station)
