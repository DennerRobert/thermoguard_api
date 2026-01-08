"""
WebSocket consumers for ThermoGuard IoT API.

This module provides real-time communication via WebSockets.
"""
import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('thermoguard')


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for main dashboard updates.
    
    Broadcasts sensor readings, AC status changes, and alerts
    to all connected dashboard clients.
    """
    
    DASHBOARD_GROUP = 'dashboard'

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        # Join dashboard group
        await self.channel_layer.group_add(
            self.DASHBOARD_GROUP,
            self.channel_name
        )
        await self.accept()
        
        logger.info(f"Dashboard WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code: int) -> None:
        """
        Handle WebSocket disconnection.
        
        Args:
            close_code: The WebSocket close code.
        """
        # Leave dashboard group
        await self.channel_layer.group_discard(
            self.DASHBOARD_GROUP,
            self.channel_name
        )
        
        logger.info(
            f"Dashboard WebSocket disconnected: {self.channel_name} "
            f"(code: {close_code})"
        )

    async def receive(self, text_data: str) -> None:
        """
        Handle incoming WebSocket messages.
        
        Args:
            text_data: The received message.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                }))
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received: {text_data}")

    async def sensor_reading(self, event: dict[str, Any]) -> None:
        """
        Send sensor reading update to client.
        
        Args:
            event: The event data containing the reading.
        """
        await self.send(text_data=json.dumps({
            'type': 'sensor_reading',
            'data': event['data'],
        }))

    async def ac_status_changed(self, event: dict[str, Any]) -> None:
        """
        Send AC status change to client.
        
        Args:
            event: The event data containing the status change.
        """
        await self.send(text_data=json.dumps({
            'type': 'ac_status_changed',
            'data': event['data'],
        }))

    async def alert_triggered(self, event: dict[str, Any]) -> None:
        """
        Send new alert to client.
        
        Args:
            event: The event data containing the alert.
        """
        await self.send(text_data=json.dumps({
            'type': 'alert_triggered',
            'data': event['data'],
        }))

    async def connection_status(self, event: dict[str, Any]) -> None:
        """
        Send sensor connection status change to client.
        
        Args:
            event: The event data containing the connection status.
        """
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'data': event['data'],
        }))


class RoomConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for room-specific updates.
    
    Provides targeted updates for a specific room.
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        
        # Validate room exists
        room_exists = await self._room_exists(self.room_id)
        if not room_exists:
            await self.close(code=4004)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        logger.info(
            f"Room WebSocket connected: {self.channel_name} "
            f"(room: {self.room_id})"
        )

    async def disconnect(self, close_code: int) -> None:
        """
        Handle WebSocket disconnection.
        
        Args:
            close_code: The WebSocket close code.
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(
            f"Room WebSocket disconnected: {self.channel_name} "
            f"(room: {self.room_id}, code: {close_code})"
        )

    async def receive(self, text_data: str) -> None:
        """
        Handle incoming WebSocket messages.
        
        Args:
            text_data: The received message.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                }))
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received: {text_data}")

    async def sensor_reading(self, event: dict[str, Any]) -> None:
        """Send sensor reading update to client."""
        await self.send(text_data=json.dumps({
            'type': 'sensor_reading',
            'data': event['data'],
        }))

    async def ac_status_changed(self, event: dict[str, Any]) -> None:
        """Send AC status change to client."""
        await self.send(text_data=json.dumps({
            'type': 'ac_status_changed',
            'data': event['data'],
        }))

    async def alert_triggered(self, event: dict[str, Any]) -> None:
        """Send new alert to client."""
        await self.send(text_data=json.dumps({
            'type': 'alert_triggered',
            'data': event['data'],
        }))

    async def connection_status(self, event: dict[str, Any]) -> None:
        """Send sensor connection status change to client."""
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'data': event['data'],
        }))

    @database_sync_to_async
    def _room_exists(self, room_id: str) -> bool:
        """
        Check if a room exists.
        
        Args:
            room_id: The room ID to check.
            
        Returns:
            True if the room exists.
        """
        from apps.core.models import Room
        return Room.objects.filter(id=room_id).exists()


async def broadcast_sensor_reading(
    room_id: str,
    sensor_id: str,
    temperature: float | None,
    humidity: float | None,
    timestamp: str
) -> None:
    """
    Broadcast a sensor reading to connected clients.
    
    Args:
        room_id: The room ID.
        sensor_id: The sensor ID.
        temperature: The temperature reading.
        humidity: The humidity reading.
        timestamp: The reading timestamp.
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    data = {
        'room_id': str(room_id),
        'sensor_id': str(sensor_id),
        'temperature': temperature,
        'humidity': humidity,
        'timestamp': timestamp,
    }
    
    # Send to dashboard
    await channel_layer.group_send(
        DashboardConsumer.DASHBOARD_GROUP,
        {
            'type': 'sensor_reading',
            'data': data,
        }
    )
    
    # Send to room-specific channel
    await channel_layer.group_send(
        f'room_{room_id}',
        {
            'type': 'sensor_reading',
            'data': data,
        }
    )


async def broadcast_ac_status(
    room_id: str,
    ac_id: str,
    status: str,
    changed_by: str | None = None
) -> None:
    """
    Broadcast AC status change to connected clients.
    
    Args:
        room_id: The room ID.
        ac_id: The air conditioner ID.
        status: The new status.
        changed_by: Who changed the status.
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    data = {
        'room_id': str(room_id),
        'ac_id': str(ac_id),
        'status': status,
        'changed_by': changed_by,
    }
    
    # Send to dashboard
    await channel_layer.group_send(
        DashboardConsumer.DASHBOARD_GROUP,
        {
            'type': 'ac_status_changed',
            'data': data,
        }
    )
    
    # Send to room-specific channel
    await channel_layer.group_send(
        f'room_{room_id}',
        {
            'type': 'ac_status_changed',
            'data': data,
        }
    )


async def broadcast_alert(
    room_id: str,
    alert_id: str,
    alert_type: str,
    severity: str,
    message: str
) -> None:
    """
    Broadcast new alert to connected clients.
    
    Args:
        room_id: The room ID.
        alert_id: The alert ID.
        alert_type: The type of alert.
        severity: The alert severity.
        message: The alert message.
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    data = {
        'room_id': str(room_id),
        'alert_id': str(alert_id),
        'alert_type': alert_type,
        'severity': severity,
        'message': message,
    }
    
    # Send to dashboard
    await channel_layer.group_send(
        DashboardConsumer.DASHBOARD_GROUP,
        {
            'type': 'alert_triggered',
            'data': data,
        }
    )
    
    # Send to room-specific channel
    await channel_layer.group_send(
        f'room_{room_id}',
        {
            'type': 'alert_triggered',
            'data': data,
        }
    )


