"""
Model tests for ThermoGuard IoT API.

This module contains unit tests for all Django models.
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.alerts.models import Alert
from apps.core.models import DataCenter, Room
from apps.devices.models import AirConditioner, CommandLog, IRSignal
from apps.sensors.models import AggregatedReading, Sensor, SensorReading


class TestDataCenterModel:
    """Tests for DataCenter model."""

    def test_create_datacenter(self, db):
        """Test creating a data center."""
        dc = DataCenter.objects.create(
            name='Test DC',
            location='Test Location',
        )
        assert dc.id is not None
        assert dc.name == 'Test DC'
        assert dc.is_active is True

    def test_datacenter_str(self, data_center):
        """Test data center string representation."""
        assert str(data_center) == 'Test Data Center - Test Location, Building A'

    def test_datacenter_room_count(self, data_center, room):
        """Test room count property."""
        assert data_center.room_count == 1


class TestRoomModel:
    """Tests for Room model."""

    def test_create_room(self, data_center):
        """Test creating a room."""
        room = Room.objects.create(
            data_center=data_center,
            name='Test Room',
            target_temperature=23.0,
            target_humidity=55.0,
        )
        assert room.id is not None
        assert room.operation_mode == Room.OperationMode.MANUAL

    def test_room_str(self, room):
        """Test room string representation."""
        assert 'Server Room 1' in str(room)

    def test_room_unique_together(self, data_center, room):
        """Test room name is unique within data center."""
        with pytest.raises(Exception):
            Room.objects.create(
                data_center=data_center,
                name='Server Room 1',  # Same name
            )


class TestSensorModel:
    """Tests for Sensor model."""

    def test_create_sensor(self, room):
        """Test creating a sensor."""
        sensor = Sensor.objects.create(
            room=room,
            device_id='11:22:33:44:55:66',
            name='Test Sensor',
        )
        assert sensor.id is not None
        assert sensor.is_online is False

    def test_sensor_str(self, sensor):
        """Test sensor string representation."""
        assert 'Sensor 1' in str(sensor)
        assert 'AA:BB:CC:DD:EE:FF' in str(sensor)

    def test_sensor_device_id_unique(self, sensor, room):
        """Test device_id is unique."""
        with pytest.raises(Exception):
            Sensor.objects.create(
                room=room,
                device_id='AA:BB:CC:DD:EE:FF',  # Same device_id
                name='Another Sensor',
            )

    def test_mark_online(self, sensor):
        """Test marking sensor as online."""
        assert sensor.is_online is False
        sensor.mark_online()
        sensor.refresh_from_db()
        assert sensor.is_online is True
        assert sensor.last_seen is not None


class TestSensorReadingModel:
    """Tests for SensorReading model."""

    def test_create_reading(self, sensor):
        """Test creating a sensor reading."""
        reading = SensorReading.objects.create(
            sensor=sensor,
            temperature=25.0,
            humidity=60.0,
        )
        assert reading.id is not None
        assert reading.temperature == 25.0

    def test_reading_validation_temperature_range(self, sensor):
        """Test temperature range validation."""
        reading = SensorReading(
            sensor=sensor,
            temperature=100.0,  # Invalid
            humidity=50.0,
        )
        with pytest.raises(ValidationError):
            reading.full_clean()

    def test_reading_validation_humidity_range(self, sensor):
        """Test humidity range validation."""
        reading = SensorReading(
            sensor=sensor,
            temperature=25.0,
            humidity=150.0,  # Invalid
        )
        with pytest.raises(ValidationError):
            reading.full_clean()

    def test_reading_requires_at_least_one_value(self, sensor):
        """Test that at least one reading value is required."""
        reading = SensorReading(
            sensor=sensor,
            temperature=None,
            humidity=None,
        )
        with pytest.raises(ValidationError):
            reading.full_clean()


class TestAirConditionerModel:
    """Tests for AirConditioner model."""

    def test_create_air_conditioner(self, room):
        """Test creating an air conditioner."""
        ac = AirConditioner.objects.create(
            room=room,
            name='Test AC',
        )
        assert ac.id is not None
        assert ac.status == AirConditioner.Status.OFF

    def test_air_conditioner_str(self, air_conditioner):
        """Test air conditioner string representation."""
        assert 'AC Unit 1' in str(air_conditioner)

    def test_has_ir_codes(self, air_conditioner):
        """Test has_ir_codes property."""
        assert air_conditioner.has_ir_codes is False
        
        air_conditioner.ir_code = {'power_on': 'test_signal'}
        air_conditioner.save()
        assert air_conditioner.has_ir_codes is True


class TestAlertModel:
    """Tests for Alert model."""

    def test_create_alert(self, room):
        """Test creating an alert."""
        alert = Alert.objects.create(
            room=room,
            alert_type=Alert.AlertType.HIGH_TEMP,
            severity=Alert.Severity.WARNING,
            message='Temperature too high!',
        )
        assert alert.id is not None
        assert alert.is_acknowledged is False

    def test_acknowledge_alert(self, room, admin_user):
        """Test acknowledging an alert."""
        alert = Alert.objects.create(
            room=room,
            alert_type=Alert.AlertType.HIGH_TEMP,
            severity=Alert.Severity.CRITICAL,
            message='Critical temperature!',
        )
        
        alert.acknowledge(admin_user)
        alert.refresh_from_db()
        
        assert alert.is_acknowledged is True
        assert alert.acknowledged_by == admin_user
        assert alert.acknowledged_at is not None


