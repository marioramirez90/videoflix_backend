"""Database models for authentication and user management."""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    """Custom manager for the User model with email-based authentication."""

    def create_user(self, email, username=None, password=None, **extra_fields):
        """Create and return a regular user with an email and password.

        Args:
            email (str): User email address.
            username (str, optional): User display name or handle. Defaults to local-part of email.
            password (str, optional): Raw user password.
            **extra_fields: Additional fields passed to the model.

        Raises:
            ValueError: If the email address is not provided.

        Returns:
            User: Newly created user instance.
        """
        if not email:
            raise ValueError("The email address must be provided.")
        email = self.normalize_email(email)
        if not username:
            username = email.split('@')[0]
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """Create and return a superuser with staff and superuser permissions.

        Args:
            email (str): Superuser email address.
            username (str, optional): Superuser username. Defaults to email prefix or 'admin'.
            password (str, optional): Raw superuser password.
            **extra_fields: Additional fields passed to the model.

        Returns:
            User: Newly created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not username:
            username = email.split('@')[0] if email else 'admin'

        return self.create_user(email, username=username, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model representing registered system accounts.

    Uses email as the unique identifier for authentication instead of usernames.
    """

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """Return the string representation of the user, which is their email address.

        Returns:
            str: User's email.
        """
        return self.email
