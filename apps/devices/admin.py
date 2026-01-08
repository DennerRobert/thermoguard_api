"""
Admin configuration for device models.

This module configures the Django admin interface for device models.
"""
from django.contrib import admin

from apps.devices.models import AirConditioner, CommandLog, IRSignal


@admin.register(AirConditioner)
class AirConditionerAdmin(admin.ModelAdmin):
    """Admin configuration for AirConditioner model."""
    
    list_display = [
        'name',
        'room',
        'status',
        'is_active',
        'has_ir_codes',
        'last_command',
    ]
    list_filter = ['status', 'is_active', 'room__data_center', 'room']
    search_fields = ['name', 'room__name', 'esp32_device_id']
    ordering = ['room', 'name']
    readonly_fields = ['id', 'status', 'last_command', 'created_at', 'updated_at']


@admin.register(IRSignal)
class IRSignalAdmin(admin.ModelAdmin):
    """Admin configuration for IRSignal model."""
    
    list_display = [
        'air_conditioner',
        'command_type',
        'protocol',
        'created_at',
    ]
    list_filter = ['command_type', 'air_conditioner__room']
    search_fields = ['air_conditioner__name', 'description']
    ordering = ['air_conditioner', 'command_type']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CommandLog)
class CommandLogAdmin(admin.ModelAdmin):
    """Admin configuration for CommandLog model."""
    
    list_display = [
        'air_conditioner',
        'command',
        'executed_by',
        'success',
        'automatic',
        'created_at',
    ]
    list_filter = ['success', 'automatic', 'command', 'air_conditioner__room']
    search_fields = [
        'air_conditioner__name',
        'command',
        'executed_by__email',
        'response',
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


