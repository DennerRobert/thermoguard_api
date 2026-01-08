"""Rooms URL configuration for device settings."""
from django.urls import path

from apps.devices.views import RoomSettingsView

app_name = 'rooms'

urlpatterns = [
    path(
        '<uuid:room_id>/settings/',
        RoomSettingsView.as_view(),
        name='room-settings'
    ),
]


