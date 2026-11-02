from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework.views import APIView
from .utils import activate_user

from .serializers import RegisterSerializer
from .utils import (
    build_activation_url,
    generate_activation_params,
    send_activation_email,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

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