from django.urls import path
from .views import (
    ActivateView,
    LoginView,
    LogoutView,
    RegisterView,
    TokenRefreshCookieView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
]