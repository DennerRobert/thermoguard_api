"""Devices application configuration."""
from django.apps import AppConfig


class DevicesConfig(AppConfig):
    """Configuration for the devices application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.devices'
    verbose_name = 'Dispositivos'

    def ready(self) -> None:
        """Run when the application is ready."""
        from apps.devices import signals  # noqa: F401


