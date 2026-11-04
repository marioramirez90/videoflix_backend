import os
import shutil
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.api.utils import get_tokens_for_user
from video_app.models import Video

User = get_user_model()


class VideoListApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email='test@vid.com', password='pw', is_active=True)
        self.token, _ = get_tokens_for_user(self.user)
        self.client.cookies['access_token'] = self.token

    def test_video_list_unauthenticated(self):
        self.client.cookies.clear()
        res = self.client.get(reverse('video_list'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_video_list_fields_and_order(self):
        Video.objects.create(title='First', category='Drama')
        Video.objects.create(title='Second', category='Action')
        res = self.client.get(reverse('video_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['title'], 'Second')
        self.assertEqual(res.data[0]['category'], 'Action')
        self.assertEqual(res.data[1]['category'], 'Drama')

    def test_video_list_caching_and_invalidation(self):
        Video.objects.create(title='Movie 1')
        self.client.get(reverse('video_list'))
        self.assertIsNotNone(cache.get('video_list_cache'))
        Video.objects.create(title='Movie 2')
        self.assertIsNone(cache.get('video_list_cache'))


class VideoPlaylistApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='p@vid.com', password='pw', is_active=True)
        self.token, _ = get_tokens_for_user(self.user)
        self.client.cookies['access_token'] = self.token
        self.video = Video.objects.create(title='Test Movie')
        self.video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(self.video.id))

    def tearDown(self):
        if os.path.isdir(self.video_dir):
            shutil.rmtree(self.video_dir, ignore_errors=True)

    def test_playlist_unauthenticated(self):
        self.client.cookies.clear()
        url = reverse('video_playlist', kwargs={'movie_id': self.video.id, 'resolution': '720p'})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_playlist_unsupported_resolution(self):
        url = reverse('video_playlist', kwargs={'movie_id': self.video.id, 'resolution': '360p'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['detail'], 'Resolution not supported.')

    def test_playlist_video_not_found(self):
        url = reverse('video_playlist', kwargs={'movie_id': 9999, 'resolution': '720p'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['detail'], 'Video not found.')

    def test_playlist_manifest_not_found(self):
        url = reverse('video_playlist', kwargs={'movie_id': self.video.id, 'resolution': '720p'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['detail'], 'Manifest not found.')

    def test_playlist_success(self):
        path = os.path.join(self.video_dir, '1080p', 'index.m3u8')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
        url = reverse('video_playlist', kwargs={'movie_id': self.video.id, 'resolution': '1080p'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'application/vnd.apple.mpegurl')
        res.close()


class VideoSegmentApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='s@vid.com', password='pw', is_active=True)
        self.token, _ = get_tokens_for_user(self.user)
        self.client.cookies['access_token'] = self.token
        self.video = Video.objects.create(title='Test Movie')
        self.video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(self.video.id))

    def tearDown(self):
        if os.path.isdir(self.video_dir):
            shutil.rmtree(self.video_dir, ignore_errors=True)

    def test_segment_unauthenticated(self):
        self.client.cookies.clear()
        url = f"/api/video/{self.video.id}/720p/segment_000.ts"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_segment_unsupported_resolution(self):
        url = f"/api/video/{self.video.id}/360p/segment_000.ts"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_video_not_found(self):
        url = "/api/video/9999/720p/segment_000.ts"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_not_found(self):
        url = f"/api/video/{self.video.id}/720p/segment_000.ts"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['detail'], 'Segment not found.')

    def test_segment_success(self):
        seg_dir = os.path.join(self.video_dir, '1080p')
        os.makedirs(seg_dir, exist_ok=True)
        with open(os.path.join(seg_dir, 'segment_000.ts'), 'wb') as f:
            f.write(b'\x00' * 10)
        res_no_slash = self.client.get(f"/api/video/{self.video.id}/1080p/segment_000.ts")
        res_with_slash = self.client.get(f"/api/video/{self.video.id}/1080p/segment_000.ts/")
        self.assertEqual(res_no_slash.status_code, status.HTTP_200_OK)
        self.assertEqual(res_with_slash.status_code, status.HTTP_200_OK)
        self.assertEqual(res_no_slash['Content-Type'], 'video/MP2T')
        res_no_slash.close()
        res_with_slash.close()
