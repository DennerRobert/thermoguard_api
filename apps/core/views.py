"""
Core views for ThermoGuard IoT API.

This module provides views for dashboard, health checks, and data centers.
"""
import logging
from datetime import timedelta
from typing import Any

from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import get_success_response
from apps.core.models import DataCenter, Room
from apps.core.serializers import (
    DashboardRoomSerializer,
    DashboardSerializer,
    DataCenterCreateSerializer,
    DataCenterSerializer,
    RoomCreateSerializer,
    RoomSerializer,
    RoomSettingsSerializer,
    StatisticsSerializer,
)

logger = logging.getLogger('thermoguard')


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.
    
    Returns basic system health information.
    """
    
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Return health status.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response with health status.
        """
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
        })


class DataCenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataCenter CRUD operations.
    
    Provides list, retrieve, create, update, and delete operations.
    """
    
    queryset = DataCenter.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DataCenterCreateSerializer
        return DataCenterSerializer

    def list(self, request: Request) -> Response:
        """List all data centers."""
        queryset = self.get_queryset()
        
        # Filter by active status if specified
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        serializer = self.get_serializer(queryset, many=True)
        return get_success_response(serializer.data)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve a specific data center."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return get_success_response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new data center."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        output_serializer = DataCenterSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Data Center criado com sucesso.',
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request: Request, pk: str = None) -> Response:
        """Update a data center."""
        instance = self.get_object()
        serializer = DataCenterSerializer(
            instance,
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return get_success_response(
            serializer.data,
            message='Data Center atualizado com sucesso.'
        )

    def partial_update(self, request: Request, pk: str = None) -> Response:
        """Partially update a data center."""
        instance = self.get_object()
        serializer = DataCenterSerializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return get_success_response(
            serializer.data,
            message='Data Center atualizado com sucesso.'
        )

    def destroy(self, request: Request, pk: str = None) -> Response:
        """Delete a data center."""
        instance = self.get_object()
        instance.delete()
        
        return get_success_response(
            message='Data Center removido com sucesso.',
            status_code=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def rooms(self, request: Request, pk: str = None) -> Response:
        """List all rooms in a data center."""
        instance = self.get_object()
        rooms = instance.rooms.all()
        serializer = RoomSerializer(rooms, many=True)
        return get_success_response(serializer.data)


class DashboardView(APIView):
    """
    Main dashboard view.
    
    Provides system-wide overview including all rooms and their status.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Return dashboard data.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response with dashboard data.
        """
        from apps.alerts.models import Alert
        from apps.devices.models import AirConditioner
        from apps.sensors.models import Sensor, SensorReading
        
        # Get counts
        total_datacenters = DataCenter.objects.filter(is_active=True).count()
        total_rooms = Room.objects.filter(is_active=True).count()
        total_sensors = Sensor.objects.count()
        sensors_online = Sensor.objects.filter(is_online=True).count()
        total_ac_units = AirConditioner.objects.filter(is_active=True).count()
        ac_units_on = AirConditioner.objects.filter(
            is_active=True,
            status='on'
        ).count()
        
        # Get alerts
        active_alerts = Alert.objects.filter(is_acknowledged=False).count()
        critical_alerts = Alert.objects.filter(
            is_acknowledged=False,
            severity='critical'
        ).count()
        
        # Get room data
        rooms_data = []
        rooms = Room.objects.filter(is_active=True).select_related('data_center')
        
        for room in rooms:
            # Get latest reading
            latest_reading = SensorReading.objects.filter(
                sensor__room=room
            ).order_by('-timestamp').first()
            
            room_data = {
                'id': room.id,
                'name': room.name,
                'data_center_name': room.data_center.name,
                'target_temperature': room.target_temperature,
                'target_humidity': room.target_humidity,
                'current_temperature': (
                    latest_reading.temperature if latest_reading else None
                ),
                'current_humidity': (
                    latest_reading.humidity if latest_reading else None
                ),
                'operation_mode': room.operation_mode,
                'is_active': room.is_active,
                'sensors_online': Sensor.objects.filter(
                    room=room,
                    is_online=True
                ).count(),
                'sensors_total': Sensor.objects.filter(room=room).count(),
                'ac_units_on': AirConditioner.objects.filter(
                    room=room,
                    status='on'
                ).count(),
                'ac_units_total': AirConditioner.objects.filter(room=room).count(),
                'active_alerts': Alert.objects.filter(
                    room=room,
                    is_acknowledged=False
                ).count(),
                'last_reading_at': (
                    latest_reading.timestamp if latest_reading else None
                ),
            }
            rooms_data.append(room_data)
        
        dashboard_data = {
            'total_datacenters': total_datacenters,
            'total_rooms': total_rooms,
            'total_sensors': total_sensors,
            'sensors_online': sensors_online,
            'total_ac_units': total_ac_units,
            'ac_units_on': ac_units_on,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'rooms': rooms_data,
        }
        
        serializer = DashboardSerializer(dashboard_data)
        return get_success_response(serializer.data)


class RoomDashboardView(APIView):
    """
    Room-specific dashboard view.
    
    Provides detailed information about a specific room.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, room_id: str) -> Response:
        """
        Return room dashboard data.
        
        Args:
            request: The incoming request.
            room_id: The room ID.
            
        Returns:
            Response with room dashboard data.
        """
        from apps.alerts.models import Alert
        from apps.devices.models import AirConditioner
        from apps.sensors.models import Sensor, SensorReading
        
        try:
            room = Room.objects.select_related('data_center').get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Sala não encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sensors
        sensors = Sensor.objects.filter(room=room)
        sensors_data = []
        
        for sensor in sensors:
            latest = SensorReading.objects.filter(
                sensor=sensor
            ).order_by('-timestamp').first()
            
            sensors_data.append({
                'id': sensor.id,
                'name': sensor.name,
                'device_id': sensor.device_id,
                'is_online': sensor.is_online,
                'last_seen': sensor.last_seen,
                'current_temperature': latest.temperature if latest else None,
                'current_humidity': latest.humidity if latest else None,
            })
        
        # Get air conditioners
        ac_units = AirConditioner.objects.filter(room=room)
        ac_data = [{
            'id': ac.id,
            'name': ac.name,
            'status': ac.status,
            'is_active': ac.is_active,
            'last_command': ac.last_command,
        } for ac in ac_units]
        
        # Get recent alerts
        alerts = Alert.objects.filter(
            room=room
        ).order_by('-created_at')[:10]
        alerts_data = [{
            'id': alert.id,
            'type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'is_acknowledged': alert.is_acknowledged,
            'created_at': alert.created_at,
        } for alert in alerts]
        
        # Get 24h temperature history
        history_start = timezone.now() - timedelta(hours=24)
        readings = SensorReading.objects.filter(
            sensor__room=room,
            timestamp__gte=history_start
        ).order_by('timestamp').values(
            'timestamp', 'temperature', 'humidity'
        )
        
        response_data = {
            'room': RoomSerializer(room).data,
            'sensors': sensors_data,
            'air_conditioners': ac_data,
            'recent_alerts': alerts_data,
            'temperature_history': list(readings),
        }
        
        return get_success_response(response_data)


class ReportsView(APIView):
    """
    Reports and statistics view.
    
    Provides temperature history and statistics.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Return temperature history.
        
        Query params:
            room_id: Filter by room
            period: 'day', 'week', 'month'
            
        Args:
            request: The incoming request.
            
        Returns:
            Response with temperature history.
        """
        from apps.sensors.models import SensorReading
        
        room_id = request.query_params.get('room_id')
        period = request.query_params.get('period', 'day')
        
        # Calculate time range
        now = timezone.now()
        if period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'month':
            start_time = now - timedelta(days=30)
        else:  # day
            start_time = now - timedelta(hours=24)
        
        # Build query
        queryset = SensorReading.objects.filter(
            timestamp__gte=start_time
        )
        
        if room_id:
            queryset = queryset.filter(sensor__room_id=room_id)
        
        # Get readings
        readings = queryset.order_by('timestamp').values(
            'timestamp',
            'temperature',
            'humidity',
            'sensor__room__name',
            'sensor__room_id'
        )
        
        return get_success_response({
            'period': period,
            'start_time': start_time,
            'end_time': now,
            'readings': list(readings),
        })


class StatisticsView(APIView):
    """
    Statistics view.
    
    Provides min, max, avg statistics for temperature and humidity.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Return statistics.
        
        Query params:
            room_id: Filter by room (required)
            period: 'day', 'week', 'month'
            
        Args:
            request: The incoming request.
            
        Returns:
            Response with statistics.
        """
        from apps.sensors.models import SensorReading
        
        room_id = request.query_params.get('room_id')
        period = request.query_params.get('period', 'day')
        
        if not room_id:
            return Response(
                {'success': False, 'error': 'room_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Sala não encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate time range
        now = timezone.now()
        if period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'month':
            start_time = now - timedelta(days=30)
        else:  # day
            start_time = now - timedelta(hours=24)
        
        # Get statistics
        stats = SensorReading.objects.filter(
            sensor__room=room,
            timestamp__gte=start_time
        ).aggregate(
            temp_min=Min('temperature'),
            temp_max=Max('temperature'),
            temp_avg=Avg('temperature'),
            humidity_min=Min('humidity'),
            humidity_max=Max('humidity'),
            humidity_avg=Avg('humidity'),
            reading_count=Count('id'),
        )
        
        response_data = {
            'room_id': str(room.id),
            'room_name': room.name,
            'period_start': start_time,
            'period_end': now,
            'temperature': {
                'min': stats['temp_min'],
                'max': stats['temp_max'],
                'avg': round(stats['temp_avg'], 2) if stats['temp_avg'] else None,
            },
            'humidity': {
                'min': stats['humidity_min'],
                'max': stats['humidity_max'],
                'avg': round(stats['humidity_avg'], 2) if stats['humidity_avg'] else None,
            },
            'reading_count': stats['reading_count'],
        }
        
        return get_success_response(response_data)


