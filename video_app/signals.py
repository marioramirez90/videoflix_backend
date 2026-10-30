import os
import django_rq
from django.db.models.signals import post_delete, post_save
from .models import Video
from .tasks import convert720p


def create_lecture(sender, instance, created, **kwargs):
    if created and instance.video_file:
        print(f"Übergebe an Redis-Queue: {instance.title}")
        # Task in die Redis-Queue 'default' einreihen
        queue = django_rq.get_queue('default')
        queue.enqueue(convert720p, instance.video_file.path)


def delete_video_file(sender, instance, **kwargs):
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
            print(f"Original gelöscht: {instance.video_file.path}")

        base_name, _ = os.path.splitext(instance.video_file.path)
        file_720p = f"{base_name}_720p.mp4"
        if os.path.isfile(file_720p):
            os.remove(file_720p)
            print(f"720p-Datei gelöscht: {file_720p}")


post_save.connect(create_lecture, sender=Video)
post_delete.connect(delete_video_file, sender=Video)