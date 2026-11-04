"""Serializers for authentication endpoints."""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration requests.

    Accepts email and password, validating password confirmation and unique email.
    Creates an inactive user requiring email activation.
    """

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
        """Validate that the email address is not already registered.

        Args:
            value (str): Email to validate.

        Raises:
            serializers.ValidationError: If the email already exists.

        Returns:
            str: Lowercased email address.
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Please check your input and try again.")
        return value.lower()

    def validate(self, attrs):
        """Validate that the password and confirmation password match.

        Supports both `confirmed_password` and `confirm_password` field names.

        Args:
            attrs (dict): Serializer input data.

        Raises:
            serializers.ValidationError: If passwords do not match or confirmation is missing.

        Returns:
            dict: Validated attribute dictionary with canonical confirmed_password set.
        """
        confirm = attrs.get('confirmed_password') or attrs.get('confirm_password')
        if not confirm or attrs.get('password') != confirm:
            raise serializers.ValidationError("Please check your input and try again.")
        attrs['confirmed_password'] = confirm
        return attrs

    def create(self, validated_data):
        """Create and return a new inactive User instance.

        Args:
            validated_data (dict): Validated data from the serializer.

        Returns:
            User: Newly created inactive User object.
        """
        validated_data.pop('confirmed_password', None)
        validated_data.pop('confirm_password', None)
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )


class LoginSerializer(serializers.Serializer):
    """Serializer for authenticating users via email and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate credentials, checking user activation and authenticating user.

        Args:
            attrs (dict): Serializer input dictionary containing email and password.

        Raises:
            serializers.ValidationError: If the account is inactive or credentials are invalid.

        Returns:
            dict: Attributes containing authenticated user object.
        """
        email = attrs.get("email", "").lower()
        password = attrs.get("password")
        user = User.objects.filter(email__iexact=email).first()
        if user and user.check_password(password) and not user.is_active:
            raise serializers.ValidationError("Account is not activated yet.")
        auth_user = authenticate(username=email, password=password)
        if not auth_user:
            raise serializers.ValidationError("Please check your input and try again.")
        attrs["user"] = auth_user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for initiating a password reset request."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Serializer for setting a new password via reset token confirmation."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate that new password and password confirmation match.

        Args:
            attrs (dict): Serializer input attributes.

        Raises:
            serializers.ValidationError: If the two passwords do not match.

        Returns:
            dict: Validated attributes.
        """
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return attrs
