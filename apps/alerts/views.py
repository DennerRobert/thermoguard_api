"""
Views for alert management.

This module provides views for listing and acknowledging alerts.
"""
import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.alerts.serializers import (
    AlertAcknowledgeSerializer,
    AlertListSerializer,
    AlertSerializer,
    AlertSummarySerializer,
)
from apps.core.exceptions import get_error_response, get_success_response

logger = logging.getLogger('thermoguard')


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Alert list and detail operations.
    
    Alerts are created automatically and can only be listed and acknowledged.
    """
    
    queryset = Alert.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AlertListSerializer
        return AlertSerializer

    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset().select_related(
            'room', 'room__data_center', 'acknowledged_by'
        )
        
        # Filter by room
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Filter by data center
        datacenter_id = self.request.query_params.get('datacenter_id')
        if datacenter_id:
            queryset = queryset.filter(room__data_center_id=datacenter_id)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by alert type
        alert_type = self.request.query_params.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by acknowledged status
        acknowledged = self.request.query_params.get('acknowledged')
        if acknowledged is not None:
            queryset = queryset.filter(
                is_acknowledged=acknowledged.lower() == 'true'
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset

    def list(self, request: Request) -> Response:
        """List alerts with pagination."""
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return get_success_response(serializer.data)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve a specific alert."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return get_success_response(serializer.data)

    @action(detail=True, methods=['patch'])
    def acknowledge(self, request: Request, pk: str = None) -> Response:
        """
        Acknowledge an alert.
        
        Marks the alert as acknowledged by the current user.
        """
        alert = self.get_object()
        
        if alert.is_acknowledged:
            return get_error_response(
                'Este alerta já foi reconhecido.',
                code='already_acknowledged',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        alert.acknowledge(request.user)
        
        logger.info(
            f"Alert acknowledged: {alert.id} by {request.user.email}"
        )
        
        serializer = AlertSerializer(alert)
        return get_success_response(
            serializer.data,
            message='Alerta reconhecido com sucesso.'
        )

    @action(detail=False, methods=['get'])
    def summary(self, request: Request) -> Response:
        """
        Get alert summary.
        
        Returns counts by severity and acknowledgement status.
        """
        queryset = self.get_queryset()
        
        total = queryset.count()
        unacknowledged = queryset.filter(is_acknowledged=False).count()
        critical = queryset.filter(
            is_acknowledged=False,
            severity=Alert.Severity.CRITICAL
        ).count()
        warning = queryset.filter(
            is_acknowledged=False,
            severity=Alert.Severity.WARNING
        ).count()
        info = queryset.filter(
            is_acknowledged=False,
            severity=Alert.Severity.INFO
        ).count()
        
        data = {
            'total': total,
            'unacknowledged': unacknowledged,
            'critical': critical,
            'warning': warning,
            'info': info,
        }
        
        return get_success_response(data)

    @action(detail=False, methods=['post'])
    def acknowledge_all(self, request: Request) -> Response:
        """
        Acknowledge all unacknowledged alerts.
        
        Optionally filter by room_id or severity.
        """
        room_id = request.data.get('room_id')
        severity = request.data.get('severity')
        
        queryset = Alert.objects.filter(is_acknowledged=False)
        
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        count = queryset.count()
        
        now = timezone.now()
        queryset.update(
            is_acknowledged=True,
            acknowledged_by=request.user,
            acknowledged_at=now,
            updated_at=now,
        )
        
        logger.info(
            f"{count} alerts acknowledged by {request.user.email}"
        )
        
        return get_success_response(
            {'count': count},
            message=f'{count} alertas reconhecidos com sucesso.'
        )

    @action(detail=False, methods=['get'])
    def recent(self, request: Request) -> Response:
        """
        Get recent alerts (last 24 hours).
        
        Returns unacknowledged alerts from the last 24 hours.
        """
        since = timezone.now() - timedelta(hours=24)
        
        queryset = Alert.objects.filter(
            created_at__gte=since,
            is_acknowledged=False
        ).select_related(
            'room', 'room__data_center'
        ).order_by('-created_at')[:20]
        
        serializer = AlertListSerializer(queryset, many=True)
        return get_success_response(serializer.data)


