"""Admin interface configuration for the video_app module."""

import os
from django.conf import settings
from django.contrib import admin
from .models import Video
from .tasks import run_ffmpeg_thumbnail


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video instances in the Django admin interface."""

    list_display = ('id', 'title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'category')

    def save_model(self, request, obj, form, change):
        """Save video model and ensure thumbnail fallback when cleared or absent."""
        super().save_model(request, obj, form, change)
        if not obj.thumbnail and obj.video_file:
            thumb_rel = f'thumbnails/thumb_{obj.id}.jpg'
            thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_rel)
            if os.path.isfile(thumb_path):
                Video.objects.filter(id=obj.id).update(thumbnail=thumb_rel)
                obj.thumbnail.name = thumb_rel
            else:
                try:
                    if hasattr(obj.video_file, 'path') and os.path.isfile(obj.video_file.path):
                        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                        if run_ffmpeg_thumbnail(obj.video_file.path, thumb_path) and os.path.isfile(thumb_path):
                            Video.objects.filter(id=obj.id).update(thumbnail=thumb_rel)
                            obj.thumbnail.name = thumb_rel
                except (ValueError, FileNotFoundError):
                    pass
