"""
Admin configuration for sensor models.

This module configures the Django admin interface for sensor models.
"""
from django.contrib import admin

from apps.sensors.models import AggregatedReading, Sensor, SensorReading


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    """Admin configuration for Sensor model."""
    
    list_display = [
        'name',
        'device_id',
        'room',
        'sensor_type',
        'is_online',
        'last_seen',
    ]
    list_filter = ['sensor_type', 'is_online', 'room__data_center', 'room']
    search_fields = ['name', 'device_id', 'room__name']
    ordering = ['room', 'name']
    readonly_fields = ['id', 'is_online', 'last_seen', 'created_at', 'updated_at']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    """Admin configuration for SensorReading model."""
    
    list_display = [
        'sensor',
        'temperature',
        'humidity',
        'timestamp',
    ]
    list_filter = ['sensor__room', 'timestamp']
    search_fields = ['sensor__name', 'sensor__device_id']
    ordering = ['-timestamp']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'


@admin.register(AggregatedReading)
class AggregatedReadingAdmin(admin.ModelAdmin):
    """Admin configuration for AggregatedReading model."""
    
    list_display = [
        'sensor',
        'hour',
        'temp_avg',
        'humidity_avg',
        'reading_count',
    ]
    list_filter = ['sensor__room', 'hour']
    search_fields = ['sensor__name']
    ordering = ['-hour']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'hour'


