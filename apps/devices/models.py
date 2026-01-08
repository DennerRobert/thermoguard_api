"""
Device models for ThermoGuard IoT API.

This module contains models for air conditioners, IR signals, and command logs.
"""
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, Room


class AirConditioner(BaseModel):
    """
    Air Conditioner model.
    
    Represents a physical AC unit controlled via IR transmitter.
    
    Attributes:
        room: The room where the AC is located.
        name: Human-readable name for the AC.
        status: Current status (on, off, error).
        is_active: Whether the AC is available for use.
        ir_code: JSON data with recorded IR codes.
        last_command: Timestamp of last command sent.
    """
    
    class Status(models.TextChoices):
        """AC status choices."""
        ON = 'on', 'Ligado'
        OFF = 'off', 'Desligado'
        ERROR = 'error', 'Erro'

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='air_conditioners',
        verbose_name='Sala'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFF,
        verbose_name='Status'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    ir_code = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Códigos IR',
        help_text='Códigos IR gravados para diferentes comandos'
    )
    last_command = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Comando'
    )
    esp32_device_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='ID do ESP32 Transmissor',
        help_text='MAC address do ESP32 que controla este AC'
    )

    class Meta:
        verbose_name = 'Ar-Condicionado'
        verbose_name_plural = 'Ar-Condicionados'
        ordering = ['room', 'name']

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.room.name})"

    def turn_on(self) -> bool:
        """
        Turn on the air conditioner.
        
        Returns:
            True if successful, False otherwise.
        """
        from django.utils import timezone
        from apps.devices.services import AirConditionerService
        
        success = AirConditionerService.send_ir_command(self, 'power_on')
        
        if success:
            self.status = self.Status.ON
            self.last_command = timezone.now()
            self.save(update_fields=['status', 'last_command', 'updated_at'])
        
        return success

    def turn_off(self) -> bool:
        """
        Turn off the air conditioner.
        
        Returns:
            True if successful, False otherwise.
        """
        from django.utils import timezone
        from apps.devices.services import AirConditionerService
        
        success = AirConditionerService.send_ir_command(self, 'power_off')
        
        if success:
            self.status = self.Status.OFF
            self.last_command = timezone.now()
            self.save(update_fields=['status', 'last_command', 'updated_at'])
        
        return success

    @property
    def has_ir_codes(self) -> bool:
        """Check if AC has recorded IR codes."""
        return bool(self.ir_code and 'power_on' in self.ir_code)


class IRSignal(BaseModel):
    """
    IR Signal model.
    
    Stores recorded IR signals for AC control.
    
    Attributes:
        air_conditioner: The AC this signal controls.
        command_type: Type of command (power_on, power_off, etc).
        raw_signal: Raw IR signal data.
        description: Optional description of the signal.
    """
    
    class CommandType(models.TextChoices):
        """Command type choices."""
        POWER_ON = 'power_on', 'Ligar'
        POWER_OFF = 'power_off', 'Desligar'
        TEMP_UP = 'temp_up', 'Aumentar Temperatura'
        TEMP_DOWN = 'temp_down', 'Diminuir Temperatura'
        MODE_COOL = 'mode_cool', 'Modo Refrigeração'
        MODE_HEAT = 'mode_heat', 'Modo Aquecimento'
        MODE_AUTO = 'mode_auto', 'Modo Automático'
        FAN_LOW = 'fan_low', 'Ventilação Baixa'
        FAN_MED = 'fan_med', 'Ventilação Média'
        FAN_HIGH = 'fan_high', 'Ventilação Alta'

    air_conditioner = models.ForeignKey(
        AirConditioner,
        on_delete=models.CASCADE,
        related_name='ir_signals',
        verbose_name='Ar-Condicionado'
    )
    command_type = models.CharField(
        max_length=20,
        choices=CommandType.choices,
        verbose_name='Tipo de Comando'
    )
    raw_signal = models.TextField(
        verbose_name='Sinal Raw',
        help_text='Dados brutos do sinal IR'
    )
    protocol = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Protocolo IR'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Descrição'
    )

    class Meta:
        verbose_name = 'Sinal IR'
        verbose_name_plural = 'Sinais IR'
        unique_together = ['air_conditioner', 'command_type']
        ordering = ['air_conditioner', 'command_type']

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.air_conditioner.name} - {self.get_command_type_display()}"


class CommandLog(BaseModel):
    """
    Command Log model.
    
    Stores log of all commands sent to devices.
    
    Attributes:
        air_conditioner: The AC the command was sent to.
        command: The command that was executed.
        executed_by: User who executed the command (null for automatic).
        success: Whether the command was successful.
        response: Response from the device.
        automatic: Whether this was an automatic command.
    """
    
    air_conditioner = models.ForeignKey(
        AirConditioner,
        on_delete=models.CASCADE,
        related_name='command_logs',
        verbose_name='Ar-Condicionado'
    )
    command = models.CharField(
        max_length=50,
        verbose_name='Comando'
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='device_commands',
        verbose_name='Executado Por'
    )
    success = models.BooleanField(
        default=True,
        verbose_name='Sucesso'
    )
    response = models.TextField(
        blank=True,
        default='',
        verbose_name='Resposta'
    )
    automatic = models.BooleanField(
        default=False,
        verbose_name='Automático',
        help_text='Indica se foi executado automaticamente'
    )

    class Meta:
        verbose_name = 'Log de Comando'
        verbose_name_plural = 'Logs de Comandos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['air_conditioner', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        executor = self.executed_by.email if self.executed_by else 'Sistema'
        status = 'OK' if self.success else 'FALHA'
        return f"{self.command} -> {self.air_conditioner.name} ({status}) by {executor}"


