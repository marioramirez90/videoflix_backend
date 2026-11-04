"""Database models for video metadata and asset storage."""

from django.db import models


class Video(models.Model):
    """Model representing an uploaded video asset and its streaming metadata.

    Attributes:
        title (str): Display title of the video.
        description (str, optional): Synopsis or detailed summary.
        video_file (FileField): Uploaded source video file.
        thumbnail (ImageField, optional): Extracted or uploaded preview thumbnail.
        category (str): Content genre or category classification.
        created_at (DateTimeField): Timestamp when the video record was created.
    """

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    category = models.CharField(max_length=50, default='General', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the string representation of the video instance.

        Returns:
            str: Video title.
        """
        return self.title
