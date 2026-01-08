"""
Serializers for core models.

This module provides serializers for DataCenter and Room models.
"""
from typing import Any

from rest_framework import serializers

from apps.core.models import DataCenter, Room


class DataCenterSerializer(serializers.ModelSerializer):
    """
    Serializer for DataCenter model.
    
    Includes computed properties for room counts.
    """
    
    room_count = serializers.IntegerField(read_only=True)
    active_room_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataCenter
        fields = [
            'id',
            'name',
            'location',
            'is_active',
            'room_count',
            'active_room_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DataCenterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DataCenter."""
    
    class Meta:
        model = DataCenter
        fields = ['name', 'location', 'is_active']


class RoomSerializer(serializers.ModelSerializer):
    """
    Serializer for Room model.
    
    Includes computed properties and nested DataCenter info.
    """
    
    data_center_name = serializers.CharField(
        source='data_center.name',
        read_only=True
    )
    sensor_count = serializers.IntegerField(read_only=True)
    online_sensor_count = serializers.IntegerField(read_only=True)
    air_conditioner_count = serializers.IntegerField(read_only=True)
    operation_mode_display = serializers.CharField(
        source='get_operation_mode_display',
        read_only=True
    )

    class Meta:
        model = Room
        fields = [
            'id',
            'data_center',
            'data_center_name',
            'name',
            'description',
            'target_temperature',
            'target_humidity',
            'operation_mode',
            'operation_mode_display',
            'is_active',
            'sensor_count',
            'online_sensor_count',
            'air_conditioner_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Room."""
    
    class Meta:
        model = Room
        fields = [
            'data_center',
            'name',
            'description',
            'target_temperature',
            'target_humidity',
            'operation_mode',
            'is_active',
        ]

    def validate_target_temperature(self, value: float) -> float:
        """
        Validate target temperature is within reasonable range.
        
        Args:
            value: The temperature value.
            
        Returns:
            The validated temperature.
            
        Raises:
            ValidationError: If temperature is out of range.
        """
        if value < 15 or value > 30:
            raise serializers.ValidationError(
                'A temperatura alvo deve estar entre 15°C e 30°C.'
            )
        return value

    def validate_target_humidity(self, value: float) -> float:
        """
        Validate target humidity is within reasonable range.
        
        Args:
            value: The humidity value.
            
        Returns:
            The validated humidity.
            
        Raises:
            ValidationError: If humidity is out of range.
        """
        if value < 20 or value > 80:
            raise serializers.ValidationError(
                'A umidade alvo deve estar entre 20% e 80%.'
            )
        return value


class RoomSettingsSerializer(serializers.ModelSerializer):
    """Serializer for Room settings update."""
    
    class Meta:
        model = Room
        fields = [
            'target_temperature',
            'target_humidity',
            'operation_mode',
        ]

    def validate_target_temperature(self, value: float) -> float:
        """Validate target temperature."""
        if value < 15 or value > 30:
            raise serializers.ValidationError(
                'A temperatura alvo deve estar entre 15°C e 30°C.'
            )
        return value

    def validate_target_humidity(self, value: float) -> float:
        """Validate target humidity."""
        if value < 20 or value > 80:
            raise serializers.ValidationError(
                'A umidade alvo deve estar entre 20% e 80%.'
            )
        return value


class DashboardRoomSerializer(serializers.Serializer):
    """
    Serializer for dashboard room data.
    
    Includes current readings and system status.
    """
    
    id = serializers.UUIDField()
    name = serializers.CharField()
    data_center_name = serializers.CharField()
    target_temperature = serializers.FloatField()
    target_humidity = serializers.FloatField()
    current_temperature = serializers.FloatField(allow_null=True)
    current_humidity = serializers.FloatField(allow_null=True)
    operation_mode = serializers.CharField()
    is_active = serializers.BooleanField()
    sensors_online = serializers.IntegerField()
    sensors_total = serializers.IntegerField()
    ac_units_on = serializers.IntegerField()
    ac_units_total = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    last_reading_at = serializers.DateTimeField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    """
    Serializer for main dashboard data.
    
    Provides system-wide overview.
    """
    
    total_datacenters = serializers.IntegerField()
    total_rooms = serializers.IntegerField()
    total_sensors = serializers.IntegerField()
    sensors_online = serializers.IntegerField()
    total_ac_units = serializers.IntegerField()
    ac_units_on = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    rooms = DashboardRoomSerializer(many=True)


class StatisticsSerializer(serializers.Serializer):
    """Serializer for temperature/humidity statistics."""
    
    room_id = serializers.UUIDField()
    room_name = serializers.CharField()
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    temperature = serializers.DictField(child=serializers.FloatField())
    humidity = serializers.DictField(child=serializers.FloatField())
    reading_count = serializers.IntegerField()


