from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from serializers import SongPlaySerializer

# Placeholder

def index(request):
	return HttpResponse('Hello from the musicstats index.')


# Log a song play

@api_view(http_method_names=['POST', 'PUT'], exclude_from_schema=False)
def log_song_play(request):
    
    # Pull in the song play

    data = JSONParser().parse(request)
    serializer = SongPlaySerializer(data=data)

    if (serializer.is_valid()):
        return JsonResponse(serializer.data, status=200)
    else:
        return JsonResponse(serializer.errors, status=400)

