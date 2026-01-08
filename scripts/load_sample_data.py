#!/usr/bin/env python
"""
Script to load sample data into the database.

Usage:
    python scripts/load_sample_data.py
    
Or with Docker:
    docker-compose exec api python scripts/load_sample_data.py
"""
import os
import sys
from datetime import timedelta
import random

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.core.models import DataCenter, Room
from apps.sensors.models import Sensor, SensorReading
from apps.devices.models import AirConditioner
from apps.alerts.models import Alert

User = get_user_model()


def create_sample_data():
    """Create sample data for development and testing."""
    print('Creating sample data...')
    
    # Create Data Center
    dc, created = DataCenter.objects.get_or_create(
        name='Data Center Principal',
        defaults={
            'location': 'São Paulo, SP - Tech Tower, Piso 5',
        }
    )
    print(f'Data Center: {dc.name} ({"created" if created else "exists"})')
    
    # Create Rooms
    room1, created = Room.objects.get_or_create(
        data_center=dc,
        name='Sala de Servidores A',
        defaults={
            'description': 'Sala principal com servidores de produção',
            'target_temperature': 22.0,
            'target_humidity': 50.0,
            'operation_mode': Room.OperationMode.AUTOMATIC,
        }
    )
    print(f'Room: {room1.name} ({"created" if created else "exists"})')
    
    room2, created = Room.objects.get_or_create(
        data_center=dc,
        name='Sala de Servidores B',
        defaults={
            'description': 'Sala secundária',
            'target_temperature': 23.0,
            'target_humidity': 55.0,
            'operation_mode': Room.OperationMode.MANUAL,
        }
    )
    print(f'Room: {room2.name} ({"created" if created else "exists"})')
    
    # Create Sensors
    for i, room in enumerate([room1, room2], 1):
        for j in range(1, 3):
            sensor, created = Sensor.objects.get_or_create(
                device_id=f'AA:BB:CC:DD:{i:02X}:{j:02X}',
                defaults={
                    'room': room,
                    'name': f'Sensor Rack {j}',
                    'sensor_type': Sensor.SensorType.BOTH,
                    'is_online': True,
                    'last_seen': timezone.now(),
                }
            )
            print(f'Sensor: {sensor.name} ({"created" if created else "exists"})')
            
            # Create sample readings
            if created:
                now = timezone.now()
                for hours_ago in range(24):
                    for minutes in [0, 15, 30, 45]:
                        timestamp = now - timedelta(hours=hours_ago, minutes=minutes)
                        SensorReading.objects.create(
                            sensor=sensor,
                            temperature=22.0 + random.uniform(-2, 3),
                            humidity=50.0 + random.uniform(-5, 10),
                            timestamp=timestamp,
                        )
    
    print('Sample readings created')
    
    # Create Air Conditioners
    for i, room in enumerate([room1, room2], 1):
        for j in range(1, 3):
            ac, created = AirConditioner.objects.get_or_create(
                room=room,
                name=f'AC Precisão {j}',
                defaults={
                    'status': AirConditioner.Status.ON if j == 1 else AirConditioner.Status.OFF,
                    'is_active': True,
                    'ir_code': {
                        'power_on': '0x1234ABCD',
                        'power_off': '0x1234DCBA',
                    },
                    'esp32_device_id': f'FF:EE:DD:CC:{i:02X}:{j:02X}',
                }
            )
            print(f'AC: {ac.name} ({"created" if created else "exists"})')
    
    # Create sample alerts
    alert, created = Alert.objects.get_or_create(
        room=room1,
        alert_type=Alert.AlertType.HIGH_TEMP,
        is_acknowledged=False,
        defaults={
            'severity': Alert.Severity.WARNING,
            'message': 'Temperatura acima do setpoint: 24.5°C (limite: 23°C)',
        }
    )
    print(f'Alert: {alert.alert_type} ({"created" if created else "exists"})')
    
    # Create sample users
    users_data = [
        ('admin@thermoguard.local', 'Admin', 'User', User.Role.ADMIN),
        ('operator@thermoguard.local', 'Operator', 'User', User.Role.OPERATOR),
        ('viewer@thermoguard.local', 'Viewer', 'User', User.Role.VIEWER),
    ]
    
    for email, first, last, role in users_data:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first,
                'last_name': last,
                'role': role,
                'is_active': True,
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        print(f'User: {email} ({"created" if created else "exists"})')
    
    print('\nSample data created successfully!')
    print('\nDefault users:')
    print('  admin@thermoguard.local / password123 (Admin)')
    print('  operator@thermoguard.local / password123 (Operator)')
    print('  viewer@thermoguard.local / password123 (Viewer)')


if __name__ == '__main__':
    create_sample_data()


