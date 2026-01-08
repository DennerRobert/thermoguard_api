"""
Serializers for device models.

This module provides serializers for air conditioners and related models.
"""
from typing import Any

from rest_framework import serializers

from apps.devices.models import AirConditioner, CommandLog, IRSignal


class AirConditionerSerializer(serializers.ModelSerializer):
    """
    Serializer for AirConditioner model.
    
    Includes room information and IR code status.
    """
    
    room_name = serializers.CharField(
        source='room.name',
        read_only=True
    )
    data_center_name = serializers.CharField(
        source='room.data_center.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    has_ir_codes = serializers.BooleanField(read_only=True)

    class Meta:
        model = AirConditioner
        fields = [
            'id',
            'room',
            'room_name',
            'data_center_name',
            'name',
            'status',
            'status_display',
            'is_active',
            'has_ir_codes',
            'esp32_device_id',
            'last_command',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'last_command',
            'created_at',
            'updated_at',
        ]


class AirConditionerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating air conditioners."""
    
    class Meta:
        model = AirConditioner
        fields = [
            'room',
            'name',
            'is_active',
            'esp32_device_id',
        ]


class AirConditionerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating air conditioners."""
    
    class Meta:
        model = AirConditioner
        fields = [
            'room',
            'name',
            'is_active',
            'esp32_device_id',
        ]


class IRSignalSerializer(serializers.ModelSerializer):
    """
    Serializer for IRSignal model.
    """
    
    command_type_display = serializers.CharField(
        source='get_command_type_display',
        read_only=True
    )

    class Meta:
        model = IRSignal
        fields = [
            'id',
            'air_conditioner',
            'command_type',
            'command_type_display',
            'raw_signal',
            'protocol',
            'description',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class IRSignalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/recording IR signals."""
    
    class Meta:
        model = IRSignal
        fields = [
            'command_type',
            'raw_signal',
            'protocol',
            'description',
        ]


class IRRecordRequestSerializer(serializers.Serializer):
    """Serializer for IR recording request."""
    
    command_type = serializers.ChoiceField(
        choices=IRSignal.CommandType.choices
    )


class IRRecordResponseSerializer(serializers.Serializer):
    """Serializer for IR recording response from ESP32."""
    
    command_type = serializers.CharField()
    raw_signal = serializers.CharField()
    protocol = serializers.CharField(required=False, default='')
    success = serializers.BooleanField()
    message = serializers.CharField(required=False, default='')


class CommandLogSerializer(serializers.ModelSerializer):
    """
    Serializer for CommandLog model.
    """
    
    air_conditioner_name = serializers.CharField(
        source='air_conditioner.name',
        read_only=True
    )
    executed_by_email = serializers.CharField(
        source='executed_by.email',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = CommandLog
        fields = [
            'id',
            'air_conditioner',
            'air_conditioner_name',
            'command',
            'executed_by',
            'executed_by_email',
            'success',
            'response',
            'automatic',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ACControlSerializer(serializers.Serializer):
    """Serializer for AC control commands."""
    
    command = serializers.ChoiceField(
        choices=[
            ('power_on', 'Ligar'),
            ('power_off', 'Desligar'),
            ('temp_up', 'Aumentar Temperatura'),
            ('temp_down', 'Diminuir Temperatura'),
        ]
    )


class ACStatusSerializer(serializers.Serializer):
    """Serializer for AC status response."""
    
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    last_command = serializers.DateTimeField(allow_null=True)
    message = serializers.CharField()


