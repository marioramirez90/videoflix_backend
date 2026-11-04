"""URL configuration for authentication endpoints."""

from django.urls import path
from .views import (
    ActivateView,
    LoginView,
    LogoutView,
    PasswordConfirmView,
    PasswordResetView,
    RegisterView,
    TokenRefreshCookieView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_confirm'),
]
