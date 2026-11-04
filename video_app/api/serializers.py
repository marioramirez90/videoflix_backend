"""Serializers for video catalog representations and metadata."""

from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer representing video metadata for listing and dashboard displays.

    Builds an absolute URI for the thumbnail asset when available.
    """

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('id', 'created_at', 'title', 'description', 'thumbnail_url', 'category')

    def get_thumbnail_url(self, obj):
        """Construct the absolute URL for the video thumbnail image.

        Args:
            obj (Video): The Video instance being serialized.

        Returns:
            str or None: Absolute URL string to the thumbnail, or None if no thumbnail exists.
        """
        request = self.context.get('request')
        if obj.thumbnail:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None
