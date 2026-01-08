"""
URL Configuration for ThermoGuard IoT API.

This module defines all URL routes for the API, including:
- Authentication endpoints
- Dashboard endpoints
- Sensor management
- Device control
- Alert management
- API documentation
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API URL patterns
api_v1_patterns = [
    # Authentication
    path('auth/', include('apps.users.urls')),
    
    # Dashboard
    path('dashboard/', include('apps.core.urls.dashboard')),
    
    # Sensors
    path('sensors/', include('apps.sensors.urls')),
    
    # Devices (Air Conditioners)
    path('air-conditioners/', include('apps.devices.urls.air_conditioners')),
    path('rooms/', include('apps.devices.urls.rooms')),
    
    # Alerts
    path('alerts/', include('apps.alerts.urls')),
    
    # Reports
    path('reports/', include('apps.core.urls.reports')),
    
    # Data Centers
    path('datacenters/', include('apps.core.urls.datacenters')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/', include(api_v1_patterns)),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
    
    # Health Check
    path('health/', include('apps.core.urls.health')),
]


