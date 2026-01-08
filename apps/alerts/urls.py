"""Alerts URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.alerts.views import AlertViewSet

app_name = 'alerts'

router = DefaultRouter()
router.register('', AlertViewSet, basename='alerts')

urlpatterns = [
    path('', include(router.urls)),
]


