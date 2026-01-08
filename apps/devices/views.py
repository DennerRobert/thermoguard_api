"""
Views for device management.

This module provides views for air conditioner control and IR signal management.
"""
import logging
from typing import Any

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.authentication import APIKeyAuthentication, DeviceAPIKeyPermission
from apps.core.exceptions import get_error_response, get_success_response
from apps.core.models import Room
from apps.core.serializers import RoomSerializer, RoomSettingsSerializer
from apps.devices.models import AirConditioner, CommandLog, IRSignal
from apps.devices.serializers import (
    ACControlSerializer,
    AirConditionerCreateSerializer,
    AirConditionerSerializer,
    AirConditionerUpdateSerializer,
    CommandLogSerializer,
    IRRecordRequestSerializer,
    IRRecordResponseSerializer,
    IRSignalCreateSerializer,
    IRSignalSerializer,
)
from apps.devices.services import AirConditionerService
from apps.users.permissions import CanControlDevices

logger = logging.getLogger('thermoguard')


class AirConditionerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AirConditioner CRUD and control operations.
    """
    
    queryset = AirConditioner.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AirConditionerCreateSerializer
        if self.action in ['update', 'partial_update']:
            return AirConditionerUpdateSerializer
        return AirConditionerSerializer

    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset().select_related(
            'room', 'room__data_center'
        )
        
        # Filter by room
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Filter by status
        ac_status = self.request.query_params.get('status')
        if ac_status:
            queryset = queryset.filter(status=ac_status)
        
        # Filter by active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    def list(self, request: Request) -> Response:
        """List all air conditioners."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return get_success_response(serializer.data)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve a specific air conditioner."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return get_success_response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new air conditioner."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ac = serializer.save()
        
        logger.info(f"AC created: {ac.name} in {ac.room.name}")
        
        output_serializer = AirConditionerSerializer(ac)
        return get_success_response(
            output_serializer.data,
            message='Ar-condicionado criado com sucesso.',
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request: Request, pk: str = None) -> Response:
        """Update an air conditioner."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = AirConditionerSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Ar-condicionado atualizado com sucesso.'
        )

    def destroy(self, request: Request, pk: str = None) -> Response:
        """Delete an air conditioner."""
        instance = self.get_object()
        logger.warning(f"AC deleted: {instance.name}")
        instance.delete()
        
        return get_success_response(
            message='Ar-condicionado removido com sucesso.'
        )

    @action(detail=True, methods=['post'], permission_classes=[CanControlDevices])
    def turn_on(self, request: Request, pk: str = None) -> Response:
        """Turn on the air conditioner."""
        ac = self.get_object()
        
        success = AirConditionerService.turn_on(ac, request.user)
        
        if success:
            return get_success_response(
                {
                    'id': str(ac.id),
                    'name': ac.name,
                    'status': ac.status,
                    'last_command': ac.last_command.isoformat() if ac.last_command else None,
                },
                message=f'{ac.name} ligado com sucesso.'
            )
        else:
            return get_error_response(
                f'Falha ao ligar {ac.name}.',
                code='command_failed',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[CanControlDevices])
    def turn_off(self, request: Request, pk: str = None) -> Response:
        """Turn off the air conditioner."""
        ac = self.get_object()
        
        success = AirConditionerService.turn_off(ac, request.user)
        
        if success:
            return get_success_response(
                {
                    'id': str(ac.id),
                    'name': ac.name,
                    'status': ac.status,
                    'last_command': ac.last_command.isoformat() if ac.last_command else None,
                },
                message=f'{ac.name} desligado com sucesso.'
            )
        else:
            return get_error_response(
                f'Falha ao desligar {ac.name}.',
                code='command_failed',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[CanControlDevices])
    def toggle(self, request: Request, pk: str = None) -> Response:
        """Toggle the air conditioner on/off."""
        ac = self.get_object()
        
        if ac.status == AirConditioner.Status.ON:
            success = AirConditionerService.turn_off(ac, request.user)
            action_text = 'desligado'
        else:
            success = AirConditionerService.turn_on(ac, request.user)
            action_text = 'ligado'
        
        if success:
            return get_success_response(
                {
                    'id': str(ac.id),
                    'name': ac.name,
                    'status': ac.status,
                    'last_command': ac.last_command.isoformat() if ac.last_command else None,
                },
                message=f'{ac.name} {action_text} com sucesso.'
            )
        else:
            return get_error_response(
                f'Falha ao alternar {ac.name}.',
                code='command_failed',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def logs(self, request: Request, pk: str = None) -> Response:
        """Get command logs for this air conditioner."""
        ac = self.get_object()
        logs = ac.command_logs.all()[:50]  # Last 50 logs
        serializer = CommandLogSerializer(logs, many=True)
        return get_success_response(serializer.data)

    @action(detail=True, methods=['get'])
    def ir_signals(self, request: Request, pk: str = None) -> Response:
        """Get recorded IR signals for this air conditioner."""
        ac = self.get_object()
        signals = ac.ir_signals.all()
        serializer = IRSignalSerializer(signals, many=True)
        return get_success_response(serializer.data)

    @action(detail=True, methods=['post'], url_path='record-ir')
    def record_ir(self, request: Request, pk: str = None) -> Response:
        """
        Start IR signal recording mode.
        
        This triggers the ESP32 to enter recording mode.
        """
        ac = self.get_object()
        
        serializer = IRRecordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command_type = serializer.validated_data['command_type']
        
        success = AirConditionerService.start_ir_recording(ac, command_type)
        
        if success:
            return get_success_response(
                message=f'Modo de gravação iniciado. Aponte o controle remoto para o sensor e pressione o botão.',
                data={'command_type': command_type}
            )
        else:
            return get_error_response(
                'Falha ao iniciar modo de gravação.',
                code='recording_failed',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TurnOffAllACView(APIView):
    """
    View to turn off all air conditioners.
    
    Emergency endpoint to shut down all AC units.
    """
    
    permission_classes = [CanControlDevices]

    def post(self, request: Request) -> Response:
        """Turn off all air conditioners."""
        room_id = request.data.get('room_id')
        
        if room_id:
            acs = AirConditioner.objects.filter(
                room_id=room_id,
                is_active=True,
                status=AirConditioner.Status.ON
            )
        else:
            acs = AirConditioner.objects.filter(
                is_active=True,
                status=AirConditioner.Status.ON
            )
        
        results = []
        for ac in acs:
            success = AirConditionerService.turn_off(ac, request.user)
            results.append({
                'id': str(ac.id),
                'name': ac.name,
                'success': success,
            })
        
        logger.warning(
            f"Turn off all ACs executed by {request.user.email}: "
            f"{len(results)} units affected"
        )
        
        return get_success_response(
            {'results': results},
            message=f'{len(results)} ar-condicionados desligados.'
        )


class IRSignalReceiveView(APIView):
    """
    View for ESP32 to submit recorded IR signals.
    
    Called by ESP32 after recording an IR signal.
    """
    
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [DeviceAPIKeyPermission]

    def post(self, request: Request, ac_id: str) -> Response:
        """
        Receive recorded IR signal from ESP32.
        
        Args:
            request: The incoming request.
            ac_id: The air conditioner ID.
            
        Returns:
            Response confirming signal was saved.
        """
        try:
            ac = AirConditioner.objects.get(id=ac_id)
        except AirConditioner.DoesNotExist:
            return get_error_response(
                'Ar-condicionado não encontrado.',
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = IRRecordResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        if not data.get('success', True):
            return get_error_response(
                data.get('message', 'Falha na gravação do sinal IR.'),
                code='recording_failed',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Save or update IR signal
        ir_signal, created = IRSignal.objects.update_or_create(
            air_conditioner=ac,
            command_type=data['command_type'],
            defaults={
                'raw_signal': data['raw_signal'],
                'protocol': data.get('protocol', ''),
            }
        )
        
        # Update AC ir_code field
        if not ac.ir_code:
            ac.ir_code = {}
        ac.ir_code[data['command_type']] = data['raw_signal']
        ac.save(update_fields=['ir_code', 'updated_at'])
        
        logger.info(
            f"IR signal recorded for {ac.name}: {data['command_type']}"
        )
        
        return get_success_response(
            IRSignalSerializer(ir_signal).data,
            message='Sinal IR gravado com sucesso.'
        )


class RoomSettingsView(APIView):
    """
    View for room settings management.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, room_id: str) -> Response:
        """Get room settings."""
        try:
            room = Room.objects.select_related('data_center').get(id=room_id)
        except Room.DoesNotExist:
            return get_error_response(
                'Sala não encontrada.',
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RoomSerializer(room)
        return get_success_response(serializer.data)

    def patch(self, request: Request, room_id: str) -> Response:
        """Update room settings (setpoint, mode)."""
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return get_error_response(
                'Sala não encontrada.',
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RoomSettingsSerializer(
            room,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(
            f"Room settings updated: {room.name} by {request.user.email}"
        )
        
        output_serializer = RoomSerializer(room)
        return get_success_response(
            output_serializer.data,
            message='Configurações atualizadas com sucesso.'
        )


