"""
Serializers for user authentication and management.

This module provides serializers for JWT authentication and user CRUD.
"""
from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes user info in response.
    
    Extends the default JWT token serializer to include additional
    user information in the token claims and response.
    """

    @classmethod
    def get_token(cls, user: User) -> RefreshToken:
        """
        Get token with custom claims.
        
        Args:
            user: The user to create token for.
            
        Returns:
            RefreshToken with custom claims.
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        
        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate credentials and return token data.
        
        Args:
            attrs: The input attributes (email, password).
            
        Returns:
            Dictionary with tokens and user info.
        """
        data = super().validate(attrs)
        
        # Add user info to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
        }
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Provides read-only access to user information.
    """
    
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_display',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    
    Includes password validation and confirmation.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that passwords match.
        
        Args:
            attrs: The input attributes.
            
        Returns:
            Validated attributes.
            
        Raises:
            ValidationError: If passwords don't match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            validated_data: The validated input data.
            
        Returns:
            The created user.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'role',
            'is_active',
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    current_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value: str) -> str:
        """
        Validate current password.
        
        Args:
            value: The current password.
            
        Returns:
            The validated password.
            
        Raises:
            ValidationError: If password is incorrect.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that new passwords match.
        
        Args:
            attrs: The input attributes.
            
        Returns:
            Validated attributes.
            
        Raises:
            ValidationError: If passwords don't match.
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'As senhas não coincidem.'
            })
        return attrs

    def save(self) -> User:
        """
        Save the new password.
        
        Returns:
            The updated user.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login request documentation."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response documentation."""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


