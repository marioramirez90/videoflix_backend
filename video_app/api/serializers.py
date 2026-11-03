from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('id', 'created_at', 'title', 'description', 'thumbnail_url', 'category')

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        for attr in ('thumbnail', 'thumbnail_url', 'cover_image'):
            img = getattr(obj, attr, None)
            if img:
                url = img.url if hasattr(img, 'url') else str(img)
                return request.build_absolute_uri(url) if request else url
        return None

    def get_category(self, obj):
        return getattr(obj, 'category', getattr(obj, 'genre', 'General'))