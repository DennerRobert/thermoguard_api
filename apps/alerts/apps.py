"""Alerts application configuration."""
from django.apps import AppConfig


class AlertsConfig(AppConfig):
    """Configuration for the alerts application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.alerts'
    verbose_name = 'Alertas'

    def ready(self) -> None:
        """Run when the application is ready."""
        from apps.alerts import signals  # noqa: F401


