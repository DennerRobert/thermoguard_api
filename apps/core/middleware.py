"""
Custom middleware for ThermoGuard IoT API.

This module contains middleware for request logging and exception handling.
"""
import logging
import time
import traceback
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger('thermoguard')


class RequestLoggingMiddleware:
    """
    Middleware for logging all API requests.
    
    Logs request details including method, path, duration, and status code.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request and log details.
        
        Args:
            request: The incoming HTTP request.
            
        Returns:
            The HTTP response.
        """
        # Skip logging for static files and health checks
        if self._should_skip_logging(request.path):
            return self.get_response(request)
        
        # Start timing
        start_time = time.time()
        
        # Get response
        response = self.get_response(request)
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get user info
        user = getattr(request, 'user', None)
        user_info = (
            str(user.id) if user and user.is_authenticated 
            else 'anonymous'
        )
        
        # Log request
        log_message = (
            f"{request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.2f}ms | "
            f"User: {user_info}"
        )
        
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return response

    def _should_skip_logging(self, path: str) -> bool:
        """
        Check if logging should be skipped for this path.
        
        Args:
            path: The request path.
            
        Returns:
            True if logging should be skipped.
        """
        skip_paths = ['/static/', '/media/', '/health/', '/favicon.ico']
        return any(path.startswith(p) for p in skip_paths)


class ExceptionHandlerMiddleware:
    """
    Middleware for handling uncaught exceptions.
    
    Ensures all exceptions return proper JSON responses.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request and handle exceptions.
        
        Args:
            request: The incoming HTTP request.
            
        Returns:
            The HTTP response.
        """
        return self.get_response(request)

    def process_exception(
        self, 
        request: HttpRequest, 
        exception: Exception
    ) -> JsonResponse | None:
        """
        Handle uncaught exceptions.
        
        Args:
            request: The incoming HTTP request.
            exception: The exception that was raised.
            
        Returns:
            JSON response with error details or None.
        """
        # Only handle non-DRF requests (DRF has its own handler)
        if request.path.startswith('/api/'):
            return None
        
        logger.exception(
            f"Unhandled exception: {exception}\n"
            f"Path: {request.path}\n"
            f"Method: {request.method}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        return JsonResponse(
            {
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': 'Ocorreu um erro interno no servidor.',
                    'status_code': 500,
                }
            },
            status=500
        )


