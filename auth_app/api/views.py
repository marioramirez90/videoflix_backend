"""API views for user registration, authentication, token refresh, and password management."""

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
)
from .utils import (
    activate_user,
    build_activation_url,
    build_reset_url,
    generate_activation_params,
    get_tokens_for_user,
    handle_logout,
    handle_token_refresh,
    reset_user_password,
    send_activation_email,
    send_password_reset_email,
    set_jwt_cookies,
)


class RegisterView(generics.CreateAPIView):
    """View to handle new user registration and dispatch activation email."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        """Validate registration data, create inactive user, and send activation email.

        Args:
            request (Request): The incoming registration request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 201 with created user details and demonstration token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        uidb64, token = generate_activation_params(user)
        send_activation_email(user, build_activation_url(uidb64, token))
        return Response(
            {'user': {'id': user.id, 'email': user.email}, 'token': token},
            status=status.HTTP_201_CREATED,
        )


class ActivateView(APIView):
    """View to activate an inactive user account using uidb64 and token parameters."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token, *args, **kwargs):
        """Activate the user account matching the provided token and uidb64.

        Args:
            request (Request): The incoming activation request.
            uidb64 (str): Base64-encoded user identifier.
            token (str): Activation token string.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 on success or HTTP 400 if activation fails.
        """
        user = activate_user(uidb64, token)
        if user:
            return Response(
                {"message": "Account successfully activated."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Activation failed."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(generics.GenericAPIView):
    """View to authenticate credentials and issue access/refresh tokens in HttpOnly cookies."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Authenticate user credentials and attach JWT cookies to the response.

        Args:
            request (Request): The incoming login request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 with user details and cookies attached.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access_token, refresh_token = get_tokens_for_user(user)
        response = Response(
            {
                "detail": "Login successful",
                "user": {"id": user.id, "username": user.email},
            },
            status=status.HTTP_200_OK,
        )
        return set_jwt_cookies(response, access_token, refresh_token)


class TokenRefreshCookieView(APIView):
    """View to refresh expired access tokens using the refresh_token cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Extract refresh token from cookies and return a renewed access token.

        Args:
            request (Request): The incoming request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 with updated token and cookie, or HTTP 400/401 on error.
        """
        return handle_token_refresh(request.COOKIES.get("refresh_token"))


class LogoutView(APIView):
    """View to log out the user by blacklisting refresh token and clearing cookies."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Invalidate the refresh token and clear JWT cookies.

        Args:
            request (Request): The incoming logout request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 with deletion cookies or HTTP 400 if token missing.
        """
        return handle_logout(request.COOKIES.get("refresh_token"))


class PasswordResetView(generics.GenericAPIView):
    """View to request a password reset email."""

    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Accept email, generate reset token if user exists, and send reset email.

        Args:
            request (Request): The incoming request with email.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 confirming email dispatch.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user:
            uidb64, token = generate_activation_params(user)
            send_password_reset_email(user, build_reset_url(uidb64, token))
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordConfirmView(generics.GenericAPIView):
    """View to confirm password reset and set new credentials."""

    serializer_class = PasswordConfirmSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, uidb64, token, *args, **kwargs):
        """Validate new password and apply changes to user account.

        Args:
            request (Request): The incoming confirmation request.
            uidb64 (str): Base64-encoded user identifier.
            token (str): Password reset verification token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP 200 on success or HTTP 400 on invalid token/data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']
        user = reset_user_password(uidb64, token, new_password)
        if user:
            return Response(
                {"detail": "Your Password has been successfully reset."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Password reset failed."},
            status=status.HTTP_400_BAD_REQUEST,
        )
