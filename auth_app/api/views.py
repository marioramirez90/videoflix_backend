from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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