from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.api.utils import generate_activation_params, get_tokens_for_user

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_success(self):
        payload = {'email': 'new@test.com', 'password': 'pass123', 'confirm_password': 'pass123'}
        res = self.client.post(reverse('register'), payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='new@test.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_duplicate_email(self):
        User.objects.create_user(email='existing@test.com', password='old')
        payload = {'email': 'existing@test.com', 'password': 'pass123', 'confirm_password': 'pass123'}
        res = self.client.post(reverse('register'), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Bitte überprüfe deine Eingaben', str(res.data))

    def test_register_password_mismatch(self):
        payload = {'email': 'mismatch@test.com', 'password': 'pass123', 'confirm_password': 'pass456'}
        res = self.client.post(reverse('register'), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ActivationTests(APITestCase):
    def test_activate_success(self):
        user = User.objects.create_user(email='act@test.com', password='pw')
        uidb64, token = generate_activation_params(user)
        res = self.client.get(reverse('activate', kwargs={'uidb64': uidb64, 'token': token}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_invalid_token(self):
        res = self.client.get(reverse('activate', kwargs={'uidb64': 'invalid', 'token': 'bad'}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def test_login_success(self):
        User.objects.create_user(email='user@test.com', password='pw123', is_active=True)
        res = self.client.post(reverse('login'), {'email': 'user@test.com', 'password': 'pw123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', res.cookies)
        self.assertIn('refresh_token', res.cookies)

    def test_login_inactive_user(self):
        User.objects.create_user(email='inactive@test.com', password='pw123', is_active=False)
        res = self.client.post(reverse('login'), {'email': 'inactive@test.com', 'password': 'pw123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Account ist noch nicht aktiviert', str(res.data))

    def test_login_wrong_password(self):
        User.objects.create_user(email='active@test.com', password='pw123', is_active=True)
        res = self.client.post(reverse('login'), {'email': 'active@test.com', 'password': 'wrong'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Bitte überprüfe deine Eingaben', str(res.data))


class TokenRefreshAndLogoutTests(APITestCase):
    def test_token_refresh_success(self):
        user = User.objects.create_user(email='ref@test.com', password='pw', is_active=True)
        _, refresh_token = get_tokens_for_user(user)
        self.client.cookies['refresh_token'] = refresh_token
        res = self.client.post(reverse('token_refresh'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('access_token', res.cookies)

    def test_token_refresh_missing_cookie(self):
        res = self.client.post(reverse('token_refresh'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        user = User.objects.create_user(email='logout@test.com', password='pw', is_active=True)
        _, refresh_token = get_tokens_for_user(user)
        self.client.cookies['refresh_token'] = refresh_token
        res = self.client.post(reverse('logout'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_missing_cookie(self):
        res = self.client.post(reverse('logout'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTests(APITestCase):
    def test_password_reset_request(self):
        User.objects.create_user(email='reset@test.com', password='old', is_active=True)
        res = self.client.post(reverse('password_reset'), {'email': 'reset@test.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_confirm_success(self):
        user = User.objects.create_user(email='conf@test.com', password='old', is_active=True)
        uidb64, token = generate_activation_params(user)
        url = reverse('password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        payload = {'new_password': 'newpw', 'confirm_password': 'newpw'}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpw'))

    def test_password_confirm_mismatch(self):
        user = User.objects.create_user(email='mismatch@test.com', password='old', is_active=True)
        uidb64, token = generate_activation_params(user)
        url = reverse('password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        payload = {'new_password': 'newpw', 'confirm_password': 'other'}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
