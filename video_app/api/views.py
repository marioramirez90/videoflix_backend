from auth_app.api.authentication import CookieJWTAuthentication
from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from video_app.models import Video

from .serializers import VideoListSerializer
from .utils import serve_hls_playlist, serve_hls_segment

ALLOWED_RESOLUTIONS = ('480p', '720p', '1080p')


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
        if resolution not in ALLOWED_RESOLUTIONS:
            return Response(
                {'detail': 'Resolution not supported.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not Video.objects.filter(id=movie_id).exists():
            return Response(
                {'detail': 'Video not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            return serve_hls_playlist(movie_id, resolution)
        except Http404:
            return Response(
                {'detail': 'Manifest not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )