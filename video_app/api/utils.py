import os
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response
from video_app.models import Video

ALLOWED_RESOLUTIONS = ('480p', '720p', '1080p')


def validate_video_and_resolution(movie_id, resolution):
    if resolution not in ALLOWED_RESOLUTIONS:
        return Response({'detail': 'Resolution not supported.'}, status=status.HTTP_404_NOT_FOUND)
    if not Video.objects.filter(id=movie_id).exists():
        return Response({'detail': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)
    return None


def serve_hls_playlist(movie_id, resolution):
    playlist_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, 'index.m3u8')
    if not os.path.exists(playlist_path):
        raise Http404("Manifest not found.")
    return FileResponse(open(playlist_path, 'rb'), content_type='application/vnd.apple.mpegurl')


def serve_hls_segment(movie_id, resolution, segment):
    segment_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, segment)
    if not os.path.exists(segment_path):
        raise Http404("Segment not found.")
    return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')


def get_hls_playlist_response(movie_id, resolution):
    error_response = validate_video_and_resolution(movie_id, resolution)
    if error_response:
        return error_response
    try:
        return serve_hls_playlist(movie_id, resolution)
    except Http404:
        return Response({'detail': 'Manifest not found.'}, status=status.HTTP_404_NOT_FOUND)


def get_hls_segment_response(movie_id, resolution, segment):
    error_response = validate_video_and_resolution(movie_id, resolution)
    if error_response:
        return error_response
    try:
        return serve_hls_segment(movie_id, resolution, segment)
    except Http404:
        return Response({'detail': 'Segment not found.'}, status=status.HTTP_404_NOT_FOUND)
