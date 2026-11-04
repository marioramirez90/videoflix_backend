"""Signal receivers for video cache invalidation, task enqueueing, and file cleanup."""

import os
import shutil
import django_rq
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from .models import Video
from .tasks import convert_video_to_all_hls


def invalidate_video_cache(sender, instance, **kwargs):
    """Invalidate the cached list of videos when a Video instance is saved or deleted.

    Args:
        sender (class): The model class sending the signal.
        instance (Video): The instance that triggered the signal.
        **kwargs: Additional keyword arguments from the signal.
    """
    cache.delete('video_list_cache')


def enqueue_video_conversion(sender, instance, created, **kwargs):
    """Enqueue background HLS transcoding and thumbnail generation upon video creation.

    Args:
        sender (class): The model class sending the signal.
        instance (Video): The created video instance.
        created (bool): True if a new record was inserted into the database.
        **kwargs: Additional keyword arguments from the signal.
    """
    if created and instance.video_file:
        print(f"[BACKEND] Video uploaded: {instance.title} (ID: {instance.id}) -> Queue")
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(convert_video_to_all_hls, instance.video_file.path, instance.id)


def delete_video_files(sender, instance, **kwargs):
    """Remove the original video file and all generated HLS transcode directories on deletion.

    Args:
        sender (class): The model class sending the signal.
        instance (Video): The deleted video instance.
        **kwargs: Additional keyword arguments from the signal.
    """
    if instance.video_file and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)
        print(f"Original file deleted: {instance.video_file.path}")

    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(instance.id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir)
        print(f"HLS directory deleted: {video_dir}")


post_save.connect(invalidate_video_cache, sender=Video)
post_delete.connect(invalidate_video_cache, sender=Video)
post_save.connect(enqueue_video_conversion, sender=Video)
post_delete.connect(delete_video_files, sender=Video)
