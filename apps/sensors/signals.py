"""
Sensor signals for ThermoGuard IoT API.

This module contains Django signals for sensor events.
"""
import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.sensors.models import Sensor, SensorReading

logger = logging.getLogger('thermoguard')


@receiver(post_save, sender=Sensor)
def sensor_saved(sender: type, instance: Sensor, created: bool, **kwargs) -> None:
    """
    Handle Sensor save events.
    
    Args:
        sender: The model class.
        instance: The Sensor instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        logger.info(
            f"New Sensor created: {instance.name} ({instance.device_id}) "
            f"in room {instance.room.name}"
        )


@receiver(post_delete, sender=Sensor)
def sensor_deleted(sender: type, instance: Sensor, **kwargs) -> None:
    """
    Handle Sensor delete events.
    
    Args:
        sender: The model class.
        instance: The Sensor instance.
        **kwargs: Additional keyword arguments.
    """
    logger.warning(
        f"Sensor deleted: {instance.name} ({instance.device_id})"
    )


@receiver(pre_save, sender=Sensor)
def sensor_status_changed(sender: type, instance: Sensor, **kwargs) -> None:
    """
    Handle Sensor status changes.
    
    Broadcasts connection status changes via WebSocket.
    
    Args:
        sender: The model class.
        instance: The Sensor instance.
        **kwargs: Additional keyword arguments.
    """
    if not instance.pk:
        return
    
    try:
        old_instance = Sensor.objects.get(pk=instance.pk)
        
        if old_instance.is_online != instance.is_online:
            # Broadcast status change
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            
            data = {
                'sensor_id': str(instance.id),
                'sensor_name': instance.name,
                'device_id': instance.device_id,
                'is_online': instance.is_online,
                'room_id': str(instance.room_id),
            }
            
            # Broadcast to dashboard
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'connection_status',
                    'data': data,
                }
            )
            
            # Broadcast to room
            async_to_sync(channel_layer.group_send)(
                f'room_{instance.room_id}',
                {
                    'type': 'connection_status',
                    'data': data,
                }
            )
            
            status_text = 'online' if instance.is_online else 'offline'
            logger.info(f"Sensor {instance.device_id} is now {status_text}")
    except Sensor.DoesNotExist:
        pass


