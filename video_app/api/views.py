"""API views for retrieving video listings, HLS master playlists, and video segments."""

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
    """View to list all available videos ordered by newest first, using Redis caching."""

    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve all Video instances ordered descending by creation date.

        Returns:
            QuerySet: Ordered collection of Video objects.
        """
        return Video.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """Return video listing from cache if available; otherwise query database and cache result.

        Args:
            request (Request): The incoming request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 with serialized list of video objects.
        """
        cached_data = cache.get(VIDEO_CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data)
        response = super().list(request, *args, **kwargs)
        cache.set(VIDEO_CACHE_KEY, response.data, CACHE_TTL)
        return response


class VideoPlaylistView(APIView):
    """View to serve HLS master playlist files (.m3u8) for a specified video and resolution."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, *args, **kwargs):
        """Handle GET request for an HLS playlist manifest.

        Args:
            request (Request): The incoming request.
            movie_id (int): Video ID.
            resolution (str): Video resolution ('480p', '720p', '1080p').
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FileResponse or Response: Manifest file stream or 404 error response.
        """
        return get_hls_playlist_response(movie_id, resolution)


class VideoSegmentView(APIView):
    """View to serve binary MPEG-TS video chunks (.ts) for HLS streaming."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment, *args, **kwargs):
        """Handle GET request for an individual HLS video segment.

        Args:
            request (Request): The incoming request.
            movie_id (int): Video ID.
            resolution (str): Video resolution ('480p', '720p', '1080p').
            segment (str): Segment file name (e.g., 'segment_000.ts').
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FileResponse or Response: Binary segment file stream or 404 error response.
        """
        return get_hls_segment_response(movie_id, resolution, segment)
