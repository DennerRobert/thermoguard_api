"""
Custom authentication classes for ThermoGuard IoT API.

This module provides authentication for ESP32 devices via API Key.
"""
import logging
from typing import Any

from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework.request import Request

logger = logging.getLogger('thermoguard')


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication for ESP32 devices.
    
    Devices authenticate using X-API-Key header with a shared secret.
    This is simpler than JWT for IoT devices with limited resources.
    """
    
    keyword = 'X-API-Key'
    
    def authenticate(self, request: Request) -> tuple[Any, str] | None:
        """
        Authenticate the request using API Key.
        
        Args:
            request: The incoming request.
            
        Returns:
            Tuple of (None, api_key) if authenticated, None otherwise.
            
        Raises:
            AuthenticationFailed: If API key is invalid.
        """
        api_key = request.headers.get(self.keyword)
        
        if not api_key:
            return None
        
        expected_key = settings.THERMOGUARD.get('ESP32_API_KEY')
        
        if not expected_key:
            logger.error("ESP32_API_KEY not configured in settings")
            return None
        
        if api_key != expected_key:
            logger.warning(
                f"Invalid API key attempt from {request.META.get('REMOTE_ADDR')}"
            )
            raise exceptions.AuthenticationFailed(
                'Chave de API inválida.'
            )
        
        logger.debug(
            f"API key authenticated from {request.META.get('REMOTE_ADDR')}"
        )
        
        # Return None for user since this is device authentication
        # The API key itself is returned as the auth object
        return (None, api_key)

    def authenticate_header(self, request: Request) -> str:
        """
        Return the authentication header for 401 responses.
        
        Args:
            request: The incoming request.
            
        Returns:
            The authentication header value.
        """
        return self.keyword


class DeviceAPIKeyPermission:
    """
    Permission class for device API key authentication.
    
    Allows access if the request was authenticated via API key.
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        """
        Check if the request has API key permission.
        
        Args:
            request: The incoming request.
            view: The view being accessed.
            
        Returns:
            True if authenticated via API key.
        """
        return (
            request.auth is not None and 
            isinstance(request.auth, str)
        )


