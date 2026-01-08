"""
Sensor models for ThermoGuard IoT API.

This module contains models for sensors and their readings.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel, Room


class Sensor(BaseModel):
    """
    Sensor model (DHT22/ESP32).
    
    Represents a physical sensor device that reports temperature and humidity.
    
    Attributes:
        room: The room where the sensor is located.
        device_id: Unique identifier (MAC address) of the ESP32.
        name: Human-readable name for the sensor.
        sensor_type: Type of measurements the sensor provides.
        is_online: Whether the sensor is currently online.
        last_seen: Last time the sensor sent data.
    """
    
    class SensorType(models.TextChoices):
        """Sensor type choices."""
        TEMPERATURE = 'temperature', 'Temperatura'
        HUMIDITY = 'humidity', 'Umidade'
        BOTH = 'both', 'Temperatura e Umidade'

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='sensors',
        verbose_name='Sala'
    )
    device_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='ID do Dispositivo',
        help_text='MAC address do ESP32'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )
    sensor_type = models.CharField(
        max_length=20,
        choices=SensorType.choices,
        default=SensorType.BOTH,
        verbose_name='Tipo de Sensor'
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name='Online'
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Atividade'
    )

    class Meta:
        verbose_name = 'Sensor'
        verbose_name_plural = 'Sensores'
        ordering = ['room', 'name']

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.device_id})"

    def update_status(self) -> None:
        """Update sensor online status based on last activity."""
        if self.last_seen:
            threshold = settings.THERMOGUARD.get(
                'SENSOR_OFFLINE_THRESHOLD_MINUTES', 5
            )
            offline_threshold = timezone.now() - timezone.timedelta(
                minutes=threshold
            )
            self.is_online = self.last_seen > offline_threshold
        else:
            self.is_online = False

    def mark_online(self) -> None:
        """Mark sensor as online with current timestamp."""
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=['is_online', 'last_seen', 'updated_at'])

    @property
    def minutes_since_last_seen(self) -> int | None:
        """Return minutes since last activity."""
        if not self.last_seen:
            return None
        delta = timezone.now() - self.last_seen
        return int(delta.total_seconds() / 60)


class SensorReading(BaseModel):
    """
    Sensor reading model.
    
    Stores individual temperature and humidity readings from sensors.
    
    Attributes:
        sensor: The sensor that provided the reading.
        temperature: Temperature reading in Celsius.
        humidity: Humidity reading in percentage.
        timestamp: When the reading was taken.
    """
    
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='readings',
        verbose_name='Sensor'
    )
    temperature = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Temperatura (°C)'
    )
    humidity = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Umidade (%)'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Timestamp'
    )

    class Meta:
        verbose_name = 'Leitura do Sensor'
        verbose_name_plural = 'Leituras dos Sensores'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.sensor.name}: {self.temperature}°C / {self.humidity}% @ {self.timestamp}"

    def clean(self) -> None:
        """Validate reading values."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate temperature range
        if self.temperature is not None:
            if self.temperature < -40 or self.temperature > 80:
                errors['temperature'] = (
                    'Temperatura deve estar entre -40°C e 80°C.'
                )
        
        # Validate humidity range
        if self.humidity is not None:
            if self.humidity < 0 or self.humidity > 100:
                errors['humidity'] = (
                    'Umidade deve estar entre 0% e 100%.'
                )
        
        # At least one reading must be provided
        if self.temperature is None and self.humidity is None:
            errors['__all__'] = (
                'Pelo menos temperatura ou umidade deve ser fornecida.'
            )
        
        if errors:
            raise ValidationError(errors)


class AggregatedReading(BaseModel):
    """
    Aggregated sensor reading model.
    
    Stores hourly aggregated readings for historical data.
    
    Attributes:
        sensor: The sensor for the aggregated data.
        hour: The hour for the aggregation.
        temp_min: Minimum temperature in the hour.
        temp_max: Maximum temperature in the hour.
        temp_avg: Average temperature in the hour.
        humidity_min: Minimum humidity in the hour.
        humidity_max: Maximum humidity in the hour.
        humidity_avg: Average humidity in the hour.
        reading_count: Number of readings in the hour.
    """
    
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='aggregated_readings',
        verbose_name='Sensor'
    )
    hour = models.DateTimeField(
        db_index=True,
        verbose_name='Hora'
    )
    temp_min = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Temp. Mínima'
    )
    temp_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Temp. Máxima'
    )
    temp_avg = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Temp. Média'
    )
    humidity_min = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Umidade Mínima'
    )
    humidity_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Umidade Máxima'
    )
    humidity_avg = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Umidade Média'
    )
    reading_count = models.IntegerField(
        default=0,
        verbose_name='Quantidade de Leituras'
    )

    class Meta:
        verbose_name = 'Leitura Agregada'
        verbose_name_plural = 'Leituras Agregadas'
        ordering = ['-hour']
        unique_together = ['sensor', 'hour']
        indexes = [
            models.Index(fields=['sensor', '-hour']),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.sensor.name}: Aggregated @ {self.hour}"


