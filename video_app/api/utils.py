import os
from django.conf import settings
from django.http import FileResponse, Http404


def serve_hls_playlist(movie_id, resolution):
    playlist_path = os.path.join(
        settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, 'index.m3u8'
    )
    if not os.path.exists(playlist_path):
        raise Http404("Manifest not found.")
    return FileResponse(open(playlist_path, 'rb'), content_type='application/vnd.apple.mpegurl')

def serve_hls_segment(movie_id, resolution, segment):
    segment_path = os.path.join(
        settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, segment
    )
    if not os.path.exists(segment_path):
        raise Http404("Segment not found.")
    return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')