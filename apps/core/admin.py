"""
Admin configuration for core models.

This module configures the Django admin interface for core models.
"""
from django.contrib import admin

from apps.core.models import DataCenter, Room


@admin.register(DataCenter)
class DataCenterAdmin(admin.ModelAdmin):
    """Admin configuration for DataCenter model."""
    
    list_display = ['name', 'location', 'is_active', 'room_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location']
    ordering = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin configuration for Room model."""
    
    list_display = [
        'name',
        'data_center',
        'target_temperature',
        'target_humidity',
        'operation_mode',
        'is_active',
    ]
    list_filter = ['data_center', 'operation_mode', 'is_active']
    search_fields = ['name', 'description', 'data_center__name']
    ordering = ['data_center', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']


