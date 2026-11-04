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
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
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
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token, *args, **kwargs):
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
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
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
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        return handle_token_refresh(request.COOKIES.get("refresh_token"))


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        return handle_logout(request.COOKIES.get("refresh_token"))


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
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
    serializer_class = PasswordConfirmSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, uidb64, token, *args, **kwargs):
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
