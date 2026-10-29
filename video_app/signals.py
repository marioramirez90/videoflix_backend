import os
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Video
from .tasks import convert720p  


def create_lecture(sender, instance, created, **kwargs):
    if created and instance.video_file:
        print(f"New object created: {instance.title}")

        convert720p(instance.video_file.path)


def delete_video_file(sender, instance, **kwargs):
    if instance.video_file:

        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
            print(f"Datei gelöscht: {instance.video_file.path}")


        base_name, _ = os.path.splitext(instance.video_file.path)
        file_720p = f"{base_name}_720p.mp4"
        if os.path.isfile(file_720p):
            os.remove(file_720p)
            print(f"720p-Datei gelöscht: {file_720p}")


post_save.connect(create_lecture, sender=Video)
post_delete.connect(delete_video_file, sender=Video)