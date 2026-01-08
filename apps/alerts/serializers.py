"""
Serializers for alert models.

This module provides serializers for alerts.
"""
from rest_framework import serializers

from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """
    Serializer for Alert model.
    
    Includes room information and display values.
    """
    
    room_name = serializers.CharField(
        source='room.name',
        read_only=True
    )
    data_center_name = serializers.CharField(
        source='room.data_center.name',
        read_only=True
    )
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    acknowledged_by_email = serializers.CharField(
        source='acknowledged_by.email',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'room',
            'room_name',
            'data_center_name',
            'alert_type',
            'alert_type_display',
            'severity',
            'severity_display',
            'message',
            'is_acknowledged',
            'acknowledged_by',
            'acknowledged_by_email',
            'acknowledged_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'room',
            'alert_type',
            'severity',
            'message',
            'acknowledged_by',
            'acknowledged_at',
            'created_at',
            'updated_at',
        ]


class AlertListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Alert listing.
    """
    
    room_name = serializers.CharField(
        source='room.name',
        read_only=True
    )
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'room',
            'room_name',
            'alert_type',
            'alert_type_display',
            'severity',
            'severity_display',
            'message',
            'is_acknowledged',
            'created_at',
        ]


class AlertAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging alerts."""
    
    notes = serializers.CharField(
        required=False,
        max_length=500,
        allow_blank=True
    )


class AlertSummarySerializer(serializers.Serializer):
    """Serializer for alert summary."""
    
    total = serializers.IntegerField()
    unacknowledged = serializers.IntegerField()
    critical = serializers.IntegerField()
    warning = serializers.IntegerField()
    info = serializers.IntegerField()


