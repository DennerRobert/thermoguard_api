"""
Alert models for ThermoGuard IoT API.

This module contains the Alert model for system notifications.
"""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, Room


class Alert(BaseModel):
    """
    Alert model.
    
    Represents system alerts for temperature, humidity, and device issues.
    
    Attributes:
        room: The room where the alert was triggered.
        alert_type: Type of alert (high_temp, low_temp, etc).
        severity: Severity level (info, warning, critical).
        message: Human-readable alert message.
        is_acknowledged: Whether the alert has been acknowledged.
        acknowledged_by: User who acknowledged the alert.
        acknowledged_at: When the alert was acknowledged.
    """
    
    class AlertType(models.TextChoices):
        """Alert type choices."""
        HIGH_TEMP = 'high_temp', 'Temperatura Alta'
        LOW_TEMP = 'low_temp', 'Temperatura Baixa'
        HIGH_HUMIDITY = 'high_humidity', 'Umidade Alta'
        LOW_HUMIDITY = 'low_humidity', 'Umidade Baixa'
        SENSOR_OFFLINE = 'sensor_offline', 'Sensor Offline'
        AC_ERROR = 'ac_error', 'Erro no Ar-Condicionado'
        SYSTEM_ERROR = 'system_error', 'Erro do Sistema'

    class Severity(models.TextChoices):
        """Severity level choices."""
        INFO = 'info', 'Informação'
        WARNING = 'warning', 'Aviso'
        CRITICAL = 'critical', 'Crítico'

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Sala'
    )
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices,
        verbose_name='Tipo de Alerta'
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.WARNING,
        verbose_name='Severidade'
    )
    message = models.TextField(
        verbose_name='Mensagem'
    )
    is_acknowledged = models.BooleanField(
        default=False,
        verbose_name='Reconhecido'
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        verbose_name='Reconhecido Por'
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Reconhecido Em'
    )

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_acknowledged', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"[{self.severity.upper()}] {self.alert_type} - {self.room.name}"

    def acknowledge(self, user) -> None:
        """
        Acknowledge the alert.
        
        Args:
            user: The user acknowledging the alert.
        """
        from django.utils import timezone
        
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=[
            'is_acknowledged',
            'acknowledged_by',
            'acknowledged_at',
            'updated_at'
        ])


