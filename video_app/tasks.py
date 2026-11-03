import os
import shutil
import subprocess
from django.conf import settings

RESOLUTIONS = {
    '480p': {'scale': '854:480', 'bitrate': '800k'},
    '720p': {'scale': '1280:720', 'bitrate': '2500k'},
    '1080p': {'scale': '1920:1080', 'bitrate': '5000k'},
}


def convert_resolution_to_hls(source_path, movie_id, resolution, config):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution)
    os.makedirs(output_dir, exist_ok=True)

    playlist_file = os.path.join(output_dir, 'index.m3u8')
    segment_pattern = os.path.join(output_dir, 'segment_%03d.ts')

    cmd = [
        'ffmpeg', '-y', '-i', source_path,
        '-vf', f"scale={config['scale']}",
        '-c:v', 'libx264', '-b:v', config['bitrate'],
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', segment_pattern,
        playlist_file
    ]

    print(f"[WORKER] Starte HLS-Konvertierung für Video {movie_id} ({resolution})...")
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode != 0:
        print(f"[WORKER ERROR] {run.stderr}")
    else:
        print(f"[WORKER] Fertig: {playlist_file}")
    return run.returncode


def convert_video_to_all_hls(source_path, movie_id):
    """Konvertiert das Video nacheinander in 480p, 720p und 1080p HLS."""
    for resolution, config in RESOLUTIONS.items():
        convert_resolution_to_hls(source_path, movie_id, resolution, config)