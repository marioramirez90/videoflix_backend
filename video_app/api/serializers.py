from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('id', 'created_at', 'title', 'description', 'thumbnail_url', 'category')

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None
