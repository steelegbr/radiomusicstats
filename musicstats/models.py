'''
    MusicStats Data Model
'''

from django.db import models

# Utility methods

def artist_thumbnail_path(instance, filename):
    return 'artists/thumbnails/{}_{}'.format(instance.id, filename)

def artist_image_path(instance, filename):
    return 'artists/images/{}_{}'.format(instance.id, filename)

def song_thumbnail_path(instance, filename):
    return 'songs/thumbnails/{}_{}'.format(instance.id, filename)

def song_image_path(instance, filename):
    return 'songs/images/{}_{}'.format(instance.id, filename)

def logo_thumbnail_path(instance, filename):
    return 'logos/thumbnails/{}_{}'.format(instance.id, filename)

def logo_image_path(instance, filename):
    return 'logos/images/{}_{}'.format(instance.id, filename)

# Artist

class Artist(models.Model):
    name = models.TextField(unique=True)
    thumbnail = models.ImageField(upload_to=artist_thumbnail_path)
    image = models.ImageField(upload_to=artist_image_path)
    musicbrainz_id = models.CharField(max_length=255)
    wiki_content = models.TextField()

    def __str__(self):
        return self.name

# Song

class Song(models.Model):
    display_artist = models.TextField()
    artists = models.ManyToManyField(Artist)
    title = models.TextField()
    thumbnail = models.ImageField(upload_to=song_thumbnail_path)
    image = models.ImageField(upload_to=song_image_path)
    musicbrainz_id = models.CharField(max_length=255)
    wiki_content = models.TextField()
    itunes_url = models.TextField()
    amazon_url = models.TextField()

    def __str__(self):
        return '{} - {}'.format(self.display_artist, self.title)

# Station

class Station(models.Model):
    name = models.TextField(unique=True)
    logo = models.ImageField(upload_to=logo_image_path)
    thumbnail = models.ImageField(upload_to=logo_thumbnail_path)
    slogan = models.TextField()

    def __ste__(self):
        return self.name

# Song Play on a Station

class SongPlay(models.Model):
    song = models.ForeignKey(Song)
    station = models.ForeignKey(Station)
    date_time = models.DateTimeField(auto_now=True)

# A vote for a song

class Vote(models.Model):
    song = models.ForeignKey(Song)
    station = models.ForeignKey(Station)
    date_time = models.DateTimeField(auto_now=True)

