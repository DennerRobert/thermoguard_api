"""
Core models for ThermoGuard IoT API.

This module contains base models and the DataCenter model.
All models use UUID as primary key for security and distribution.
"""
import uuid
from typing import Any

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields.
    
    Provides UUID primary key and timestamp fields for all models.
    
    Attributes:
        id: UUID primary key.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the model instance with validation."""
        self.full_clean()
        super().save(*args, **kwargs)


class DataCenter(BaseModel):
    """
    Data Center model.
    
    Represents a physical data center location containing multiple rooms.
    
    Attributes:
        name: Name of the data center.
        location: Physical address or location description.
        is_active: Whether the data center is currently active.
    """
    
    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )
    location = models.CharField(
        max_length=500,
        verbose_name='Localização'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'Data Center'
        verbose_name_plural = 'Data Centers'
        ordering = ['name']

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} - {self.location}"

    @property
    def room_count(self) -> int:
        """Return the number of rooms in this data center."""
        return self.rooms.count()

    @property
    def active_room_count(self) -> int:
        """Return the number of active rooms in this data center."""
        return self.rooms.filter(is_active=True).count()


class Room(BaseModel):
    """
    Room model.
    
    Represents a server room within a data center with temperature controls.
    
    Attributes:
        data_center: Reference to the parent data center.
        name: Name of the room.
        description: Detailed description of the room.
        target_temperature: Desired temperature setpoint in Celsius.
        target_humidity: Desired humidity setpoint in percentage.
        operation_mode: Control mode (manual or automatic).
        is_active: Whether the room is currently active.
    """
    
    class OperationMode(models.TextChoices):
        """Operation mode choices."""
        MANUAL = 'manual', 'Manual'
        AUTOMATIC = 'automatic', 'Automático'

    data_center = models.ForeignKey(
        DataCenter,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='Data Center'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição'
    )
    target_temperature = models.FloatField(
        default=22.0,
        verbose_name='Temperatura Alvo (°C)'
    )
    target_humidity = models.FloatField(
        default=50.0,
        verbose_name='Umidade Alvo (%)'
    )
    operation_mode = models.CharField(
        max_length=20,
        choices=OperationMode.choices,
        default=OperationMode.MANUAL,
        verbose_name='Modo de Operação'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        ordering = ['data_center', 'name']
        unique_together = ['data_center', 'name']

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.data_center.name})"

    @property
    def sensor_count(self) -> int:
        """Return the number of sensors in this room."""
        return self.sensors.count()

    @property
    def online_sensor_count(self) -> int:
        """Return the number of online sensors in this room."""
        return self.sensors.filter(is_online=True).count()

    @property
    def air_conditioner_count(self) -> int:
        """Return the number of air conditioners in this room."""
        return self.air_conditioners.count()


