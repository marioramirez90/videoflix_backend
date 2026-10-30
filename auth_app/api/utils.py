from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def generate_activation_params(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token


def build_activation_url(uidb64, token):
    base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500')
    return f'{base_url}/activate/{uidb64}/{token}/'


def send_activation_email(user, activation_url):
    subject = 'Activate your Videoflix account'
    message = (
        f'Hi {user.email},\n\n'
        f'Please click the link below to activate your account:\n'
        f'{activation_url}\n\n'
        'Your Videoflix Team'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )