"""
Alert services for ThermoGuard IoT API.

This module contains business logic for alert operations.
"""
import logging
from datetime import timedelta
from typing import Any

from asgiref.sync import async_to_sync
from django.utils import timezone

from apps.alerts.models import Alert
from apps.core.models import Room

logger = logging.getLogger('thermoguard')


class AlertService:
    """
    Service class for alert operations.
    
    Provides methods for creating and managing alerts.
    """

    # Minimum time between similar alerts (to avoid spam)
    ALERT_COOLDOWN_MINUTES = 5

    @staticmethod
    def create_alert(
        room: Room,
        alert_type: str,
        severity: str,
        message: str
    ) -> Alert | None:
        """
        Create a new alert if not duplicate.
        
        Checks for similar recent alerts to avoid spam.
        
        Args:
            room: The room for the alert.
            alert_type: Type of alert.
            severity: Severity level.
            message: Alert message.
            
        Returns:
            The created alert or None if duplicate.
        """
        # Check for recent similar alerts
        cooldown_time = timezone.now() - timedelta(
            minutes=AlertService.ALERT_COOLDOWN_MINUTES
        )
        
        recent_similar = Alert.objects.filter(
            room=room,
            alert_type=alert_type,
            created_at__gte=cooldown_time,
            is_acknowledged=False,
        ).exists()
        
        if recent_similar:
            logger.debug(
                f"Skipping duplicate alert: {alert_type} for {room.name}"
            )
            return None
        
        # Create the alert
        alert = Alert.objects.create(
            room=room,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        
        logger.info(
            f"Alert created: [{severity.upper()}] {alert_type} - {room.name}"
        )
        
        # Broadcast alert via WebSocket
        AlertService._broadcast_alert(alert)
        
        return alert

    @staticmethod
    def _broadcast_alert(alert: Alert) -> None:
        """
        Broadcast alert via WebSocket.
        
        Args:
            alert: The alert to broadcast.
        """
        from apps.core.consumers import broadcast_alert
        
        try:
            async_to_sync(broadcast_alert)(
                room_id=str(alert.room.id),
                alert_id=str(alert.id),
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast alert: {e}")

    @staticmethod
    def get_active_alerts_count(room_id: str | None = None) -> dict[str, int]:
        """
        Get count of active (unacknowledged) alerts.
        
        Args:
            room_id: Optional room ID to filter by.
            
        Returns:
            Dictionary with counts by severity.
        """
        queryset = Alert.objects.filter(is_acknowledged=False)
        
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return {
            'total': queryset.count(),
            'critical': queryset.filter(severity=Alert.Severity.CRITICAL).count(),
            'warning': queryset.filter(severity=Alert.Severity.WARNING).count(),
            'info': queryset.filter(severity=Alert.Severity.INFO).count(),
        }

    @staticmethod
    def cleanup_old_alerts() -> int:
        """
        Clean up old acknowledged alerts.
        
        Removes acknowledged alerts older than the retention period.
        
        Returns:
            Number of alerts deleted.
        """
        from django.conf import settings
        
        retention_days = settings.THERMOGUARD.get('ALERT_RETENTION_DAYS', 365)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        deleted_count, _ = Alert.objects.filter(
            is_acknowledged=True,
            created_at__lt=cutoff_date,
        ).delete()
        
        if deleted_count:
            logger.info(f"Cleaned up {deleted_count} old alerts")
        
        return deleted_count

    @staticmethod
    def escalate_critical_alerts() -> None:
        """
        Escalate unacknowledged critical alerts.
        
        Sends notifications for critical alerts that haven't been
        acknowledged within a certain time period.
        """
        escalation_threshold = timezone.now() - timedelta(minutes=30)
        
        unacknowledged_critical = Alert.objects.filter(
            severity=Alert.Severity.CRITICAL,
            is_acknowledged=False,
            created_at__lte=escalation_threshold,
        )
        
        for alert in unacknowledged_critical:
            # TODO: Send email/SMS notification
            logger.warning(
                f"ESCALATION: Critical alert unacknowledged for 30+ minutes: "
                f"{alert.message}"
            )


