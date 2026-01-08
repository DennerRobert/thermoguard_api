"""
Serializer tests for ThermoGuard IoT API.

This module contains unit tests for serializers.
"""
import pytest
from rest_framework.exceptions import ValidationError

from apps.core.serializers import RoomCreateSerializer, RoomSettingsSerializer
from apps.sensors.serializers import SensorCreateSerializer, SensorReadingCreateSerializer
from apps.users.serializers import UserCreateSerializer


class TestUserCreateSerializer:
    """Tests for UserCreateSerializer."""

    def test_valid_data(self, db):
        """Test serializer with valid data."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'operator',
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self, db):
        """Test serializer with password mismatch."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'DifferentPassword!',
            'first_name': 'Test',
            'last_name': 'User',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors


class TestRoomCreateSerializer:
    """Tests for RoomCreateSerializer."""

    def test_valid_data(self, data_center):
        """Test serializer with valid data."""
        data = {
            'data_center': str(data_center.id),
            'name': 'Test Room',
            'target_temperature': 22.0,
            'target_humidity': 50.0,
        }
        serializer = RoomCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_temperature_too_low(self, data_center):
        """Test serializer with temperature too low."""
        data = {
            'data_center': str(data_center.id),
            'name': 'Test Room',
            'target_temperature': 10.0,  # Too low
            'target_humidity': 50.0,
        }
        serializer = RoomCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'target_temperature' in serializer.errors

    def test_invalid_temperature_too_high(self, data_center):
        """Test serializer with temperature too high."""
        data = {
            'data_center': str(data_center.id),
            'name': 'Test Room',
            'target_temperature': 35.0,  # Too high
            'target_humidity': 50.0,
        }
        serializer = RoomCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'target_temperature' in serializer.errors


class TestSensorReadingCreateSerializer:
    """Tests for SensorReadingCreateSerializer."""

    def test_valid_data_with_device_id(self, sensor):
        """Test serializer with valid data using device_id."""
        data = {
            'device_id': sensor.device_id,
            'temperature': 24.5,
            'humidity': 55.0,
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_valid_data_with_sensor_id(self, sensor):
        """Test serializer with valid data using sensor_id."""
        data = {
            'sensor_id': str(sensor.id),
            'temperature': 24.5,
            'humidity': 55.0,
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_identifier(self):
        """Test serializer without device_id or sensor_id."""
        data = {
            'temperature': 24.5,
            'humidity': 55.0,
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert not serializer.is_valid()

    def test_missing_readings(self, sensor):
        """Test serializer without temperature or humidity."""
        data = {
            'device_id': sensor.device_id,
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert not serializer.is_valid()

    def test_invalid_temperature_range(self, sensor):
        """Test serializer with invalid temperature."""
        data = {
            'device_id': sensor.device_id,
            'temperature': 100.0,  # Invalid
            'humidity': 55.0,
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'temperature' in serializer.errors

    def test_invalid_humidity_range(self, sensor):
        """Test serializer with invalid humidity."""
        data = {
            'device_id': sensor.device_id,
            'temperature': 24.5,
            'humidity': 150.0,  # Invalid
        }
        serializer = SensorReadingCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'humidity' in serializer.errors


