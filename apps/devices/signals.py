"""
Device signals for ThermoGuard IoT API.

This module contains Django signals for device events.
"""
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.devices.models import AirConditioner, CommandLog

logger = logging.getLogger('thermoguard')


@receiver(post_save, sender=AirConditioner)
def air_conditioner_saved(
    sender: type,
    instance: AirConditioner,
    created: bool,
    **kwargs
) -> None:
    """
    Handle AirConditioner save events.
    
    Args:
        sender: The model class.
        instance: The AirConditioner instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        logger.info(
            f"New AC created: {instance.name} in {instance.room.name}"
        )


@receiver(post_delete, sender=AirConditioner)
def air_conditioner_deleted(
    sender: type,
    instance: AirConditioner,
    **kwargs
) -> None:
    """
    Handle AirConditioner delete events.
    
    Args:
        sender: The model class.
        instance: The AirConditioner instance.
        **kwargs: Additional keyword arguments.
    """
    logger.warning(f"AC deleted: {instance.name}")


@receiver(post_save, sender=CommandLog)
def command_log_created(
    sender: type,
    instance: CommandLog,
    created: bool,
    **kwargs
) -> None:
    """
    Handle CommandLog creation.
    
    Creates alert if command failed.
    
    Args:
        sender: The model class.
        instance: The CommandLog instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created and not instance.success:
        from apps.alerts.services import AlertService
        
        AlertService.create_alert(
            room=instance.air_conditioner.room,
            alert_type='ac_error',
            severity='warning',
            message=(
                f'Falha ao executar comando {instance.command} '
                f'no AC {instance.air_conditioner.name}'
            )
        )


