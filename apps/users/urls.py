"""Users URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    RefreshTokenView,
    UserViewSet,
)

app_name = 'users'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Current user
    path('me/', CurrentUserView.as_view(), name='me'),
    path('me/password/', PasswordChangeView.as_view(), name='password-change'),
    
    # User management
    path('', include(router.urls)),
]


