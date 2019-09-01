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
    name = models.CharField(unique=True, max_length=768)
    thumbnail = models.ImageField(upload_to=artist_thumbnail_path, blank=True)
    image = models.ImageField(upload_to=artist_image_path, blank=True)
    musicbrainz_id = models.CharField(max_length=255)
    wiki_content = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Song

class Song(models.Model):
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
        return '{} - {}'.format(self.display_artist, self.title)

    class Meta:
        ordering = ['display_artist', 'title']

# Station

class Station(models.Model):
    name = models.CharField(unique=True, max_length=768)
    logo = models.ImageField(upload_to=logo_image_path, blank=True)
    thumbnail = models.ImageField(upload_to=logo_thumbnail_path, blank=True)
    slogan = models.TextField()
    update_account = models.ForeignKey('auth.User', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Song Play on a Station

class SongPlay(models.Model):
    song = models.ForeignKey(Song, on_delete=models.DO_NOTHING)
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING)
    date_time = models.DateTimeField(auto_now=True)

# A vote for a song

class Vote(models.Model):

    VOTE_OPTIONS = {
            ('U', 'Upvote'),
            ('D', 'Downvote'),
            ('B', 'Burned')
    }

    song = models.ForeignKey(Song, on_delete=models.DO_NOTHING)
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING)
    date_time = models.DateTimeField(auto_now=True)
    vote = models.CharField(max_length=1, choices=VOTE_OPTIONS, default='U')

