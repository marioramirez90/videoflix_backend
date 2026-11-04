"""Utility functions for authentication, token handling, and notification emails."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def generate_activation_params(user):
    """Generate base64-encoded user ID and a secure activation/reset token.

    Args:
        user (User): The user model instance.

    Returns:
        tuple[str, str]: (uidb64, token) tuple for verification links.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token


def build_activation_url(uidb64, token):
    """Construct the frontend account activation URL with query parameters.

    Args:
        uidb64 (str): Base64-encoded user primary key.
        token (str): Activation token string.

    Returns:
        str: Absolute URL pointing to frontend activation page.
    """
    base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500').rstrip('/')
    return f'{base_url}/pages/auth/activate.html?uid={uidb64}&token={token}'


def send_html_email(subject, text_msg, html_msg, recipient):
    """Send a multipart email with both plain text and HTML content.

    Args:
        subject (str): Email subject line.
        text_msg (str): Plain text fallback message body.
        html_msg (str): Rendered HTML email body.
        recipient (str): Destination email address.
    """
    send_mail(
        subject,
        text_msg,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        html_message=html_msg,
        fail_silently=False,
    )


def send_activation_email(user, activation_url):
    """Send an account activation email containing the confirmation link.

    Args:
        user (User): Target user receiving the activation link.
        activation_url (str): Absolute activation URL.
    """
    subject = 'Activate your Videoflix account'
    ctx = {'email': user.email, 'activation_url': activation_url}
    text_body = f'Hi {user.email},\nActivate here: {activation_url}\nVideoflix Team'
    html_body = render_to_string('emails/activation_email.html', ctx)
    send_html_email(subject, text_body, html_body, user.email)


def activate_user(uidb64, token):
    """Decode UID, verify activation token, and set user account to active.

    Args:
        uidb64 (str): Base64-encoded user ID.
        token (str): Activation token to validate.

    Returns:
        User or None: Activated user object if valid, None otherwise.
    """
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
    """Generate a JWT access and refresh token pair for a user.

    Args:
        user (User): Authenticated user instance.

    Returns:
        tuple[str, str]: (access_token_string, refresh_token_string).
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_jwt_cookies(response, access_token, refresh_token):
    """Attach JWT access and refresh tokens to response as HttpOnly cookies.

    Args:
        response (Response): Django or DRF response instance.
        access_token (str): Raw access token string.
        refresh_token (str): Raw refresh token string.

    Returns:
        Response: The response object with cookie headers appended.
    """
    cookie_kwargs = {"httponly": True, "samesite": "Lax", "secure": False}
    response.set_cookie("access_token", access_token, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)
    return response


def refresh_access_token(refresh_token_str):
    """Validate a refresh token string and generate a new access token.

    Args:
        refresh_token_str (str): Refresh token to be validated.

    Returns:
        tuple[str or None, str or None]: (new_access_token, error_message).
    """
    try:
        refresh = RefreshToken(refresh_token_str)
        return str(refresh.access_token), None
    except TokenError:
        return None, "Invalid refresh token."


def blacklist_refresh_token(refresh_token_str):
    """Add a refresh token to the blacklist so it cannot be reused.

    Args:
        refresh_token_str (str): Refresh token string to blacklist.

    Returns:
        bool: True if blacklisted successfully, False if token is invalid.
    """
    try:
        token = RefreshToken(refresh_token_str)
        token.blacklist()
        return True
    except TokenError:
        return False


def delete_jwt_cookies(response):
    """Delete access_token and refresh_token cookies from the response.

    Args:
        response (Response): Response object to remove cookies from.

    Returns:
        Response: Modified response object with cookie deletion headers.
    """
    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")
    return response


def handle_token_refresh(refresh_token):
    """Coordinate token refresh flow using cookie-provided refresh token.

    Args:
        refresh_token (str or None): Refresh token value from cookies.

    Returns:
        Response: HTTP 200 with new token and updated cookie, or HTTP 400/401 on error.
    """
    if not refresh_token:
        return Response({"detail": "Refresh token is missing."}, status=status.HTTP_400_BAD_REQUEST)
    new_access, error = refresh_access_token(refresh_token)
    if error:
        return Response({"detail": error}, status=status.HTTP_401_UNAUTHORIZED)
    response = Response({"detail": "Token refreshed", "access": new_access}, status=status.HTTP_200_OK)
    response.set_cookie("access_token", new_access, httponly=True, samesite="Lax", secure=False)
    return response


def handle_logout(refresh_token):
    """Coordinate user logout by blacklisting the refresh token and deleting cookies.

    Args:
        refresh_token (str or None): Refresh token value from cookies.

    Returns:
        Response: HTTP 200 on success, or HTTP 400 if token missing or invalid.
    """
    if not refresh_token:
        return Response({"detail": "Refresh token is missing."}, status=status.HTTP_400_BAD_REQUEST)
    if not blacklist_refresh_token(refresh_token):
        return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
    msg = "Logout successful! All tokens will be deleted. Refresh token is now invalid."
    return delete_jwt_cookies(Response({"detail": msg}, status=status.HTTP_200_OK))


def build_reset_url(uidb64, token):
    """Construct the frontend password reset confirmation URL with query parameters.

    Args:
        uidb64 (str): Base64-encoded user ID.
        token (str): Password reset token.

    Returns:
        str: Absolute URL to the password confirmation page.
    """
    base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500').rstrip('/')
    return f'{base_url}/pages/auth/confirm_password.html?uid={uidb64}&token={token}'


def send_password_reset_email(user, reset_url):
    """Send an email with a password reset link to the user.

    Args:
        user (User): The user requesting a password reset.
        reset_url (str): Absolute password reset URL.
    """
    subject = 'Reset your Videoflix password'
    ctx = {'email': user.email, 'reset_url': reset_url}
    text_body = f'Hi {user.email},\nReset your password here: {reset_url}\nVideoflix Team'
    html_body = render_to_string('emails/password_reset_email.html', ctx)
    send_html_email(subject, text_body, html_body, user.email)


def reset_user_password(uidb64, token, new_password):
    """Verify reset token and update the user's password.

    Args:
        uidb64 (str): Base64-encoded user ID.
        token (str): Password reset verification token.
        new_password (str): New plain text password to set.

    Returns:
        User or None: Updated user instance if successful, None otherwise.
    """
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
