from auth_app.api.authentication import CookieJWTAuthentication
from django.core.cache import cache
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from video_app.models import Video

from .serializers import VideoListSerializer
from .utils import get_hls_playlist_response, get_hls_segment_response

VIDEO_CACHE_KEY = 'video_list_cache'
CACHE_TTL = 60 * 15


class VideoListView(generics.ListAPIView):
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Video.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        cached_data = cache.get(VIDEO_CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data)
        response = super().list(request, *args, **kwargs)
        cache.set(VIDEO_CACHE_KEY, response.data, CACHE_TTL)
        return response


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
