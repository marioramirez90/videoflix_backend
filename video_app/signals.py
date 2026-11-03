import os
import shutil
import django_rq
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from .models import Video
from .tasks import convert_video_to_all_hls


def enqueue_video_conversion(sender, instance, created, **kwargs):
    if created and instance.video_file:
        print(f"[BACKEND] Video hochgeladen: {instance.title} (ID: {instance.id}) -> Queue")
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(convert_video_to_all_hls, instance.video_file.path, instance.id)


def delete_video_files(sender, instance, **kwargs):
    """Löscht Originaldatei und alle erzeugten HLS-Auflösungen."""
    if instance.video_file and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)
        print(f"Originaldatei gelöscht: {instance.video_file.path}")

    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(instance.id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir)
        print(f"HLS-Verzeichnis gelöscht: {video_dir}")


post_save.connect(enqueue_video_conversion, sender=Video)
post_delete.connect(delete_video_files, sender=Video)
