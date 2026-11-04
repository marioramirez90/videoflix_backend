"""Custom authentication classes for JWT-based cookie and header authentication."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that inspects HttpOnly cookies and standard headers.

    Checks the 'access_token' cookie first. If not present or empty, falls back to the
    standard 'Authorization: Bearer <token>' header.
    """

    def authenticate(self, request):
        """Authenticate the request using cookies or fallback to standard header authentication.

        Args:
            request (Request): The incoming DRF request object.

        Returns:
            tuple (User, Token) or None: Returns authenticated user and validated token,
            or None if no credentials provided or token is invalid.
        """
        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return super().authenticate(request)
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            return None
