"""
Custom exceptions and exception handling for ThermoGuard IoT API.

This module provides centralized exception handling and custom exception classes.
"""
import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('thermoguard')


class ThermoGuardException(APIException):
    """Base exception for ThermoGuard API."""
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Ocorreu um erro interno no servidor.'
    default_code = 'server_error'


class DeviceOfflineException(ThermoGuardException):
    """Exception raised when a device is offline."""
    
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'O dispositivo está offline.'
    default_code = 'device_offline'


class DeviceCommandException(ThermoGuardException):
    """Exception raised when a device command fails."""
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Falha ao executar comando no dispositivo.'
    default_code = 'command_failed'


class SensorNotFoundException(ThermoGuardException):
    """Exception raised when a sensor is not found."""
    
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Sensor não encontrado.'
    default_code = 'sensor_not_found'


class RoomNotFoundException(ThermoGuardException):
    """Exception raised when a room is not found."""
    
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Sala não encontrada.'
    default_code = 'room_not_found'


class InvalidAPIKeyException(ThermoGuardException):
    """Exception raised when an API key is invalid."""
    
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Chave de API inválida.'
    default_code = 'invalid_api_key'


class RateLimitExceededException(ThermoGuardException):
    """Exception raised when rate limit is exceeded."""
    
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Limite de requisições excedido. Tente novamente mais tarde.'
    default_code = 'rate_limit_exceeded'


class InvalidReadingException(ThermoGuardException):
    """Exception raised when a sensor reading is invalid."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Leitura de sensor inválida.'
    default_code = 'invalid_reading'


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any]
) -> Response | None:
    """
    Custom exception handler for DRF.
    
    Provides consistent error response format and logging.
    
    Args:
        exc: The exception that was raised.
        context: Context information about the request.
        
    Returns:
        Response object with error details or None.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request info for logging
    request = context.get('request')
    view = context.get('view')
    
    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.messages)
        response = exception_handler(exc, context)
    
    if response is not None:
        # Build custom error response
        error_data = {
            'success': False,
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                'status_code': response.status_code,
            }
        }
        
        # Add field errors for validation errors
        if isinstance(exc, ValidationError) and isinstance(exc.detail, dict):
            error_data['error']['fields'] = exc.detail
        
        # Log the error
        log_message = (
            f"API Error: {error_data['error']['code']} - "
            f"{error_data['error']['message']}"
        )
        
        if request:
            log_message += f" | Path: {request.path} | Method: {request.method}"
        
        if response.status_code >= 500:
            logger.error(log_message, exc_info=True)
        elif response.status_code >= 400:
            logger.warning(log_message)
        
        response.data = error_data
    else:
        # Handle unexpected exceptions
        logger.exception(
            f"Unhandled exception in {view.__class__.__name__ if view else 'unknown'}: {exc}"
        )
        
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': 'Ocorreu um erro interno no servidor.',
                    'status_code': 500,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def get_error_response(
    message: str,
    code: str = 'error',
    status_code: int = 400,
    fields: dict | None = None
) -> Response:
    """
    Helper function to create standardized error responses.
    
    Args:
        message: Error message.
        code: Error code.
        status_code: HTTP status code.
        fields: Field-specific errors.
        
    Returns:
        Response object with error details.
    """
    error_data = {
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'status_code': status_code,
        }
    }
    
    if fields:
        error_data['error']['fields'] = fields
    
    return Response(error_data, status=status_code)


def get_success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200
) -> Response:
    """
    Helper function to create standardized success responses.
    
    Args:
        data: Response data.
        message: Success message.
        status_code: HTTP status code.
        
    Returns:
        Response object with success data.
    """
    response_data = {
        'success': True,
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    return Response(response_data, status=status_code)


