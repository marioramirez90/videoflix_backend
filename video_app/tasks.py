import os
import subprocess
from django.conf import settings

RESOLUTIONS = {
    '480p': {'scale': '854:480', 'bitrate': '800k'},
    '720p': {'scale': '1280:720', 'bitrate': '2500k'},
    '1080p': {'scale': '1920:1080', 'bitrate': '5000k'},
}


def run_ffmpeg_thumbnail(source_path, target_path):
    cmd = ['ffmpeg', '-y', '-ss', '00:00:01', '-i', source_path, '-vframes', '1', '-q:v', '2', target_path]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def extract_video_thumbnail(source_path, movie_id):
    from video_app.models import Video
    video = Video.objects.filter(id=movie_id).first()
    if not video or video.thumbnail:
        return
    thumb_rel = f'thumbnails/thumb_{movie_id}.jpg'
    thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_rel)
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    if run_ffmpeg_thumbnail(source_path, thumb_path) and os.path.exists(thumb_path):
        video.thumbnail = thumb_rel
        video.save(update_fields=['thumbnail'])


def build_hls_command(source_path, playlist_file, segment_pattern, config):
    return [
        'ffmpeg', '-y', '-i', source_path,
        '-vf', f"scale={config['scale']}",
        '-c:v', 'libx264', '-b:v', config['bitrate'],
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', segment_pattern,
        playlist_file,
    ]


def execute_ffmpeg_conversion(cmd, movie_id, resolution):
    print(f"[WORKER] Starte HLS-Konvertierung für Video {movie_id} ({resolution})...")
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode != 0:
        print(f"[WORKER ERROR] {run.stderr}")
    return run.returncode


def convert_resolution_to_hls(source_path, movie_id, resolution, config):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution)
    os.makedirs(output_dir, exist_ok=True)
    playlist = os.path.join(output_dir, 'index.m3u8')
    segments = os.path.join(output_dir, 'segment_%03d.ts')
    cmd = build_hls_command(source_path, playlist, segments, config)
    return execute_ffmpeg_conversion(cmd, movie_id, resolution)


def convert_video_to_all_hls(source_path, movie_id):
    """Extrahiert Thumbnail und konvertiert das Video in 480p, 720p und 1080p HLS."""
    extract_video_thumbnail(source_path, movie_id)
    for resolution, config in RESOLUTIONS.items():
        convert_resolution_to_hls(source_path, movie_id, resolution, config)
