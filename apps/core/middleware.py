"""
Middleware for timezone detection and activation.

This module provides middleware to automatically detect and activate
the user's timezone for the current request.
"""

import zoneinfo
import logging
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    """
    Middleware to detect and activate user timezone.
    
    Timezone detection priority:
    1. User's saved timezone preference (from User model)
    2. Timezone from session (set by client-side detection)
    3. Timezone from HTTP header (X-Timezone)
    4. Default to UTC
    
    The activated timezone will be used for all datetime operations
    in the current request, while the database still stores everything in UTC.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process the request and activate appropriate timezone."""
        
        if not getattr(settings, 'USER_TIME_ZONE_ENABLED', False):
            return self.get_response(request)
        
        tzname = self._get_timezone(request)
        
        if tzname:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
                logger.debug(f"Activated timezone: {tzname} for request")
            except (zoneinfo.ZoneInfoNotFoundError, KeyError, ValueError) as e:
                logger.warning(f"Invalid timezone '{tzname}': {e}. Using default.")
                timezone.deactivate()
        else:
            timezone.deactivate()
        
        response = self.get_response(request)
        return response
    
    def _get_timezone(self, request):
        """
        Determine the timezone to use for this request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: The timezone name (e.g., 'America/New_York') or None
        """
        # Priority 1: User's saved preference
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'timezone') and request.user.timezone:
                return request.user.timezone
        
        # Priority 2: Session timezone (set by client-side JavaScript)
        if 'detected_timezone' in request.session:
            return request.session['detected_timezone']
        
        # Priority 3: HTTP Header (X-Timezone)
        if 'HTTP_X_TIMEZONE' in request.META:
            return request.META['HTTP_X_TIMEZONE']
        
        # Default: None (will use UTC)
        return None
