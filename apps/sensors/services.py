"""
Sensor services for ThermoGuard IoT API.

This module contains business logic for sensor operations.
"""
import asyncio
import logging
from typing import Any

from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone

from apps.sensors.models import Sensor, SensorReading

logger = logging.getLogger('thermoguard')


class SensorService:
    """
    Service class for sensor operations.
    
    Provides methods for processing readings and managing sensor state.
    """

    @staticmethod
    def process_new_reading(reading: SensorReading) -> None:
        """
        Process a new sensor reading.
        
        Triggers alerts, automation, and WebSocket broadcasts.
        
        Args:
            reading: The new sensor reading.
        """
        sensor = reading.sensor
        room = sensor.room
        
        # Check for temperature alerts
        if reading.temperature is not None:
            SensorService._check_temperature_alerts(reading, room)
        
        # Check for humidity alerts
        if reading.humidity is not None:
            SensorService._check_humidity_alerts(reading, room)
        
        # Trigger automatic AC control if room is in automatic mode
        if room.operation_mode == 'automatic':
            SensorService._process_automatic_control(reading, room)
        
        # Broadcast reading via WebSocket
        SensorService._broadcast_reading(reading)

    @staticmethod
    def _check_temperature_alerts(reading: SensorReading, room: Any) -> None:
        """
        Check if temperature reading triggers alerts.
        
        Args:
            reading: The sensor reading.
            room: The room object.
        """
        from apps.alerts.services import AlertService
        
        temperature = reading.temperature
        target = room.target_temperature
        threshold = settings.THERMOGUARD.get('TEMPERATURE_CRITICAL_THRESHOLD', 5.0)
        
        # Critical high temperature
        if temperature > target + threshold:
            AlertService.create_alert(
                room=room,
                alert_type='high_temp',
                severity='critical',
                message=(
                    f'Temperatura crítica: {temperature:.1f}°C '
                    f'(limite: {target + threshold:.1f}°C)'
                )
            )
        # Warning high temperature
        elif temperature > target + 2:
            AlertService.create_alert(
                room=room,
                alert_type='high_temp',
                severity='warning',
                message=(
                    f'Temperatura elevada: {temperature:.1f}°C '
                    f'(setpoint: {target:.1f}°C)'
                )
            )
        # Low temperature warning
        elif temperature < target - 3:
            AlertService.create_alert(
                room=room,
                alert_type='low_temp',
                severity='warning',
                message=(
                    f'Temperatura baixa: {temperature:.1f}°C '
                    f'(setpoint: {target:.1f}°C)'
                )
            )

    @staticmethod
    def _check_humidity_alerts(reading: SensorReading, room: Any) -> None:
        """
        Check if humidity reading triggers alerts.
        
        Args:
            reading: The sensor reading.
            room: The room object.
        """
        from apps.alerts.services import AlertService
        
        humidity = reading.humidity
        target = room.target_humidity
        
        # High humidity
        if humidity > target + 15:
            AlertService.create_alert(
                room=room,
                alert_type='high_humidity',
                severity='warning',
                message=(
                    f'Umidade elevada: {humidity:.1f}% '
                    f'(limite: {target + 15:.1f}%)'
                )
            )

    @staticmethod
    def _process_automatic_control(reading: SensorReading, room: Any) -> None:
        """
        Process automatic AC control based on temperature.
        
        Args:
            reading: The sensor reading.
            room: The room object.
        """
        from apps.devices.services import AirConditionerService
        
        if reading.temperature is None:
            return
        
        temperature = reading.temperature
        target = room.target_temperature
        hysteresis = settings.THERMOGUARD.get('HYSTERESIS_THRESHOLD', 1.0)
        
        # Temperature above setpoint + hysteresis -> Turn on AC
        if temperature > target + hysteresis:
            AirConditionerService.auto_turn_on_ac(room)
        
        # Temperature below setpoint - hysteresis -> Turn off AC
        elif temperature < target - hysteresis:
            AirConditionerService.auto_turn_off_ac(room)

    @staticmethod
    def _broadcast_reading(reading: SensorReading) -> None:
        """
        Broadcast reading via WebSocket.
        
        Args:
            reading: The sensor reading.
        """
        from apps.core.consumers import broadcast_sensor_reading
        
        try:
            async_to_sync(broadcast_sensor_reading)(
                room_id=str(reading.sensor.room.id),
                sensor_id=str(reading.sensor.id),
                temperature=reading.temperature,
                humidity=reading.humidity,
                timestamp=reading.timestamp.isoformat(),
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast reading: {e}")

    @staticmethod
    def check_all_sensor_status() -> None:
        """
        Check and update status of all sensors.
        
        Marks sensors as offline if not seen recently.
        """
        from apps.alerts.services import AlertService
        
        threshold_minutes = settings.THERMOGUARD.get(
            'SENSOR_OFFLINE_THRESHOLD_MINUTES', 5
        )
        threshold_time = timezone.now() - timezone.timedelta(
            minutes=threshold_minutes
        )
        
        # Find sensors that went offline
        offline_sensors = Sensor.objects.filter(
            is_online=True,
            last_seen__lt=threshold_time
        )
        
        for sensor in offline_sensors:
            sensor.is_online = False
            sensor.save(update_fields=['is_online', 'updated_at'])
            
            # Create alert
            AlertService.create_alert(
                room=sensor.room,
                alert_type='sensor_offline',
                severity='warning',
                message=f'Sensor offline: {sensor.name} ({sensor.device_id})'
            )
            
            logger.warning(f"Sensor marked offline: {sensor.device_id}")

    @staticmethod
    def get_room_average_readings(room_id: str) -> dict[str, float | None]:
        """
        Get average readings for a room from all online sensors.
        
        Args:
            room_id: The room ID.
            
        Returns:
            Dictionary with average temperature and humidity.
        """
        from django.db.models import Avg
        
        # Get latest readings from online sensors in the room
        latest_readings = []
        sensors = Sensor.objects.filter(
            room_id=room_id,
            is_online=True
        )
        
        for sensor in sensors:
            latest = sensor.readings.first()
            if latest:
                latest_readings.append(latest)
        
        if not latest_readings:
            return {'temperature': None, 'humidity': None}
        
        # Calculate averages
        temps = [r.temperature for r in latest_readings if r.temperature]
        humidities = [r.humidity for r in latest_readings if r.humidity]
        
        return {
            'temperature': sum(temps) / len(temps) if temps else None,
            'humidity': sum(humidities) / len(humidities) if humidities else None,
        }


