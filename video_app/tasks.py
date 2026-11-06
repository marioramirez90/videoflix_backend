"""Asynchronous background tasks for FFmpeg video processing and HLS transcoding."""

import os
import subprocess
from django.conf import settings

RESOLUTIONS = {
    '480p': {'scale': '854:480', 'bitrate': '800k'},
    '720p': {'scale': '1280:720', 'bitrate': '2500k'},
    '1080p': {'scale': '1920:1080', 'bitrate': '5000k'},
}


def run_ffmpeg_thumbnail(source_path, target_path):
    """Execute FFmpeg command to capture a single frame thumbnail at the 1-second mark.

    Args:
        source_path (str): Filesystem path to the input video.
        target_path (str): Destination path for the extracted JPEG image.

    Returns:
        bool: True if the process completed with return code 0, False otherwise.
    """
    cmd = ['ffmpeg', '-y', '-ss', '00:00:01', '-i', source_path, '-vframes', '1', '-q:v', '2', target_path]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def extract_video_thumbnail(source_path, movie_id):
    """Generate and attach a thumbnail image to the Video model instance if absent.

    Args:
        source_path (str): Absolute filesystem path to the uploaded video file.
        movie_id (int): Primary key of the Video database record.
    """
    from video_app.models import Video
    video = Video.objects.filter(id=movie_id).first()
    if not video:
        return
    thumb_rel = f'thumbnails/thumb_{movie_id}.jpg'
    thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_rel)
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    if not os.path.exists(thumb_path):
        run_ffmpeg_thumbnail(source_path, thumb_path)
    if not video.thumbnail and os.path.exists(thumb_path):
        video.thumbnail = thumb_rel
        video.save(update_fields=['thumbnail'])


def build_hls_command(source_path, playlist_file, segment_pattern, config):
    """Build the FFmpeg command argument list for converting a video into HLS chunks.

    Args:
        source_path (str): Path to the source video file.
        playlist_file (str): Target path for the output `.m3u8` playlist.
        segment_pattern (str): Filename format pattern for `.ts` video chunks.
        config (dict): Target resolution profile containing 'scale' and 'bitrate'.

    Returns:
        list[str]: Complete list of command line arguments for subprocess execution.
    """
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
    """Run the FFmpeg transcoding process and log worker output and errors.

    Args:
        cmd (list[str]): Command arguments to pass to the FFmpeg process.
        movie_id (int): Primary key of the video being converted.
        resolution (str): Target resolution label (e.g., '720p').

    Returns:
        int: Process exit code (0 for success).
    """
    print(f"[WORKER] Starting HLS conversion for video {movie_id} ({resolution})...")
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode != 0:
        print(f"[WORKER ERROR] {run.stderr}")
    return run.returncode


def convert_resolution_to_hls(source_path, movie_id, resolution, config):
    """Convert an input video into an HLS stream for a specific resolution profile.

    Args:
        source_path (str): Filesystem path to source video file.
        movie_id (int): ID of the video record.
        resolution (str): Target resolution string ('480p', '720p', or '1080p').
        config (dict): Scale and bitrate dictionary.

    Returns:
        int: Subprocess exit code.
    """
    output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution)
    os.makedirs(output_dir, exist_ok=True)
    playlist = os.path.join(output_dir, 'index.m3u8')
    segments = os.path.join(output_dir, 'segment_%03d.ts')
    cmd = build_hls_command(source_path, playlist, segments, config)
    return execute_ffmpeg_conversion(cmd, movie_id, resolution)


def convert_video_to_all_hls(source_path, movie_id):
    """Extract preview thumbnail and transcode video into 480p, 720p, and 1080p HLS profiles.

    Args:
        source_path (str): Filepath of the source video.
        movie_id (int): ID of the target Video model instance.
    """
    extract_video_thumbnail(source_path, movie_id)
    for resolution, config in RESOLUTIONS.items():
        convert_resolution_to_hls(source_path, movie_id, resolution, config)
