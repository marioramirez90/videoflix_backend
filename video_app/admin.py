from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'category')
