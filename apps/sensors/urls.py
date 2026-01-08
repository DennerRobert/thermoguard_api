"""Sensors URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sensors.views import (
    AllLatestReadingsView,
    BulkSensorReadingView,
    SensorReadingCreateView,
    SensorViewSet,
)

app_name = 'sensors'

router = DefaultRouter()
router.register('', SensorViewSet, basename='sensors')

urlpatterns = [
    # Readings submission (for ESP32)
    path(
        '<uuid:sensor_id>/readings/',
        SensorReadingCreateView.as_view(),
        name='sensor-readings-create'
    ),
    path(
        'readings/',
        SensorReadingCreateView.as_view(),
        name='readings-create'
    ),
    path(
        'readings/bulk/',
        BulkSensorReadingView.as_view(),
        name='readings-bulk'
    ),
    
    # Latest readings for all sensors
    path(
        'readings/latest/',
        AllLatestReadingsView.as_view(),
        name='readings-latest-all'
    ),
    
    # Sensor CRUD
    path('', include(router.urls)),
]


