from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def generate_activation_params(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token


def build_activation_url(uidb64, token):
    base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500')
    return f'{base_url}/activate/{uidb64}/{token}/'


def send_html_email(subject, text_msg, html_msg, recipient):
    send_mail(
        subject,
        text_msg,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        html_message=html_msg,
        fail_silently=False,
    )


def send_activation_email(user, activation_url):
    subject = 'Activate your Videoflix account'
    ctx = {'email': user.email, 'activation_url': activation_url}
    text_body = f'Hi {user.email},\nActivate here: {activation_url}\nVideoflix Team'
    html_body = render_to_string('emails/activation_email.html', ctx)
    send_html_email(subject, text_body, html_body, user.email)


def activate_user(uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return user
    return None


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_jwt_cookies(response, access_token, refresh_token):
    cookie_kwargs = {"httponly": True, "samesite": "Lax", "secure": False}
    response.set_cookie("access_token", access_token, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)
    return response


def refresh_access_token(refresh_token_str):
    try:
        refresh = RefreshToken(refresh_token_str)
        return str(refresh.access_token), None
    except TokenError:
        return None, "Ungültiger Refresh-Token."


def blacklist_refresh_token(refresh_token_str):
    try:
        token = RefreshToken(refresh_token_str)
        token.blacklist()
        return True
    except TokenError:
        return False


def delete_jwt_cookies(response):
    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")
    return response


def build_reset_url(uidb64, token):
    base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500')
    return f'{base_url}/password-reset/{uidb64}/{token}/'


def send_password_reset_email(user, reset_url):
    subject = 'Reset your Videoflix password'
    ctx = {'email': user.email, 'reset_url': reset_url}
    text_body = f'Hi {user.email},\nReset your password here: {reset_url}\nVideoflix Team'
    html_body = render_to_string('emails/password_reset_email.html', ctx)
    send_html_email(subject, text_body, html_body, user.email)


def reset_user_password(uidb64, token, new_password):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if default_token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()
        return user
    return None
