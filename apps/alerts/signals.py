"""
Alert signals for ThermoGuard IoT API.

This module contains Django signals for alert events.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.alerts.models import Alert

logger = logging.getLogger('thermoguard')


@receiver(post_save, sender=Alert)
def alert_saved(sender: type, instance: Alert, created: bool, **kwargs) -> None:
    """
    Handle Alert save events.
    
    Args:
        sender: The model class.
        instance: The Alert instance.
        created: Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨',
        }
        
        emoji = severity_emoji.get(instance.severity, '📢')
        
        logger.info(
            f"{emoji} New Alert: [{instance.severity.upper()}] "
            f"{instance.alert_type} in {instance.room.name}"
        )


