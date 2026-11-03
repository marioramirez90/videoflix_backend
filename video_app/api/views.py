from auth_app.api.authentication import CookieJWTAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from video_app.models import Video

from .serializers import VideoListSerializer


class VideoListView(generics.ListAPIView):
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Video.objects.all().order_by('-created_at')