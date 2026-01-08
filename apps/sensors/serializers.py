"""
Serializers for sensor models.

This module provides serializers for sensors and readings.
"""
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.sensors.models import AggregatedReading, Sensor, SensorReading


class SensorSerializer(serializers.ModelSerializer):
    """
    Serializer for Sensor model.
    
    Includes room information and status details.
    """
    
    room_name = serializers.CharField(
        source='room.name',
        read_only=True
    )
    data_center_name = serializers.CharField(
        source='room.data_center.name',
        read_only=True
    )
    sensor_type_display = serializers.CharField(
        source='get_sensor_type_display',
        read_only=True
    )
    minutes_since_last_seen = serializers.IntegerField(read_only=True)

    class Meta:
        model = Sensor
        fields = [
            'id',
            'room',
            'room_name',
            'data_center_name',
            'device_id',
            'name',
            'sensor_type',
            'sensor_type_display',
            'is_online',
            'last_seen',
            'minutes_since_last_seen',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_online', 'last_seen', 'created_at', 'updated_at']


class SensorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sensors."""
    
    class Meta:
        model = Sensor
        fields = [
            'room',
            'device_id',
            'name',
            'sensor_type',
        ]

    def validate_device_id(self, value: str) -> str:
        """
        Validate device_id format.
        
        Args:
            value: The device ID.
            
        Returns:
            Validated device ID.
        """
        # Basic validation for MAC address format
        value = value.upper().replace('-', ':')
        return value


class SensorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating sensors."""
    
    class Meta:
        model = Sensor
        fields = [
            'room',
            'name',
            'sensor_type',
        ]


class SensorReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorReading model.
    
    Provides reading data with sensor information.
    """
    
    sensor_name = serializers.CharField(
        source='sensor.name',
        read_only=True
    )
    sensor_device_id = serializers.CharField(
        source='sensor.device_id',
        read_only=True
    )

    class Meta:
        model = SensorReading
        fields = [
            'id',
            'sensor',
            'sensor_name',
            'sensor_device_id',
            'temperature',
            'humidity',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp']


class SensorReadingCreateSerializer(serializers.Serializer):
    """
    Serializer for creating sensor readings.
    
    Used by ESP32 devices to submit readings.
    Supports both sensor ID and device_id for flexibility.
    """
    
    device_id = serializers.CharField(required=False)
    sensor_id = serializers.UUIDField(required=False)
    temperature = serializers.FloatField(required=False, allow_null=True)
    humidity = serializers.FloatField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate reading data.
        
        Args:
            attrs: The input attributes.
            
        Returns:
            Validated attributes.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Require either device_id or sensor_id
        if not attrs.get('device_id') and not attrs.get('sensor_id'):
            raise serializers.ValidationError(
                'device_id ou sensor_id é obrigatório.'
            )
        
        # Require at least one reading
        if attrs.get('temperature') is None and attrs.get('humidity') is None:
            raise serializers.ValidationError(
                'Pelo menos temperature ou humidity é obrigatório.'
            )
        
        # Validate temperature range
        temp = attrs.get('temperature')
        if temp is not None and (temp < -40 or temp > 80):
            raise serializers.ValidationError({
                'temperature': 'Temperatura deve estar entre -40°C e 80°C.'
            })
        
        # Validate humidity range
        humidity = attrs.get('humidity')
        if humidity is not None and (humidity < 0 or humidity > 100):
            raise serializers.ValidationError({
                'humidity': 'Umidade deve estar entre 0% e 100%.'
            })
        
        return attrs

    def create(self, validated_data: dict[str, Any]) -> SensorReading:
        """
        Create a new sensor reading.
        
        Args:
            validated_data: The validated input data.
            
        Returns:
            The created reading.
        """
        device_id = validated_data.get('device_id')
        sensor_id = validated_data.get('sensor_id')
        
        # Find sensor
        if sensor_id:
            sensor = Sensor.objects.get(id=sensor_id)
        else:
            sensor = Sensor.objects.get(device_id=device_id)
        
        # Update sensor status
        sensor.mark_online()
        
        # Create reading
        reading = SensorReading.objects.create(
            sensor=sensor,
            temperature=validated_data.get('temperature'),
            humidity=validated_data.get('humidity'),
            timestamp=validated_data.get('timestamp', timezone.now()),
        )
        
        return reading


class BulkSensorReadingSerializer(serializers.Serializer):
    """
    Serializer for bulk sensor readings.
    
    Allows ESP32 to send multiple readings at once.
    """
    
    readings = SensorReadingCreateSerializer(many=True)

    def create(self, validated_data: dict[str, Any]) -> list[SensorReading]:
        """
        Create multiple sensor readings.
        
        Args:
            validated_data: The validated input data.
            
        Returns:
            List of created readings.
        """
        readings = []
        for reading_data in validated_data['readings']:
            serializer = SensorReadingCreateSerializer(data=reading_data)
            serializer.is_valid(raise_exception=True)
            readings.append(serializer.save())
        return readings


class AggregatedReadingSerializer(serializers.ModelSerializer):
    """Serializer for AggregatedReading model."""
    
    sensor_name = serializers.CharField(
        source='sensor.name',
        read_only=True
    )

    class Meta:
        model = AggregatedReading
        fields = [
            'id',
            'sensor',
            'sensor_name',
            'hour',
            'temp_min',
            'temp_max',
            'temp_avg',
            'humidity_min',
            'humidity_max',
            'humidity_avg',
            'reading_count',
        ]


class LatestReadingSerializer(serializers.Serializer):
    """Serializer for latest reading response."""
    
    sensor_id = serializers.UUIDField()
    sensor_name = serializers.CharField()
    room_name = serializers.CharField()
    temperature = serializers.FloatField(allow_null=True)
    humidity = serializers.FloatField(allow_null=True)
    timestamp = serializers.DateTimeField()
    is_online = serializers.BooleanField()


