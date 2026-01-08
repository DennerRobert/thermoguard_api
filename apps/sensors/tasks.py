"""
Celery tasks for sensor operations.

This module contains background tasks for sensor management.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone

logger = logging.getLogger('thermoguard')


@shared_task
def check_sensor_status() -> dict:
    """
    Check status of all sensors.
    
    Marks sensors as offline if not seen recently and creates alerts.
    
    Returns:
        Dictionary with task results.
    """
    from apps.sensors.services import SensorService
    
    logger.info("Running sensor status check...")
    
    SensorService.check_all_sensor_status()
    
    return {'status': 'completed'}


@shared_task
def cleanup_old_readings() -> dict:
    """
    Clean up old sensor readings.
    
    Removes readings older than the retention period.
    
    Returns:
        Dictionary with deletion count.
    """
    from apps.sensors.models import SensorReading
    
    retention_days = settings.THERMOGUARD.get('DATA_RETENTION_DAYS', 30)
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    logger.info(f"Cleaning readings older than {cutoff_date}...")
    
    # Delete old readings
    deleted_count, _ = SensorReading.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old readings")
    
    return {'deleted_count': deleted_count}


@shared_task
def aggregate_readings() -> dict:
    """
    Aggregate old readings into hourly summaries.
    
    Creates aggregated readings for data older than the aggregation threshold.
    
    Returns:
        Dictionary with aggregation count.
    """
    from apps.sensors.models import AggregatedReading, Sensor, SensorReading
    
    aggregation_hours = settings.THERMOGUARD.get('READING_AGGREGATION_HOURS', 24)
    cutoff_time = timezone.now() - timedelta(hours=aggregation_hours)
    
    logger.info(f"Aggregating readings older than {cutoff_time}...")
    
    aggregated_count = 0
    
    for sensor in Sensor.objects.all():
        # Get readings to aggregate (by hour)
        readings = SensorReading.objects.filter(
            sensor=sensor,
            timestamp__lt=cutoff_time
        )
        
        if not readings.exists():
            continue
        
        # Group by hour
        from django.db.models.functions import TruncHour
        
        hourly_stats = readings.annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            temp_min=Min('temperature'),
            temp_max=Max('temperature'),
            temp_avg=Avg('temperature'),
            humidity_min=Min('humidity'),
            humidity_max=Max('humidity'),
            humidity_avg=Avg('humidity'),
            reading_count=Count('id'),
        )
        
        for stats in hourly_stats:
            # Create or update aggregated reading
            AggregatedReading.objects.update_or_create(
                sensor=sensor,
                hour=stats['hour'],
                defaults={
                    'temp_min': stats['temp_min'],
                    'temp_max': stats['temp_max'],
                    'temp_avg': stats['temp_avg'],
                    'humidity_min': stats['humidity_min'],
                    'humidity_max': stats['humidity_max'],
                    'humidity_avg': stats['humidity_avg'],
                    'reading_count': stats['reading_count'],
                }
            )
            aggregated_count += 1
        
        # Delete aggregated readings (keep only the aggregated ones)
        readings.delete()
    
    logger.info(f"Created {aggregated_count} aggregated readings")
    
    return {'aggregated_count': aggregated_count}


@shared_task
def generate_daily_report() -> dict:
    """
    Generate daily statistics report.
    
    Creates a summary of all readings for the past 24 hours.
    
    Returns:
        Dictionary with report data.
    """
    from apps.core.models import Room
    from apps.sensors.models import SensorReading
    
    yesterday = timezone.now() - timedelta(days=1)
    
    report = []
    
    for room in Room.objects.filter(is_active=True):
        stats = SensorReading.objects.filter(
            sensor__room=room,
            timestamp__gte=yesterday
        ).aggregate(
            temp_min=Min('temperature'),
            temp_max=Max('temperature'),
            temp_avg=Avg('temperature'),
            humidity_min=Min('humidity'),
            humidity_max=Max('humidity'),
            humidity_avg=Avg('humidity'),
            reading_count=Count('id'),
        )
        
        report.append({
            'room_id': str(room.id),
            'room_name': room.name,
            'stats': stats,
        })
    
    logger.info(f"Generated daily report for {len(report)} rooms")
    
    return {'rooms': report}


