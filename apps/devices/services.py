"""
Device services for ThermoGuard IoT API.

This module contains business logic for device operations.
"""
import logging
from typing import Any

from asgiref.sync import async_to_sync
from django.utils import timezone

from apps.devices.models import AirConditioner, CommandLog

logger = logging.getLogger('thermoguard')


class AirConditionerService:
    """
    Service class for air conditioner operations.
    
    Provides methods for controlling AC units and managing IR signals.
    """

    @staticmethod
    def turn_on(ac: AirConditioner, user: Any = None) -> bool:
        """
        Turn on an air conditioner.
        
        Args:
            ac: The air conditioner to turn on.
            user: The user executing the command (None for automatic).
            
        Returns:
            True if successful, False otherwise.
        """
        success = AirConditionerService.send_ir_command(ac, 'power_on')
        
        # Log the command
        CommandLog.objects.create(
            air_conditioner=ac,
            command='power_on',
            executed_by=user,
            success=success,
            response='OK' if success else 'Failed to send command',
            automatic=user is None,
        )
        
        if success:
            ac.status = AirConditioner.Status.ON
            ac.last_command = timezone.now()
            ac.save(update_fields=['status', 'last_command', 'updated_at'])
            
            # Broadcast status change
            AirConditionerService._broadcast_status_change(ac, user)
            
            logger.info(
                f"AC turned on: {ac.name} by {user.email if user else 'System'}"
            )
        else:
            logger.error(f"Failed to turn on AC: {ac.name}")
        
        return success

    @staticmethod
    def turn_off(ac: AirConditioner, user: Any = None) -> bool:
        """
        Turn off an air conditioner.
        
        Args:
            ac: The air conditioner to turn off.
            user: The user executing the command (None for automatic).
            
        Returns:
            True if successful, False otherwise.
        """
        success = AirConditionerService.send_ir_command(ac, 'power_off')
        
        # Log the command
        CommandLog.objects.create(
            air_conditioner=ac,
            command='power_off',
            executed_by=user,
            success=success,
            response='OK' if success else 'Failed to send command',
            automatic=user is None,
        )
        
        if success:
            ac.status = AirConditioner.Status.OFF
            ac.last_command = timezone.now()
            ac.save(update_fields=['status', 'last_command', 'updated_at'])
            
            # Broadcast status change
            AirConditionerService._broadcast_status_change(ac, user)
            
            logger.info(
                f"AC turned off: {ac.name} by {user.email if user else 'System'}"
            )
        else:
            logger.error(f"Failed to turn off AC: {ac.name}")
        
        return success

    @staticmethod
    def send_ir_command(ac: AirConditioner, command_type: str) -> bool:
        """
        Send IR command to ESP32.
        
        Args:
            ac: The air conditioner to control.
            command_type: The type of command to send.
            
        Returns:
            True if successful, False otherwise.
        """
        # Check if AC has the required IR code
        if not ac.ir_code or command_type not in ac.ir_code:
            logger.warning(
                f"No IR code for {command_type} on AC {ac.name}"
            )
            # For now, simulate success if no IR code is configured
            # In production, this would return False
            return True
        
        ir_signal = ac.ir_code[command_type]
        
        # TODO: Implement actual ESP32 communication
        # This would typically use MQTT or HTTP to send the command
        # to the ESP32 device identified by ac.esp32_device_id
        #
        # Example implementation:
        # try:
        #     response = requests.post(
        #         f"http://{esp32_ip}/ir/send",
        #         json={'signal': ir_signal},
        #         timeout=5
        #     )
        #     return response.status_code == 200
        # except Exception as e:
        #     logger.error(f"Failed to send IR command: {e}")
        #     return False
        
        logger.debug(f"IR command sent: {command_type} to {ac.name}")
        return True

    @staticmethod
    def start_ir_recording(ac: AirConditioner, command_type: str) -> bool:
        """
        Start IR recording mode on ESP32.
        
        Args:
            ac: The air conditioner to configure.
            command_type: The type of command to record.
            
        Returns:
            True if recording mode started, False otherwise.
        """
        # TODO: Implement actual ESP32 communication
        # This would send a command to the ESP32 to enter recording mode
        #
        # Example implementation:
        # try:
        #     response = requests.post(
        #         f"http://{esp32_ip}/ir/record",
        #         json={'command_type': command_type, 'ac_id': str(ac.id)},
        #         timeout=5
        #     )
        #     return response.status_code == 200
        # except Exception as e:
        #     logger.error(f"Failed to start IR recording: {e}")
        #     return False
        
        logger.info(f"IR recording started for {ac.name}: {command_type}")
        return True

    @staticmethod
    def auto_turn_on_ac(room: Any) -> bool:
        """
        Automatically turn on an AC in a room.
        
        Selects an available AC that is currently off.
        
        Args:
            room: The room that needs cooling.
            
        Returns:
            True if an AC was turned on, False otherwise.
        """
        # Find an available AC that is off
        ac = AirConditioner.objects.filter(
            room=room,
            is_active=True,
            status=AirConditioner.Status.OFF
        ).first()
        
        if ac:
            success = AirConditionerService.turn_on(ac, user=None)
            if success:
                logger.info(
                    f"Auto turn on: {ac.name} in {room.name}"
                )
            return success
        
        logger.debug(f"No available AC to turn on in {room.name}")
        return False

    @staticmethod
    def auto_turn_off_ac(room: Any) -> bool:
        """
        Automatically turn off an AC in a room.
        
        Selects an AC that is currently on.
        
        Args:
            room: The room that is cool enough.
            
        Returns:
            True if an AC was turned off, False otherwise.
        """
        # Find an AC that is on
        ac = AirConditioner.objects.filter(
            room=room,
            is_active=True,
            status=AirConditioner.Status.ON
        ).first()
        
        if ac:
            success = AirConditionerService.turn_off(ac, user=None)
            if success:
                logger.info(
                    f"Auto turn off: {ac.name} in {room.name}"
                )
            return success
        
        logger.debug(f"No AC to turn off in {room.name}")
        return False

    @staticmethod
    def _broadcast_status_change(ac: AirConditioner, user: Any = None) -> None:
        """
        Broadcast AC status change via WebSocket.
        
        Args:
            ac: The air conditioner that changed.
            user: The user who made the change (None for automatic).
        """
        from apps.core.consumers import broadcast_ac_status
        
        try:
            async_to_sync(broadcast_ac_status)(
                room_id=str(ac.room.id),
                ac_id=str(ac.id),
                status=ac.status,
                changed_by=user.email if user else 'Sistema',
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast AC status: {e}")


