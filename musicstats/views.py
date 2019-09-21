'''
Provides the V part of MVC for this application.
'''

from datetime import datetime
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework import viewsets
from channels.layers import get_channel_layer
from musicstats.serializers import SongPlaySerializer, \
    SimpleSongPlaySerializer, ArtistSerializer, SongSerializer, \
        StationSerializer, EpgEntrySerializer
from musicstats.models import Station, Song, Artist, SongPlay, EpgEntry

# Placeholder

def index(request):
    '''
    Simple hello/index page. Really needs replaced with something a bit more like a web app.
    '''
    return HttpResponse('Hello from the musicstats index.')


@api_view(http_method_names=['POST', 'PUT'])
def log_song_play(request):
    '''
    Logs a song play.
    '''

    # Pull in the song play

    data = JSONParser().parse(request)
    serializer = SimpleSongPlaySerializer(data=data)

    if serializer.is_valid():

        # Obtain the station

        stations = Station.objects.filter(name=serializer.data['station'])[:1]
        if stations:
            station = stations[0]
        else:
            return JsonResponse(
                {'Error': 'Failed to find a matching station for the request.'},
                status=400
            )

        # Check the current user is allowed to make updates

        update_account = station.update_account
        if ((not update_account) or (update_account.id != request.user.id)):
            return JsonResponse({'Error': 'Not authenticated to make this request.'}, status=401)

        # Search for an existing song

        song_query = Song.objects.filter(title=serializer.data['song']['title'])
        for artist in serializer.data['song']['artists']:
            song_query = song_query.filter(artists__name=artist)

        # Build a new song if we have to

        if not song_query:

            # Get the basics in place

            song = Song()
            song.title = serializer.data['song']['title']
            song.display_artist = serializer.data['song']['display_artist']
            song.save()

            # Flesh out the artists

            for artist in serializer.data['song']['artists']:

                # Try for the artist in the database

                artist_query = Artist.objects.filter(name=artist)
                if not artist_query:

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
        song_play_serial = SongPlaySerializer(song_play)

        # Inform websocket listeners

        layer = get_channel_layer()
        async_to_sync(layer.group_send) \
            (
                f"nowplaying_{station.id}",
                {
                    'type': 'now_playing',
                    'message': song_play_serial.data
                }
            )

        # Let the user know we're successful - send the song back

        return JsonResponse(song_play_serial.data, status=200, safe=False)

    else:
        return JsonResponse(serializer.errors, status=400)

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    Read only artists viewset.
    '''

    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    lookup_field = 'name'
    lookup_value_regex = '.*'

class StationViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    Read only station viewset.
    '''

    queryset = Station.objects.all()
    serializer_class = StationSerializer
    lookup_field = 'name'

class SongViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    Read only songs viewset.
    '''

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    lookup_field = 'song'
    lookup_value_regex = '.*'

    def get_object(self):

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

@api_view(http_method_names=['GET'])
def song_play_recent(request, station_name=None, start_time=None, end_time=None):
    '''
    Displays the song play history for a specified radio station.
    '''

    # Pull out the station

    station = get_object_or_404(Station, name=station_name)

    # See or set a limit

    try:
        limit = int(request.GET.get('limit'))
        if limit <= 0:
            limit = 10
    except ValueError:
        limit = 10
    except TypeError:
        limit = 10

    # Check the start and end time

    if (start_time and end_time):
        try:
            start = timezone.make_aware(
                datetime.fromtimestamp(int(start_time)),
                timezone.get_current_timezone()
            )
            end = timezone.make_aware(
                datetime.fromtimestamp(int(end_time)),
                timezone.get_current_timezone()
            )
        except ValueError:
            return JsonResponse({'Error': 'Invalid start and end time supplied.'}, status=400)
        except TypeError:
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

@api_view(http_method_names=['GET'])
def epg_current(request, station_name=None):
    '''
    Obtains the current EPG entry for a station.
    '''

    # Get the station

    station = get_object_or_404(Station, name=station_name)

    # Obtain the EPG entry

    current_epg = EpgEntry.objects \
                    .filter(station=station) \
                    .order_by('-last_updated') \
                    .first()

    if current_epg:
        epg_serial = EpgEntrySerializer(current_epg)
        return JsonResponse(epg_serial.data, status=200, safe=False)
    else:
        return JsonResponse({'Error': 'Failed to find an EPG entry for that station.'}, status=404)
