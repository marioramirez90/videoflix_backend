"""Admin interface configuration for the video_app module."""

from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video instances in the Django admin interface."""

    list_display = ('id', 'title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'category')
