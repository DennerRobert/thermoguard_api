#!/usr/bin/env python
"""
Script to create a superuser non-interactively.

Usage:
    python scripts/create_superuser.py
    
Or with Docker:
    docker-compose exec api python scripts/create_superuser.py
"""
import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_superuser():
    """Create a superuser if it doesn't exist."""
    email = os.getenv('SUPERUSER_EMAIL', 'admin@thermoguard.local')
    password = os.getenv('SUPERUSER_PASSWORD', 'admin123')
    
    if User.objects.filter(email=email).exists():
        print(f'Superuser {email} already exists.')
        return
    
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name='Admin',
        last_name='ThermoGuard',
    )
    
    print(f'Superuser {email} created successfully.')


if __name__ == '__main__':
    create_superuser()


