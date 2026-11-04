"""Admin configuration for the auth_app module."""

from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for custom User model.
    
    Provides display and search capabilities for user accounts in the Django admin interface.
    """
    list_display = ('id', 'email', 'username', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'username')
