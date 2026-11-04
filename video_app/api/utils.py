"""Utility functions for validating, resolving, and serving HLS playlists and video segments."""

import os
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response
from video_app.models import Video

ALLOWED_RESOLUTIONS = ('480p', '720p', '1080p')


def validate_video_and_resolution(movie_id, resolution):
    """Check if the requested resolution is permitted and the video exists in the database.

    Args:
        movie_id (int): Primary key of the video asset.
        resolution (str): Video stream resolution (e.g. '480p', '720p', '1080p').

    Returns:
        Response or None: HTTP 404 Response if invalid or missing, or None if valid.
    """
    if resolution not in ALLOWED_RESOLUTIONS:
        return Response({'detail': 'Resolution not supported.'}, status=status.HTTP_404_NOT_FOUND)
    if not Video.objects.filter(id=movie_id).exists():
        return Response({'detail': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)
    return None


def serve_hls_playlist(movie_id, resolution):
    """Retrieve and stream the HLS .m3u8 playlist file from the storage directory.

    Args:
        movie_id (int): Primary key of the video.
        resolution (str): Selected stream resolution.

    Raises:
        Http404: If the playlist file does not exist on disk.

    Returns:
        FileResponse: Streaming file response with MPEG-URL content type.
    """
    playlist_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, 'index.m3u8')
    if not os.path.exists(playlist_path):
        raise Http404("Manifest not found.")
    return FileResponse(open(playlist_path, 'rb'), content_type='application/vnd.apple.mpegurl')


def serve_hls_segment(movie_id, resolution, segment):
    """Retrieve and stream a binary MPEG-TS segment file.

    Args:
        movie_id (int): Primary key of the video.
        resolution (str): Selected stream resolution.
        segment (str): Filename of the target transport stream segment.

    Raises:
        Http404: If the segment chunk does not exist on disk.

    Returns:
        FileResponse: Binary file response with video/MP2T content type.
    """
    segment_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, segment)
    if not os.path.exists(segment_path):
        raise Http404("Segment not found.")
    return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')


def get_hls_playlist_response(movie_id, resolution):
    """Handle playlist request, returning either the playlist file or a 404 response.

    Args:
        movie_id (int): Primary key of the target video.
        resolution (str): Target stream resolution.

    Returns:
        Response or FileResponse: FileResponse on success, or HTTP 404 Response on failure.
    """
    error_response = validate_video_and_resolution(movie_id, resolution)
    if error_response:
        return error_response
    try:
        return serve_hls_playlist(movie_id, resolution)
    except Http404:
        return Response({'detail': 'Manifest not found.'}, status=status.HTTP_404_NOT_FOUND)


def get_hls_segment_response(movie_id, resolution, segment):
    """Handle segment request, returning either the binary chunk or a 404 response.

    Args:
        movie_id (int): Primary key of the target video.
        resolution (str): Target stream resolution.
        segment (str): Filename of the requested transport stream chunk.

    Returns:
        Response or FileResponse: Binary FileResponse on success, or HTTP 404 Response on failure.
    """
    error_response = validate_video_and_resolution(movie_id, resolution)
    if error_response:
        return error_response
    try:
        return serve_hls_segment(movie_id, resolution, segment)
    except Http404:
        return Response({'detail': 'Segment not found.'}, status=status.HTTP_404_NOT_FOUND)
