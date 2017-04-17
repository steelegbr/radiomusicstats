'''
    Serializers for MusicStats data models.
'''

import models
from rest_framework import serializers

# Artist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Artist
        fields = ('name', 'thumbnail', 'image', 'musicbrainz_id', 'wiki_content')

# Song

class SongSerializer(serializers.ModelSerializer):

    artists = ArtistSerializer()

    class Meta:
        model = models.Song
        fields = ('display_artist', 'artists', 'title', 'thumbnail', 'image', 'musicbrainz_id', 'wiki_content', 'itunes_url', 'amazon_url')

# Song (simplified for input)

class SimpleSongSerializer(serializers.Serializer):

    artists = serializers.ListField(child=serializers.CharField())
    display_artist = serializers.CharField()
    title = serializers.CharField()

# Station

class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Station
        fields = ('name', 'logo', 'thumbnail', 'slogan')

# Song Play

class SongPlaySerializer(serializers.ModelSerializer):

    song = SimpleSongSerializer()
    station = serializers.CharField()

    class Meta:
        model = models.SongPlay
        fields = ('song', 'station', 'date_time')

# Vote

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Vote
        fields = ('song', 'station', 'date_time', 'vote')

