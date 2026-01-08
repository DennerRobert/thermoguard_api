"""
Core signals for ThermoGuard IoT API.

This module contains Django signals for core application events.
"""
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.core.models import DataCenter, Room

logger = logging.getLogger('thermoguard')


@receiver(post_save, sender=DataCenter)
def datacenter_saved(
    sender: type,
    instance: DataCenter,
    created: bool,
    **kwargs
) -> None:
    """
    Handle DataCenter save events.
    
    Args:
        sender: The model class.
        instance: The DataCenter instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        logger.info(f"New DataCenter created: {instance.name}")
    else:
        logger.debug(f"DataCenter updated: {instance.name}")


@receiver(post_delete, sender=DataCenter)
def datacenter_deleted(sender: type, instance: DataCenter, **kwargs) -> None:
    """
    Handle DataCenter delete events.
    
    Args:
        sender: The model class.
        instance: The DataCenter instance.
        **kwargs: Additional keyword arguments.
    """
    logger.warning(f"DataCenter deleted: {instance.name}")


@receiver(post_save, sender=Room)
def room_saved(
    sender: type,
    instance: Room,
    created: bool,
    **kwargs
) -> None:
    """
    Handle Room save events.
    
    Args:
        sender: The model class.
        instance: The Room instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        logger.info(
            f"New Room created: {instance.name} in {instance.data_center.name}"
        )
    else:
        logger.debug(f"Room updated: {instance.name}")


