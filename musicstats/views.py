from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import viewsets
from musicstats.serializers import SongPlaySerializer, SimpleSongPlaySerializer, ArtistSerializer, SongSerializer
from musicstats.models import Station, Song, Artist, SongPlay
from datetime import datetime
from channels import Group

# Placeholder

def index(request):
	return HttpResponse('Hello from the musicstats index.')


# Log a song play

@api_view(http_method_names=['POST', 'PUT'], exclude_from_schema=False)
def log_song_play(request):
    
    # Pull in the song play

    data = JSONParser().parse(request)
    serializer = SimpleSongPlaySerializer(data=data)

    if (serializer.is_valid()):

        # Obtain the station

        stations = Station.objects.filter(name=serializer.data['station'])[:1]
        if (len(stations) > 0) :
            station = stations[0]
        else:
            return JsonResponse({'Error': 'Failed to find a matching station for the request.'}, status=400)

        # Check the current user is allowed to make updates

        update_account = station.update_account
        if ((not update_account) or (update_account.id != request.user.id)):
            return JsonResponse({'Error': 'Not authenticated to make this request.'}, status=401)

        # Search for an existing song

        song_query = Song.objects.filter(title=serializer.data['song']['title'])
        for artist in serializer.data['song']['artists']:
            song_query = song_query.filter(artists__name=artist)

        # Build a new song if we have to

        if (len(song_query) == 0):

            # Get the basics in place

            song = Song()
            song.title = serializer.data['song']['title']
            song.display_artist = serializer.data['song']['display_artist']
            song.save()

            # Flesh out the artists

            for artist in serializer.data['song']['artists']:

                # Try for the artist in the database

                artist_query = Artist.objects.filter(name=artist)
                if (len(artist_query) == 0):

                    # Create the new artist

                    new_artist = Artist()
                    new_artist.name = artist
                    new_artist.save()
                    song.artists.add(new_artist)

                else:

                    # Add the existing artist to the list

                    song.artists.add(artist_query[0])

            # Save the song

            song.save()

        else:
            song = song_query[0]

        # Now create and save the song play

        song_play = SongPlay()
        song_play.station = station
        song_play.song = song
        song_play.save()
        
        # Inform websocket listeners
        
        song_play_serial = SongPlaySerializer(song_play)
        Group('musicstats-{}'.format(station.name)).send(song_play_serial)

        # Let the user know we're successful - send the song back

        return JsonResponse(song_play_serial.data, status=200, safe=False)

    else:
        return JsonResponse(serializer.errors, status=400)

# Artist

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    lookup_field = 'name'
    lookup_value_regex = '.*'

# Song

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    lookup_field = 'song'
    lookup_value_regex = '.*'

    def get_object(self, queryset=None):

        # Split out the artist and title

        try:
            combined = self.kwargs['song']
            split_parts = combined.split(' - ')
            artist = split_parts[0]
            title = split_parts[1]

        except:
            raise Http404

        song = get_object_or_404(Song, display_artist=artist, title=title)
        return song

# Song play history

@api_view(http_method_names=['GET'], exclude_from_schema=False)
def song_play_recent(request, station_name=None, start_time=None, end_time=None):

    # Pull out the station

    station = get_object_or_404(Station, name=station_name)

    # See or set a limit

    try:
        limit = int(request.GET.get('limit'))
        if (limit <= 0):
            limit = 10
    except:
        limit = 10

    # Check the start and end time

    if (start_time and end_time):
        try:
            start = timezone.make_aware(datetime.fromtimestamp(int(start_time)), timezone.get_current_timezone())
            end = timezone.make_aware(datetime.fromtimestamp(int(end_time)), timezone.get_current_timezone())
        except:
            return JsonResponse({'Error': 'Invalid start and end time supplied.'}, status=400)
    else:
        start = timezone.make_aware(datetime.fromtimestamp(0), timezone.get_current_timezone())
        end = timezone.now()

    # Pull out the song history

    play_query = SongPlay.objects.all()
    play_query = play_query.filter(station__id=station.id)
    play_query = play_query.filter(date_time__gte=start)
    play_query = play_query.filter(date_time__lte=end)
    play_query = play_query.order_by('-date_time')[:limit]

    song_play_serial = SongPlaySerializer(play_query, many=True)
    return JsonResponse(song_play_serial.data, status=200, safe=False)
