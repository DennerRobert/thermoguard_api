"""Air conditioners URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.devices.views import (
    AirConditionerViewSet,
    IRSignalReceiveView,
    TurnOffAllACView,
)

app_name = 'air_conditioners'

router = DefaultRouter()
router.register('', AirConditionerViewSet, basename='air-conditioners')

urlpatterns = [
    # Turn off all ACs
    path('turn-off-all/', TurnOffAllACView.as_view(), name='turn-off-all'),
    
    # IR signal reception from ESP32
    path(
        '<uuid:ac_id>/ir-signal/',
        IRSignalReceiveView.as_view(),
        name='ir-signal-receive'
    ),
    
    # AC CRUD and control
    path('', include(router.urls)),
]


