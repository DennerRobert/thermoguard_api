"""Reports URL configuration."""
from django.urls import path

from apps.core.views import ReportsView, StatisticsView

app_name = 'reports'

urlpatterns = [
    path('temperature-history/', ReportsView.as_view(), name='temperature-history'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
]


