"""Package-level view exports for auth_app.

Re-exports the API views for convenient access from the app root.
"""

from auth_app.api.views import (
    ActivateView,
    LoginView,
    LogoutView,
    PasswordConfirmView,
    PasswordResetView,
    RegisterView,
    TokenRefreshCookieView,
)

__all__ = [
    'RegisterView',
    'ActivateView',
    'LoginView',
    'TokenRefreshCookieView',
    'LogoutView',
    'PasswordResetView',
    'PasswordConfirmView',
]
