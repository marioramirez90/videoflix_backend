from auth_app.api.authentication import CookieJWTAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from video_app.models import Video

from .serializers import VideoListSerializer
from .utils import get_hls_playlist_response, get_hls_segment_response


class VideoListView(generics.ListAPIView):
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Video.objects.all().order_by('-created_at')


class VideoPlaylistView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, *args, **kwargs):
        return get_hls_playlist_response(movie_id, resolution)


class VideoSegmentView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment, *args, **kwargs):
        return get_hls_segment_response(movie_id, resolution, segment)
