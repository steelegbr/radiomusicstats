'''
    MusicStats Data Model
'''

from django.db import models
from colorful.fields import RGBColorField
from polymorphic.models import PolymorphicModel

# Utility methods

def artist_thumbnail_path(instance, filename):
    '''
    Obtains the artist thumbnail path.
    '''
    return f"artists/thumbnails/{instance.id}_{filename}"

def artist_image_path(instance, filename):
    '''
    Obtains the artist image path.
    '''
    return f"artists/images/{instance.id}_{filename}"

def song_thumbnail_path(instance, filename):
    '''
    Obtains the song thumnail path.
    '''
    return f"songs/thumbnails/{instance.id}_{filename}"

def song_image_path(instance, filename):
    '''
    Obtains the song image path.
    '''
    return f"songs/images/{instance.id}_{filename}"

def logo_image_path(instance, filename):
    '''
    Obtains the logo image path.
    '''
    return f"logos/images/{instance.id}_{filename}"

def logo_inverse_path(instance, filename):
    '''
    Obtains the inverse logo thumbnail path.
    '''
    return f"logos/images/inverse_{instance.id}_{filename}"

class Artist(models.Model):
    '''
    Represents an artist that can be attached to songs.
    '''

    name = models.CharField(unique=True, max_length=768)
    thumbnail = models.ImageField(upload_to=artist_thumbnail_path, blank=True)
    image = models.ImageField(upload_to=artist_image_path, blank=True)
    musicbrainz_id = models.CharField(max_length=255)
    wiki_content = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Song(models.Model):
    '''
    A song that can be played on a radio station.
    '''

    display_artist = models.TextField()
    artists = models.ManyToManyField(Artist)
    title = models.TextField()
    thumbnail = models.ImageField(upload_to=song_thumbnail_path, blank=True)
    image = models.ImageField(upload_to=song_image_path, blank=True)
    musicbrainz_id = models.CharField(max_length=255, blank=True)
    wiki_content = models.TextField(blank=True)
    itunes_url = models.TextField(blank=True)
    amazon_url = models.TextField(blank=True)

    def __str__(self):
        return f"{self.display_artist} - {self.title}"

    class Meta:
        ordering = ['display_artist', 'title']

class EpgDataSource(PolymorphicModel):
    '''
    Base class for EPG data sources.
    '''

    name = models.CharField(max_length=768, unique=True)

    def __str__(self):
        return self.name

class OnAir2DataSource(EpgDataSource):
    '''
    OnAir 2 website EPG data source.
    '''

    schedule_url = models.URLField()

    def __str__(self):
        return f"{self.name} ({self.schedule_url})"

class Station(models.Model):
    '''
    A radio station.
    '''

    name = models.CharField(unique=True, max_length=768)
    logo = models.ImageField(upload_to=logo_image_path, blank=True)
    logo_inverse = models.ImageField(upload_to=logo_inverse_path, blank=True)
    slogan = models.TextField()
    update_account = models.ForeignKey('auth.User', on_delete=models.CASCADE, blank=True, null=True)
    primary_colour = RGBColorField()
    text_colour = RGBColorField()
    stream_aac_high = models.URLField()
    stream_aac_low = models.URLField()
    stream_mp3_high = models.URLField()
    stream_mp3_low = models.URLField()
    epg = models.ForeignKey(EpgDataSource, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class SongPlay(models.Model):
    '''
    Instance of a song playing on a radio station.
    '''

    song = models.ForeignKey(Song, on_delete=models.DO_NOTHING)
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING)
    date_time = models.DateTimeField(auto_now=True)
