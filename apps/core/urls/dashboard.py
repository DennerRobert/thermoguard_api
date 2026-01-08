"""Dashboard URL configuration."""
from django.urls import path

from apps.core.views import DashboardView, RoomDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='main'),
    path('rooms/<uuid:room_id>/', RoomDashboardView.as_view(), name='room'),
]


