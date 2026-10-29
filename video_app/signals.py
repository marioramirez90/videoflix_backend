import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video


def create_lecture(sender, instance, created, **kwargs):
    if created:
        print(f"New object created: {instance.title}")


def delete_video_file(sender, instance, **kwargs):
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
            print(f"Datei gelöscht: {instance.video_file.path}")


post_save.connect(create_lecture, sender=Video)
post_delete.connect(delete_video_file, sender=Video)