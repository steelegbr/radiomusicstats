"""
    MusicStats Data Model
"""

import calendar
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from colorful.fields import RGBColorField
from polymorphic.models import PolymorphicModel
from timezone_field import TimeZoneField

# Utility methods


def artist_thumbnail_path(instance, filename):
    """
    Obtains the artist thumbnail path.
    """
    return f"artists/thumbnails/{instance.id}_{filename}"


def artist_image_path(instance, filename):
    """
    Obtains the artist image path.
    """
    return f"artists/images/{instance.id}_{filename}"


def song_thumbnail_path(instance, filename):
    """
    Obtains the song thumbnail path.
    """
    return f"songs/thumbnails/{instance.id}_{filename}"


def song_image_path(instance, filename):
    """
    Obtains the song image path.
    """
    return f"songs/images/{instance.id}_{filename}"


def logo_image_path(instance, filename):
    """
    Obtains the logo image path.
    """
    return f"logos/images/{instance.id}_{filename}"


def logo_inverse_path(instance, filename):
    """
    Obtains the inverse logo image path.
    """
    return f"logos/images/inverse_{instance.id}_{filename}"


def logo_square_path(instance, filename):
    """
    Obtains the square logo image path.
    """
    return f"logos/images/square_{instance.id}_{filename}"


class Artist(models.Model):
    """
    Represents an artist that can be attached to songs.
    """

    name = models.TextField(unique=True)
    thumbnail = models.ImageField(upload_to=artist_thumbnail_path, blank=True)
    image = models.ImageField(upload_to=artist_image_path, blank=True)
    musicbrainz_id = models.CharField(max_length=255)
    wiki_content = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Song(models.Model):
    """
    A song that can be played on a radio station.
    """

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
        ordering = ["display_artist", "title"]


class EpgDataSource(PolymorphicModel):
    """
    Base class for EPG data sources.
    """

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class OnAir2DataSource(EpgDataSource):
    """
    OnAir 2 website EPG data source.
    """

    schedule_url = models.URLField()

    def __str__(self):
        return f"{self.name} ({self.schedule_url})"


class PresenterDataSource(PolymorphicModel):
    """Base class for presenter list data sources."""

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class WordpressPresenterDataSource(PresenterDataSource):
    """Wordpress presenter data source."""

    presenter_list_url = models.URLField()

    def __str__(self):
        return f"{self.name} ({self.presenter_list_url})"


class Station(models.Model):
    """
    A radio station.
    """

    name = models.TextField(unique=True)
    logo = models.ImageField(upload_to=logo_image_path, blank=True)
    logo_inverse = models.ImageField(upload_to=logo_inverse_path, blank=True)
    logo_square = models.ImageField(upload_to=logo_square_path, blank=True)
    slogan = models.TextField()
    update_account = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, blank=True, null=True
    )
    primary_colour = RGBColorField()
    text_colour = RGBColorField()
    stream_aac_high = models.URLField()
    stream_aac_low = models.URLField()
    stream_mp3_high = models.URLField()
    stream_mp3_low = models.URLField()
    timezone = TimeZoneField(default="Europe/London")
    epg = models.ForeignKey(
        EpgDataSource, on_delete=models.CASCADE, blank=True, null=True
    )
    presenters = models.ForeignKey(
        PresenterDataSource, on_delete=models.CASCADE, blank=True, null=True
    )
    use_liners = models.BooleanField(default=False)
    liner_ratio = models.DecimalField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        max_digits=2,
        decimal_places=1,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class SongPlay(models.Model):
    """
    Instance of a song playing on a radio station.
    """

    song = models.ForeignKey(Song, on_delete=models.DO_NOTHING)
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING)
    date_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.song} on {self.station} at {self.date_time}"


class EpgEntry(models.Model):
    """
    An entry on the EPG.
    """

    title = models.TextField()
    description = models.TextField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    image = models.URLField()
    start = models.TimeField()
    day = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)], null=True
    )

    def __str__(self):
        if self.day is not None:
            return f"[{calendar.day_name[self.day]}][{self.start}] {self.title} on {self.station}"
        else:
            return f"[{self.start}] {self.title} on {self.station}"


class Podcast(models.Model):
    """
    A podcast attached to a radio station
    """

    name = models.TextField()
    feed = models.URLField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.station})"

    class Meta:
        unique_together = ["name", "station"]


class MarketingLiner(models.Model):
    """
    A marketing liner associated with a station.
    """

    line = models.TextField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    def __str__(self):
        if self.station:
            return f"[{self.station}] - {self.line}"
        else:
            return self.line

    class Meta:
        unique_together = ["line", "station"]


class Presenter(models.Model):
    """A presenter on the station."""

    name = models.TextField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    biography = models.TextField()
    image = models.URLField()
    url = None

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ["name", "station"]
