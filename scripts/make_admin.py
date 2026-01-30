#!/usr/bin/env python
"""
Script para tornar um usuário admin/superuser.

Usage:
    python scripts/make_admin.py admin@admin.com
    
Ou com Docker:
    docker-compose exec api python scripts/make_admin.py admin@admin.com
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


def make_admin(email):
    """Tornar um usuário existente em admin/superuser."""
    try:
        user = User.objects.get(email=email)
        
        # Atualizar permissões
        user.is_staff = True
        user.is_superuser = True
        user.role = User.Role.ADMIN
        user.is_active = True
        user.save()
        
        print(f'✓ Sucesso! {email} agora tem permissões de admin/superuser')
        print(f'  - is_staff: {user.is_staff}')
        print(f'  - is_superuser: {user.is_superuser}')
        print(f'  - role: {user.role}')
        print(f'  - is_active: {user.is_active}')
        
    except User.DoesNotExist:
        print(f'✗ Erro: Usuário {email} não encontrado.')
        print('Certifique-se de que o usuário existe no banco de dados.')
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python scripts/make_admin.py <email>')
        print('Exemplo: python scripts/make_admin.py admin@admin.com')
        sys.exit(1)
    
    email = sys.argv[1]
    make_admin(email)
