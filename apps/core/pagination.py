"""
Pagination classes for ThermoGuard IoT API.

This module provides custom pagination for API responses.
"""
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination for API results.
    
    Provides consistent pagination with customizable page size.
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data: list[Any]) -> Response:
        """
        Return a paginated response with metadata.
        
        Args:
            data: The paginated data.
            
        Returns:
            Response with pagination metadata.
        """
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            }
        })


class LargeResultsPagination(PageNumberPagination):
    """
    Pagination for large result sets like sensor readings.
    
    Allows larger page sizes for data export.
    """
    
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data: list[Any]) -> Response:
        """
        Return a paginated response with metadata.
        
        Args:
            data: The paginated data.
            
        Returns:
            Response with pagination metadata.
        """
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            }
        })


class SensorReadingPagination(PageNumberPagination):
    """
    Specialized pagination for sensor readings.
    
    Optimized for time-series data retrieval.
    """
    
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

    def get_paginated_response(self, data: list[Any]) -> Response:
        """
        Return a paginated response with time range metadata.
        
        Args:
            data: The paginated data.
            
        Returns:
            Response with pagination and time range metadata.
        """
        response_data = {
            'success': True,
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            }
        }
        
        # Add time range if data exists
        if data:
            response_data['time_range'] = {
                'start': data[-1].get('timestamp') if isinstance(data[-1], dict) else None,
                'end': data[0].get('timestamp') if isinstance(data[0], dict) else None,
            }
        
        return Response(response_data)


