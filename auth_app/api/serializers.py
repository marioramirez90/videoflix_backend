from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'confirmed_password', 'confirm_password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'validators': []},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bitte überprüfe deine Eingaben und versuche es erneut.")
        return value.lower()

    def validate(self, attrs):
        confirm = attrs.get('confirmed_password') or attrs.get('confirm_password')
        if not confirm or attrs.get('password') != confirm:
            raise serializers.ValidationError("Bitte überprüfe deine Eingaben und versuche es erneut.")
        attrs['confirmed_password'] = confirm
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirmed_password', None)
        validated_data.pop('confirm_password', None)
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("email"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("Bitte überprüfe deine Eingaben und versuche es erneut.")
        if not user.is_active:
            raise serializers.ValidationError("Account ist noch nicht aktiviert.")
        attrs["user"] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return attrs
