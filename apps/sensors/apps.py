"""Sensors application configuration."""
from django.apps import AppConfig


class SensorsConfig(AppConfig):
    """Configuration for the sensors application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sensors'
    verbose_name = 'Sensores'

    def ready(self) -> None:
        """Run when the application is ready."""
        from apps.sensors import signals  # noqa: F401


