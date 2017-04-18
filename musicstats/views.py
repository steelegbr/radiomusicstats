from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from serializers import SongPlaySerializer, SimpleSongPlaySerializer
from models import Station, Song, Artist, SongPlay

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

        # Let the user know we're successful - send the song back

        song_play_serial = SongPlaySerializer(song_play)
        return JsonResponse(song_play_serial.data, status=200, safe=False)

    else:
        return JsonResponse(serializer.errors, status=400)

