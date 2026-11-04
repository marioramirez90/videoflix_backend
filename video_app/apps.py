"""Application configuration for video_app."""

from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Configuration class for video_app, initializing signal handlers upon startup."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """Import signal handlers once the application registry is fully populated."""
        import video_app.signals
