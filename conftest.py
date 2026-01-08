"""
Pytest configuration and fixtures for ThermoGuard IoT API.

This module provides shared fixtures for all test modules.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import DataCenter, Room
from apps.devices.models import AirConditioner
from apps.sensors.models import Sensor

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user_password():
    """Return a test password."""
    return 'TestPassword123!'


@pytest.fixture
def admin_user(db, user_password):
    """Create and return an admin user."""
    return User.objects.create_user(
        email='admin@thermoguard.local',
        password=user_password,
        first_name='Admin',
        last_name='User',
        role=User.Role.ADMIN,
    )


@pytest.fixture
def operator_user(db, user_password):
    """Create and return an operator user."""
    return User.objects.create_user(
        email='operator@thermoguard.local',
        password=user_password,
        first_name='Operator',
        last_name='User',
        role=User.Role.OPERATOR,
    )


@pytest.fixture
def viewer_user(db, user_password):
    """Create and return a viewer user."""
    return User.objects.create_user(
        email='viewer@thermoguard.local',
        password=user_password,
        first_name='Viewer',
        last_name='User',
        role=User.Role.VIEWER,
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def operator_client(api_client, operator_user):
    """Return an operator authenticated API client."""
    refresh = RefreshToken.for_user(operator_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def viewer_client(api_client, viewer_user):
    """Return a viewer authenticated API client."""
    refresh = RefreshToken.for_user(viewer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def api_key_client(api_client, settings):
    """Return an API key authenticated client (for ESP32)."""
    api_client.credentials(HTTP_X_API_KEY=settings.THERMOGUARD['ESP32_API_KEY'])
    return api_client


@pytest.fixture
def data_center(db):
    """Create and return a test data center."""
    return DataCenter.objects.create(
        name='Test Data Center',
        location='Test Location, Building A',
    )


@pytest.fixture
def room(db, data_center):
    """Create and return a test room."""
    return Room.objects.create(
        data_center=data_center,
        name='Server Room 1',
        description='Main server room',
        target_temperature=22.0,
        target_humidity=50.0,
        operation_mode=Room.OperationMode.MANUAL,
    )


@pytest.fixture
def sensor(db, room):
    """Create and return a test sensor."""
    return Sensor.objects.create(
        room=room,
        device_id='AA:BB:CC:DD:EE:FF',
        name='Sensor 1',
        sensor_type=Sensor.SensorType.BOTH,
    )


@pytest.fixture
def air_conditioner(db, room):
    """Create and return a test air conditioner."""
    return AirConditioner.objects.create(
        room=room,
        name='AC Unit 1',
        status=AirConditioner.Status.OFF,
        is_active=True,
    )


@pytest.fixture
def sample_reading_data():
    """Return sample sensor reading data."""
    return {
        'temperature': 24.5,
        'humidity': 55.0,
    }


