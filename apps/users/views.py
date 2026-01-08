"""
Views for user authentication and management.

This module provides views for JWT authentication and user CRUD operations.
"""
import logging
from typing import Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.exceptions import get_error_response, get_success_response
from apps.users.models import User
from apps.users.permissions import IsAdminUser
from apps.users.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

logger = logging.getLogger('thermoguard')


class LoginView(TokenObtainPairView):
    """
    User login view.
    
    Authenticates user and returns JWT tokens.
    """
    
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Authenticate user and return tokens.
        
        Args:
            request: The incoming request.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
            
        Returns:
            Response with JWT tokens and user info.
        """
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        logger.info(f"User logged in: {serializer.validated_data['user']['email']}")
        
        return get_success_response(
            serializer.validated_data,
            message='Login realizado com sucesso.'
        )


class RefreshTokenView(TokenRefreshView):
    """
    Token refresh view.
    
    Refreshes an expired access token using the refresh token.
    """
    
    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Refresh the access token.
        
        Args:
            request: The incoming request.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
            
        Returns:
            Response with new JWT tokens.
        """
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        return get_success_response(
            serializer.validated_data,
            message='Token atualizado com sucesso.'
        )


class LogoutView(APIView):
    """
    User logout view.
    
    Blacklists the refresh token to prevent further use.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Logout user by blacklisting refresh token.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response confirming logout.
        """
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return get_error_response(
                    'Refresh token é obrigatório.',
                    code='missing_token',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User logged out: {request.user.email}")
            
            return get_success_response(
                message='Logout realizado com sucesso.'
            )
        except TokenError:
            return get_error_response(
                'Token inválido ou já expirado.',
                code='invalid_token',
                status_code=status.HTTP_400_BAD_REQUEST
            )


class CurrentUserView(APIView):
    """
    Current user view.
    
    Returns information about the authenticated user.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get current user information.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response with user information.
        """
        serializer = UserSerializer(request.user)
        return get_success_response(serializer.data)

    def patch(self, request: Request) -> Response:
        """
        Update current user information.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response with updated user information.
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = UserSerializer(request.user)
        return get_success_response(
            output_serializer.data,
            message='Perfil atualizado com sucesso.'
        )


class PasswordChangeView(APIView):
    """
    Password change view.
    
    Allows authenticated users to change their password.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Change user password.
        
        Args:
            request: The incoming request.
            
        Returns:
            Response confirming password change.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"Password changed for user: {request.user.email}")
        
        return get_success_response(
            message='Senha alterada com sucesso.'
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    
    Allows admins to create, update, and delete users.
    """
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def list(self, request: Request) -> Response:
        """List all users."""
        queryset = self.get_queryset()
        
        # Filter by role
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return get_success_response(serializer.data)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve a specific user."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return get_success_response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        logger.info(
            f"User created: {user.email} by {request.user.email}"
        )
        
        output_serializer = UserSerializer(user)
        return get_success_response(
            output_serializer.data,
            message='Usuário criado com sucesso.',
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request: Request, pk: str = None) -> Response:
        """Update a user."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(
            f"User updated: {instance.email} by {request.user.email}"
        )
        
        output_serializer = UserSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Usuário atualizado com sucesso.'
        )

    def partial_update(self, request: Request, pk: str = None) -> Response:
        """Partially update a user."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = UserSerializer(instance)
        return get_success_response(
            output_serializer.data,
            message='Usuário atualizado com sucesso.'
        )

    def destroy(self, request: Request, pk: str = None) -> Response:
        """Delete a user."""
        instance = self.get_object()
        
        # Prevent self-deletion
        if instance == request.user:
            return get_error_response(
                'Você não pode excluir sua própria conta.',
                code='self_deletion',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        logger.warning(
            f"User deleted: {instance.email} by {request.user.email}"
        )
        
        instance.delete()
        
        return get_success_response(
            message='Usuário removido com sucesso.'
        )

    @action(detail=True, methods=['post'])
    def reset_password(self, request: Request, pk: str = None) -> Response:
        """
        Reset user password (admin only).
        
        Args:
            request: The incoming request.
            pk: The user ID.
            
        Returns:
            Response with new temporary password.
        """
        instance = self.get_object()
        
        new_password = request.data.get('new_password')
        if not new_password:
            return get_error_response(
                'Nova senha é obrigatória.',
                code='missing_password',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        instance.set_password(new_password)
        instance.save()
        
        logger.info(
            f"Password reset for user: {instance.email} by {request.user.email}"
        )
        
        return get_success_response(
            message='Senha redefinida com sucesso.'
        )


