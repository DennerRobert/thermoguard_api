"""
WebSocket URL routing for ThermoGuard IoT API.

This module defines WebSocket routes for real-time communication,
including dashboard updates and room-specific notifications.
"""
from django.urls import path, re_path

from apps.core.consumers import DashboardConsumer, RoomConsumer

websocket_urlpatterns = [
    path('ws/dashboard/', DashboardConsumer.as_asgi(), name='ws_dashboard'),
    re_path(
        r'ws/room/(?P<room_id>[0-9a-f-]+)/$',
        RoomConsumer.as_asgi(),
        name='ws_room'
    ),
]


