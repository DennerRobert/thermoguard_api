"""
User models for ThermoGuard IoT API.

This module contains the custom User model with extended fields.
"""
import uuid
from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager for ThermoGuard users.
    
    Provides methods for creating regular and superusers.
    """
    
    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any
    ) -> 'User':
        """
        Create and return a regular user.
        
        Args:
            email: The user's email address.
            password: The user's password.
            **extra_fields: Additional fields.
            
        Returns:
            The created user.
            
        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError('O email é obrigatório.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any
    ) -> 'User':
        """
        Create and return a superuser.
        
        Args:
            email: The user's email address.
            password: The user's password.
            **extra_fields: Additional fields.
            
        Returns:
            The created superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for ThermoGuard.
    
    Uses email as the username field and includes role-based permissions.
    
    Attributes:
        id: UUID primary key.
        email: Unique email address (username).
        first_name: User's first name.
        last_name: User's last name.
        role: User role for permission management.
        is_active: Whether the user account is active.
        is_staff: Whether the user can access admin site.
        created_at: When the user was created.
        updated_at: When the user was last updated.
    """
    
    class Role(models.TextChoices):
        """User role choices."""
        ADMIN = 'admin', 'Administrador'
        OPERATOR = 'operator', 'Operador'
        VIEWER = 'viewer', 'Visualizador'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Nome'
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Sobrenome'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='Função'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Staff'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Return string representation."""
        return self.email

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_operator(self) -> bool:
        """Check if user is an operator or higher."""
        return self.role in [self.Role.ADMIN, self.Role.OPERATOR] or self.is_superuser

    def can_control_devices(self) -> bool:
        """Check if user can control devices."""
        return self.is_operator()

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.is_admin()


