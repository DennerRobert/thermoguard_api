"""
Custom permissions for ThermoGuard IoT API.

This module provides permission classes for access control.
"""
from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.users.models import User


class IsAdminUser(BasePermission):
    """
    Permission that only allows admin users.
    
    Checks if the user has admin role or is superuser.
    """
    
    message = 'Acesso restrito a administradores.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user has admin permission.
        
        Args:
            request: The incoming request.
            view: The view being accessed.
            
        Returns:
            True if user is admin.
        """
        user = request.user
        return (
            user and
            user.is_authenticated and
            (user.role == User.Role.ADMIN or user.is_superuser)
        )


class IsOperatorUser(BasePermission):
    """
    Permission that allows operators and admins.
    
    Checks if the user has operator or admin role.
    """
    
    message = 'Acesso restrito a operadores e administradores.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user has operator permission.
        
        Args:
            request: The incoming request.
            view: The view being accessed.
            
        Returns:
            True if user is operator or admin.
        """
        user = request.user
        return (
            user and
            user.is_authenticated and
            (
                user.role in [User.Role.ADMIN, User.Role.OPERATOR] or
                user.is_superuser
            )
        )


class CanControlDevices(BasePermission):
    """
    Permission for device control operations.
    
    Only operators and admins can control devices.
    """
    
    message = 'Você não tem permissão para controlar dispositivos.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user can control devices.
        
        Args:
            request: The incoming request.
            view: The view being accessed.
            
        Returns:
            True if user can control devices.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        return user.can_control_devices()


class ReadOnly(BasePermission):
    """
    Permission that allows read-only access.
    
    Only allows GET, HEAD, and OPTIONS requests.
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if request is read-only.
        
        Args:
            request: The incoming request.
            view: The view being accessed.
            
        Returns:
            True if request method is safe.
        """
        return request.method in ('GET', 'HEAD', 'OPTIONS')


