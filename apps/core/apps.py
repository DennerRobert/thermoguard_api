"""Core application configuration."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'ThermoGuard Core'

    def ready(self) -> None:
        """Run when the application is ready."""
        # Import signals
        from apps.core import signals  # noqa: F401


