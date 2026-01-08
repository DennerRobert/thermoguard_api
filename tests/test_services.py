"""
Service tests for ThermoGuard IoT API.

This module contains unit tests for business logic services.
"""
import pytest
from unittest.mock import patch, MagicMock

from apps.alerts.models import Alert
from apps.alerts.services import AlertService
from apps.devices.services import AirConditionerService
from apps.sensors.services import SensorService
from apps.sensors.models import SensorReading


class TestAlertService:
    """Tests for AlertService."""

    def test_create_alert(self, room):
        """Test creating an alert."""
        alert = AlertService.create_alert(
            room=room,
            alert_type='high_temp',
            severity='warning',
            message='Test alert message',
        )
        
        assert alert is not None
        assert alert.room == room
        assert alert.alert_type == 'high_temp'

    def test_duplicate_alert_not_created(self, room):
        """Test that duplicate alerts are not created."""
        # Create first alert
        alert1 = AlertService.create_alert(
            room=room,
            alert_type='high_temp',
            severity='warning',
            message='First alert',
        )
        
        # Try to create duplicate
        alert2 = AlertService.create_alert(
            room=room,
            alert_type='high_temp',
            severity='warning',
            message='Second alert',
        )
        
        assert alert1 is not None
        assert alert2 is None  # Should be skipped
        assert Alert.objects.count() == 1

    def test_get_active_alerts_count(self, room):
        """Test getting active alerts count."""
        Alert.objects.create(
            room=room,
            alert_type='high_temp',
            severity='critical',
            message='Critical',
        )
        Alert.objects.create(
            room=room,
            alert_type='sensor_offline',
            severity='warning',
            message='Warning',
        )
        
        counts = AlertService.get_active_alerts_count()
        
        assert counts['total'] == 2
        assert counts['critical'] == 1
        assert counts['warning'] == 1


class TestSensorService:
    """Tests for SensorService."""

    def test_get_room_average_readings(self, room, sensor):
        """Test getting room average readings."""
        sensor.is_online = True
        sensor.save()
        
        SensorReading.objects.create(
            sensor=sensor,
            temperature=24.0,
            humidity=50.0,
        )
        
        averages = SensorService.get_room_average_readings(str(room.id))
        
        assert averages['temperature'] == 24.0
        assert averages['humidity'] == 50.0

    @patch('apps.sensors.services.async_to_sync')
    def test_process_new_reading_creates_alert(self, mock_async, sensor, room):
        """Test that processing reading creates alert for high temp."""
        room.target_temperature = 20.0
        room.save()
        
        reading = SensorReading.objects.create(
            sensor=sensor,
            temperature=28.0,  # 8 degrees above setpoint
            humidity=50.0,
        )
        
        SensorService.process_new_reading(reading)
        
        # Should have created a critical alert
        alerts = Alert.objects.filter(room=room, alert_type='high_temp')
        assert alerts.exists()


class TestAirConditionerService:
    """Tests for AirConditionerService."""

    @patch('apps.devices.services.async_to_sync')
    def test_turn_on_ac(self, mock_async, air_conditioner, admin_user):
        """Test turning on an AC."""
        result = AirConditionerService.turn_on(air_conditioner, admin_user)
        
        assert result is True
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'on'

    @patch('apps.devices.services.async_to_sync')
    def test_turn_off_ac(self, mock_async, air_conditioner, admin_user):
        """Test turning off an AC."""
        air_conditioner.status = 'on'
        air_conditioner.save()
        
        result = AirConditionerService.turn_off(air_conditioner, admin_user)
        
        assert result is True
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'off'

    def test_auto_turn_on_ac(self, room, air_conditioner):
        """Test automatic AC turn on."""
        with patch.object(AirConditionerService, 'send_ir_command', return_value=True):
            result = AirConditionerService.auto_turn_on_ac(room)
        
        assert result is True
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'on'

    def test_auto_turn_off_ac(self, room, air_conditioner):
        """Test automatic AC turn off."""
        air_conditioner.status = 'on'
        air_conditioner.save()
        
        with patch.object(AirConditionerService, 'send_ir_command', return_value=True):
            result = AirConditionerService.auto_turn_off_ac(room)
        
        assert result is True
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'off'


