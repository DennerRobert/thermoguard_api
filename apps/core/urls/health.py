"""Health check URL configuration."""
from django.urls import path

from apps.core.views import HealthCheckView

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='check'),
]


