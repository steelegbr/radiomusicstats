'''
    Serializers for MusicStats data
'''

from rest_framework import serializers
from musicstats.models import Artist, Song, SongPlay, Station

class ArtistSerializer(serializers.ModelSerializer):
    '''
    Serialiser for artists.
    '''

    class Meta:
        model = Artist
        fields = ('name', 'thumbnail', 'image', 'musicbrainz_id', 'wiki_content')

class SongSerializer(serializers.ModelSerializer):
    '''
    Serialiser for songs.
    '''

    artists = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Song
        fields = (
            'display_artist',
            'artists',
            'title',
            'thumbnail',
            'image',
            'musicbrainz_id',
            'wiki_content',
            'itunes_url',
            'amazon_url'
        )

class SimpleSongSerializer(serializers.ModelSerializer):
    '''
    Simplified serialiser for songs. Used for input (i.e. songplay).
    '''

    artists = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Song
        fields = ('display_artist', 'artists', 'title')

class StationSerializer(serializers.ModelSerializer):
    '''
    Serialiser for radio stations.
    '''

    class Meta:
        model = Station
        fields = (
            'name',
            'logo',
            'logo_inverse',
            'slogan',
            'primary_colour',
            'text_colour',
            'stream_aac_high',
            'stream_aac_low',
            'stream_mp3_high',
            'stream_mp3_low')

class SimpleSongPlaySerializer(serializers.ModelSerializer):
    '''
    Simplified serialiser for recording song plays.
    '''

    song = SimpleSongSerializer()
    station = serializers.CharField()

    class Meta:
        model = SongPlay
        fields = ('song', 'station', 'date_time')

class SongPlaySerializer(serializers.ModelSerializer):
    '''
    Serialiser for song plays.
    '''

    song = SongSerializer()
    station = StationSerializer()

    class Meta:
        model = SongPlay
        fields = ('song', 'station', 'date_time')
