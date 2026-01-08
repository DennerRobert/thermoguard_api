"""DataCenter URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.views import DataCenterViewSet

app_name = 'datacenters'

router = DefaultRouter()
router.register('', DataCenterViewSet, basename='datacenter')

urlpatterns = [
    path('', include(router.urls)),
]


