"""
    Radio Music Stats - Radio Music Statistics and Now Playing
    Copyright (C) 2017-2021 Marc Steele

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from datetime import datetime, time
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from musicstats.serializers import (
    SongPlaySerializer,
    SimpleSongPlaySerializer,
    ArtistSerializer,
    SongSerializer,
    StationSerializer,
    EpgEntrySerializer,
    MarketingLinerSerializer,
    PresenterSerializer,
)
from musicstats.models import (
    Station,
    Song,
    Artist,
    SongPlay,
    EpgEntry,
    MarketingLiner,
    Presenter,
)

# Placeholder


def index(request):
    """
    Simple hello/index page. Really needs replaced with something a bit more like a web app.
    """
    return HttpResponse("Hello from the musicstats index.")


@api_view(http_method_names=["POST", "PUT"])
def log_song_play(request):
    """
    Logs a song play.
    """

    # Pull in the song play

    data = JSONParser().parse(request)
    serializer = SimpleSongPlaySerializer(data=data)

    if serializer.is_valid():

        # Obtain the station

        station = Station.objects.filter(name=serializer.data["station"]).first()
        if not station:
            return JsonResponse(
                {"Error": "Failed to find a matching station for the request."},
                status=400,
            )

        # Check the current user is allowed to make updates

        update_account = station.update_account
        if (not update_account) or (update_account.id != request.user.id):
            return JsonResponse(
                {"Error": "Not authenticated to make this request."}, status=401
            )

        # Search for an existing song

        song_query = Song.objects.filter(title=serializer.data["song"]["title"])
        for artist in serializer.data["song"]["artists"]:
            song_query = song_query.filter(artists__name=artist)

        # Build a new song if we have to

        if not song_query:

            # Get the basics in place

            song = Song()
            song.title = serializer.data["song"]["title"]
            song.display_artist = serializer.data["song"]["display_artist"]
            song.save()

            # Flesh out the artists

            for artist in serializer.data["song"]["artists"]:

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

                    song.artists.add(artist_query.first())

            # Save the song

            song.save()

        else:

            # Only grab the first song

            song = song_query.first()

            # Check we're not matching the previous song

            last_songplay = (
                SongPlay.objects.filter(station=station).order_by("-date_time").first()
            )

            if last_songplay and song.id == last_songplay.song.id:
                return JsonResponse(
                    {"Error": "This song play has already been recorded."}, status=400
                )

        # Now create and save the song play

        song_play = SongPlay()
        song_play.station = station
        song_play.song = song
        song_play.save()
        song_play_serial = SongPlaySerializer(song_play)

        # Inform websocket listeners

        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            f"nowplaying_{station.id}",
            {"type": "now_playing", "message": song_play_serial.data},
        )

        # Let the user know we're successful - send the song back

        return JsonResponse(song_play_serial.data, status=200, safe=False)

    else:
        return JsonResponse(serializer.errors, status=400)


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read only artists viewset.
    """

    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    lookup_field = "name"
    lookup_value_regex = ".*"


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read only station viewset.
    """

    queryset = Station.objects.all()
    serializer_class = StationSerializer
    lookup_field = "name"


class SongViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read only songs viewset.
    """

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    lookup_field = "song"
    lookup_value_regex = ".*"

    def get_object(self):

        # Split out the artist and title

        try:
            combined = self.kwargs["song"]
            split_parts = combined.split(" - ")
            artist = split_parts[0]
            title = split_parts[1]

        except:
            raise Http404

        song = get_object_or_404(Song, display_artist=artist, title=title)
        return song


class MarketingLinerList(generics.ListAPIView):
    """
    Lists marketing liners (filtered by station).
    """

    serializer_class = MarketingLinerSerializer

    def get_queryset(self):
        """
        Returns the list of liners associated with a station.
        """

        station = get_object_or_404(Station, name=self.kwargs["station_name"])
        return MarketingLiner.objects.filter(station=station)


class SongPlayList(generics.ListAPIView):
    """
    Songplay list. Filters by station, start, end and limits.
    """

    serializer_class = SongPlaySerializer

    def get_queryset(self):
        """
        Returns the song plays for a station.
        """

        station = get_object_or_404(Station, name=self.kwargs["station_name"])

        # Check (or default) our start and end time

        start = timezone.make_aware(
            datetime.fromtimestamp(0), timezone.get_current_timezone()
        )
        end = timezone.now()

        if "start_time" in self.kwargs and "end_time" in self.kwargs:

            start_time = self.kwargs["start_time"]
            end_time = self.kwargs["end_time"]

            if start_time and end_time:
                try:
                    start = timezone.make_aware(
                        datetime.fromtimestamp(int(start_time)),
                        timezone.get_current_timezone(),
                    )
                    end = timezone.make_aware(
                        datetime.fromtimestamp(int(end_time)),
                        timezone.get_current_timezone(),
                    )
                except OverflowError:
                    raise ValidationError("Invalid start and/or end time supplied.")

        return (
            SongPlay.objects.all()
            .filter(station=station)
            .filter(date_time__gte=start)
            .filter(date_time__lte=end)
            .order_by("-date_time")
        )


class EpgCurrent(generics.RetrieveAPIView):
    """
    Obtains the current EPG entry for a station.
    """

    serializer_class = EpgEntrySerializer

    def get_queryset(self):
        """
        Obtains the EPG entries in order.
        """

        return EpgEntry.objects.all()

    def get_object(self):
        station = get_object_or_404(Station, name=self.kwargs["station_name"])
        now = datetime.today()
        return (
            self.get_queryset()
            .filter(
                station=station,
                day=now.weekday(),
                start__lte=time(now.hour, now.minute),
            )
            .order_by("-start")
            .first()
        )


class EpgDay(APIView):
    """
    Obtains a specific day's EPG entries
    """

    def get(self, request, **kwargs):

        # Read in the station and day from the user

        station = get_object_or_404(Station, name=self.kwargs["station_name"])

        # Perform the search

        epg = {}

        for day in range(0, 7):
            epg[day] = EpgEntrySerializer(
                EpgEntry.objects.filter(station=station, day=day).order_by("start"),
                many=True,
            ).data

        return Response(epg)


class PresenterList(generics.ListAPIView):
    """Lists the presenters, filtered by station."""

    serializer_class = PresenterSerializer

    def get_queryset(self):
        """Returns the list of presenters associated with a station."""

        station = get_object_or_404(Station, name=self.kwargs["station_name"])
        return Presenter.objects.filter(station=station).order_by("name")


class NowPlayingPlain(APIView):
    """
    Provides a plain text now playing view for a given station.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, station_name):
        """
        Plain text view of the now playing song for a station.
        """

        station = get_object_or_404(Station, name=station_name)

        songplay = (
            SongPlay.objects.filter(station=station).order_by("-date_time").first()
        )

        if songplay:
            return HttpResponse(
                f"{songplay.song.display_artist} - {songplay.song.title}"
            )
        else:
            raise Http404