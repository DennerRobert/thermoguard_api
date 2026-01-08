"""
Views for sensor management.

This module provides views for sensor CRUD and reading operations.
"""
import logging
from datetime import timedelta
from typing import Any

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.authentication import APIKeyAuthentication, DeviceAPIKeyPermission
from apps.core.exceptions import get_error_response, get_success_response
from apps.core.pagination import SensorReadingPagination
from apps.sensors.models import Sensor, SensorReading
from apps.sensors.serializers import (
    BulkSensorReadingSerializer,
    LatestReadingSerializer,
    SensorCreateSerializer,
    SensorReadingCreateSerializer,
    SensorReadingSerializer,
    SensorSerializer,
    SensorUpdateSerializer,
)
from apps.sensors.services import SensorService

logger = logging.getLogger('thermoguard')


class SensorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sensor CRUD operations.
    
    Provides list, retrieve, create, update, and delete operations.
    """
    
    queryset = Sensor.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return SensorCreateSerializer
        if self.action in ['update', 'partial_update']:
            return SensorUpdateSerializer
        return SensorSerializer

    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset().select_related(
            'room', 'room__data_center'
        )
        
        # Filter by room
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Filter by data center
        datacenter_id = self.request.query_params.get('datacenter_id')
        if datacenter_id:
            queryset = queryset.filter(room__data_center_id=datacenter_id)
        
        # Filter by online status
        is_online = self.request.query_params.get('is_online')
        if is_online is not None:
            queryset = queryset.filter(is_online=is_online.lower() == 'true')
        
        # Filter by sensor type
        sensor_type = self.request.query_params.get('sensor_type')
        if sensor_type:
            queryset = queryset.filter(sensor_type=sensor_type)
        
        return queryset

    def list(self, request: Request) -> Response:
        """List all sensors."""
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return get_success_response(serializer.data)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve a specific sensor."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return get_success_response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new sensor."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor = serializer.save()
        
        logger.info(f"Sensor created: {sensor.device_id}")
        
        output_serializer = SensorSerializer(sensor)
        return get_success_response(
            output_serializer.data,
            message='Sensor criado com sucesso.',
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request: Request, pk: str = None) -> Response:
        """Update a sensor."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = SensorSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Sensor atualizado com sucesso.'
        )

    def partial_update(self, request: Request, pk: str = None) -> Response:
        """Partially update a sensor."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = SensorSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Sensor atualizado com sucesso.'
        )

    def destroy(self, request: Request, pk: str = None) -> Response:
        """Delete a sensor."""
        instance = self.get_object()
        
        logger.warning(f"Sensor deleted: {instance.device_id}")
        
        instance.delete()
        
        return get_success_response(
            message='Sensor removido com sucesso.'
        )

    @action(detail=True, methods=['get'])
    def readings(self, request: Request, pk: str = None) -> Response:
        """
        Get readings for a specific sensor.
        
        Query params:
            start_date: Filter readings from this date
            end_date: Filter readings until this date
            limit: Limit number of readings
        """
        sensor = self.get_object()
        queryset = sensor.readings.all()
        
        # Date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Pagination
        paginator = SensorReadingPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = SensorReadingSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = SensorReadingSerializer(queryset, many=True)
        return get_success_response(serializer.data)

    @action(detail=True, methods=['get'], url_path='readings/latest')
    def latest_reading(self, request: Request, pk: str = None) -> Response:
        """Get the latest reading for a specific sensor."""
        sensor = self.get_object()
        latest = sensor.readings.first()
        
        if not latest:
            return get_error_response(
                'Nenhuma leitura encontrada para este sensor.',
                code='no_readings',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        data = {
            'sensor_id': sensor.id,
            'sensor_name': sensor.name,
            'room_name': sensor.room.name,
            'temperature': latest.temperature,
            'humidity': latest.humidity,
            'timestamp': latest.timestamp,
            'is_online': sensor.is_online,
        }
        
        return get_success_response(data)


class SensorReadingCreateView(APIView):
    """
    View for ESP32 to submit sensor readings.
    
    Supports both API key authentication (for devices) and
    JWT authentication (for testing/admin).
    """
    
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [DeviceAPIKeyPermission]
    throttle_scope = 'sensor'

    def post(self, request: Request, sensor_id: str = None) -> Response:
        """
        Create a new sensor reading.
        
        Args:
            request: The incoming request.
            sensor_id: Optional sensor ID from URL.
            
        Returns:
            Response with created reading.
        """
        data = request.data.copy()
        
        # If sensor_id is in URL, add to data
        if sensor_id:
            data['sensor_id'] = sensor_id
        
        serializer = SensorReadingCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reading = serializer.save()
            
            # Trigger async processing (alerts, automation)
            SensorService.process_new_reading(reading)
            
            logger.debug(
                f"Reading received from {reading.sensor.device_id}: "
                f"T={reading.temperature}°C, H={reading.humidity}%"
            )
            
            return get_success_response(
                SensorReadingSerializer(reading).data,
                message='Leitura registrada com sucesso.',
                status_code=status.HTTP_201_CREATED
            )
        except Sensor.DoesNotExist:
            return get_error_response(
                'Sensor não encontrado.',
                code='sensor_not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )


class BulkSensorReadingView(APIView):
    """
    View for ESP32 to submit multiple readings at once.
    
    Useful for batch uploads or when connectivity is intermittent.
    """
    
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [DeviceAPIKeyPermission]
    throttle_scope = 'sensor'

    def post(self, request: Request) -> Response:
        """
        Create multiple sensor readings.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response with created readings.
        """
        serializer = BulkSensorReadingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            readings = serializer.save()
            
            # Process each reading
            for reading in readings:
                SensorService.process_new_reading(reading)
            
            logger.info(f"Bulk upload: {len(readings)} readings received")
            
            return get_success_response(
                {'count': len(readings)},
                message=f'{len(readings)} leituras registradas com sucesso.',
                status_code=status.HTTP_201_CREATED
            )
        except Sensor.DoesNotExist:
            return get_error_response(
                'Um ou mais sensores não encontrados.',
                code='sensor_not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )


class AllLatestReadingsView(APIView):
    """
    View to get latest readings for all sensors.
    
    Useful for dashboard updates.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get latest readings for all sensors.
        
        Query params:
            room_id: Filter by room
            datacenter_id: Filter by data center
        """
        queryset = Sensor.objects.select_related('room', 'room__data_center')
        
        room_id = request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        datacenter_id = request.query_params.get('datacenter_id')
        if datacenter_id:
            queryset = queryset.filter(room__data_center_id=datacenter_id)
        
        readings_data = []
        for sensor in queryset:
            latest = sensor.readings.first()
            
            if latest:
                readings_data.append({
                    'sensor_id': str(sensor.id),
                    'sensor_name': sensor.name,
                    'room_name': sensor.room.name,
                    'room_id': str(sensor.room.id),
                    'temperature': latest.temperature,
                    'humidity': latest.humidity,
                    'timestamp': latest.timestamp.isoformat(),
                    'is_online': sensor.is_online,
                })
        
        return get_success_response(readings_data)


