"""
API endpoint tests for ThermoGuard IoT API.

This module contains integration tests for all API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.alerts.models import Alert
from apps.sensors.models import SensorReading


class TestAuthenticationAPI:
    """Tests for authentication endpoints."""

    def test_login_success(self, api_client, admin_user, user_password):
        """Test successful login."""
        response = api_client.post('/api/auth/login/', {
            'email': admin_user.email,
            'password': user_password,
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']
        assert 'user' in response.data['data']

    def test_login_invalid_credentials(self, api_client, admin_user):
        """Test login with invalid credentials."""
        response = api_client.post('/api/auth/login/', {
            'email': admin_user.email,
            'password': 'wrong_password',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, admin_user):
        """Test token refresh."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(admin_user)
        response = api_client.post('/api/auth/refresh/', {
            'refresh': str(refresh),
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']

    def test_logout(self, authenticated_client, admin_user):
        """Test logout."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(admin_user)
        response = authenticated_client.post('/api/auth/logout/', {
            'refresh': str(refresh),
        })
        assert response.status_code == status.HTTP_200_OK

    def test_protected_endpoint_without_auth(self, api_client):
        """Test accessing protected endpoint without authentication."""
        response = api_client.get('/api/dashboard/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDashboardAPI:
    """Tests for dashboard endpoints."""

    def test_dashboard_main(self, authenticated_client, room, sensor):
        """Test main dashboard endpoint."""
        response = authenticated_client.get('/api/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_rooms' in response.data['data']
        assert 'rooms' in response.data['data']

    def test_dashboard_room(self, authenticated_client, room, sensor):
        """Test room dashboard endpoint."""
        response = authenticated_client.get(f'/api/dashboard/rooms/{room.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'room' in response.data['data']
        assert 'sensors' in response.data['data']


class TestSensorAPI:
    """Tests for sensor endpoints."""

    def test_list_sensors(self, authenticated_client, sensor):
        """Test listing sensors."""
        response = authenticated_client.get('/api/sensors/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1

    def test_get_sensor(self, authenticated_client, sensor):
        """Test getting a specific sensor."""
        response = authenticated_client.get(f'/api/sensors/{sensor.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['device_id'] == sensor.device_id

    def test_create_sensor(self, authenticated_client, room):
        """Test creating a sensor."""
        response = authenticated_client.post('/api/sensors/', {
            'room': str(room.id),
            'device_id': 'AA:BB:CC:11:22:33',
            'name': 'New Sensor',
            'sensor_type': 'both',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'New Sensor'

    def test_submit_reading_with_api_key(self, api_key_client, sensor, sample_reading_data):
        """Test submitting a reading with API key."""
        response = api_key_client.post(
            f'/api/sensors/{sensor.id}/readings/',
            sample_reading_data,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert SensorReading.objects.filter(sensor=sensor).count() == 1

    def test_get_sensor_readings(self, authenticated_client, sensor):
        """Test getting sensor readings."""
        # Create some readings
        SensorReading.objects.create(
            sensor=sensor,
            temperature=24.0,
            humidity=50.0,
        )
        
        response = authenticated_client.get(f'/api/sensors/{sensor.id}/readings/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1

    def test_get_latest_reading(self, authenticated_client, sensor):
        """Test getting latest reading."""
        SensorReading.objects.create(
            sensor=sensor,
            temperature=24.0,
            humidity=50.0,
        )
        
        response = authenticated_client.get(f'/api/sensors/{sensor.id}/readings/latest/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['temperature'] == 24.0


class TestAirConditionerAPI:
    """Tests for air conditioner endpoints."""

    def test_list_air_conditioners(self, authenticated_client, air_conditioner):
        """Test listing air conditioners."""
        response = authenticated_client.get('/api/air-conditioners/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1

    def test_turn_on_ac(self, operator_client, air_conditioner):
        """Test turning on an AC."""
        response = operator_client.post(
            f'/api/air-conditioners/{air_conditioner.id}/turn_on/'
        )
        assert response.status_code == status.HTTP_200_OK
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'on'

    def test_turn_off_ac(self, operator_client, air_conditioner):
        """Test turning off an AC."""
        air_conditioner.status = 'on'
        air_conditioner.save()
        
        response = operator_client.post(
            f'/api/air-conditioners/{air_conditioner.id}/turn_off/'
        )
        assert response.status_code == status.HTTP_200_OK
        air_conditioner.refresh_from_db()
        assert air_conditioner.status == 'off'

    def test_viewer_cannot_control_ac(self, viewer_client, air_conditioner):
        """Test that viewer cannot control AC."""
        response = viewer_client.post(
            f'/api/air-conditioners/{air_conditioner.id}/turn_on/'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAlertAPI:
    """Tests for alert endpoints."""

    def test_list_alerts(self, authenticated_client, room):
        """Test listing alerts."""
        Alert.objects.create(
            room=room,
            alert_type='high_temp',
            severity='warning',
            message='Test alert',
        )
        
        response = authenticated_client.get('/api/alerts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1

    def test_acknowledge_alert(self, authenticated_client, room):
        """Test acknowledging an alert."""
        alert = Alert.objects.create(
            room=room,
            alert_type='high_temp',
            severity='warning',
            message='Test alert',
        )
        
        response = authenticated_client.patch(
            f'/api/alerts/{alert.id}/acknowledge/'
        )
        assert response.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.is_acknowledged is True

    def test_alert_summary(self, authenticated_client, room):
        """Test alert summary."""
        Alert.objects.create(
            room=room,
            alert_type='high_temp',
            severity='critical',
            message='Critical!',
        )
        
        response = authenticated_client.get('/api/alerts/summary/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['critical'] == 1


class TestReportsAPI:
    """Tests for reports endpoints."""

    def test_temperature_history(self, authenticated_client, sensor):
        """Test temperature history endpoint."""
        SensorReading.objects.create(
            sensor=sensor,
            temperature=24.0,
            humidity=50.0,
        )
        
        response = authenticated_client.get('/api/reports/temperature-history/')
        assert response.status_code == status.HTTP_200_OK
        assert 'readings' in response.data['data']

    def test_statistics(self, authenticated_client, sensor, room):
        """Test statistics endpoint."""
        SensorReading.objects.create(
            sensor=sensor,
            temperature=24.0,
            humidity=50.0,
        )
        
        response = authenticated_client.get(
            f'/api/reports/statistics/?room_id={room.id}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'temperature' in response.data['data']


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, api_client):
        """Test health check endpoint."""
        response = api_client.get('/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'


