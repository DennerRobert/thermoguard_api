"""
Admin configuration for alert models.

This module configures the Django admin interface for alert models.
"""
from django.contrib import admin

from apps.alerts.models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin configuration for Alert model."""
    
    list_display = [
        'alert_type',
        'severity',
        'room',
        'message',
        'is_acknowledged',
        'created_at',
    ]
    list_filter = [
        'severity',
        'alert_type',
        'is_acknowledged',
        'room__data_center',
        'room',
        'created_at',
    ]
    search_fields = ['message', 'room__name']
    ordering = ['-created_at']
    readonly_fields = [
        'id',
        'room',
        'alert_type',
        'severity',
        'message',
        'acknowledged_by',
        'acknowledged_at',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'
    
    actions = ['acknowledge_alerts']

    def acknowledge_alerts(self, request, queryset):
        """Bulk acknowledge selected alerts."""
        from django.utils import timezone
        
        count = queryset.filter(is_acknowledged=False).update(
            is_acknowledged=True,
            acknowledged_by=request.user,
            acknowledged_at=timezone.now(),
        )
        
        self.message_user(
            request,
            f'{count} alertas foram reconhecidos.'
        )
    
    acknowledge_alerts.short_description = 'Reconhecer alertas selecionados'


