"""
Timezone utility functions for handling user timezones.

This module provides helper functions for timezone detection,
conversion, and formatting.
"""

import zoneinfo
from datetime import datetime
from typing import Optional
from django.utils import timezone


def get_all_timezones():
    """
    Get list of all available timezones.
    
    Returns:
        list: Sorted list of timezone names
    """
    return sorted(zoneinfo.available_timezones())


def get_common_timezones():
    """
    Get list of commonly used timezones.
    
    Returns:
        list: Common timezone choices for forms
    """
    common = [
        'UTC',
        'America/New_York',
        'America/Chicago',
        'America/Denver',
        'America/Los_Angeles',
        'America/Toronto',
        'America/Vancouver',
        'America/Mexico_City',
        'America/Sao_Paulo',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'Europe/Rome',
        'Europe/Madrid',
        'Europe/Moscow',
        'Asia/Dubai',
        'Asia/Kolkata',
        'Asia/Bangkok',
        'Asia/Singapore',
        'Asia/Hong_Kong',
        'Asia/Tokyo',
        'Asia/Seoul',
        'Australia/Sydney',
        'Australia/Melbourne',
        'Pacific/Auckland',
    ]
    return common


def validate_timezone(tzname: str) -> bool:
    """
    Check if a timezone name is valid.
    
    Args:
        tzname: The timezone name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        zoneinfo.ZoneInfo(tzname)
        return True
    except (zoneinfo.ZoneInfoNotFoundError, KeyError, ValueError):
        return False


def convert_to_user_timezone(dt: datetime, user_timezone: str) -> datetime:
    """
    Convert a datetime to user's timezone.
    
    Args:
        dt: The datetime to convert (should be timezone-aware)
        user_timezone: The target timezone name
        
    Returns:
        datetime: The converted datetime in user's timezone
    """
    if dt is None:
        return None
    
    # Ensure the datetime is timezone-aware
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    
    try:
        tz = zoneinfo.ZoneInfo(user_timezone)
        return dt.astimezone(tz)
    except (zoneinfo.ZoneInfoNotFoundError, KeyError, ValueError):
        # Return original datetime if timezone is invalid
        return dt


def format_datetime_in_timezone(dt: datetime, user_timezone: str, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format a datetime in user's timezone.
    
    Args:
        dt: The datetime to format
        user_timezone: The timezone to use
        format_str: The format string (default includes timezone abbreviation)
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return ""
    
    converted_dt = convert_to_user_timezone(dt, user_timezone)
    return converted_dt.strftime(format_str)


def get_timezone_offset(tzname: str) -> Optional[str]:
    """
    Get the current UTC offset for a timezone.
    
    Args:
        tzname: The timezone name
        
    Returns:
        str: Offset string like '+05:30' or '-08:00', or None if invalid
    """
    try:
        tz = zoneinfo.ZoneInfo(tzname)
        now = datetime.now(tz)
        offset = now.strftime('%z')
        # Format as +HH:MM or -HH:MM
        if len(offset) == 5:
            return f"{offset[:3]}:{offset[3:]}"
        return offset
    except (zoneinfo.ZoneInfoNotFoundError, KeyError, ValueError):
        return None


def get_user_timezone_from_request(request) -> str:
    """
    Extract timezone from request (session, header, or user preference).
    
    Args:
        request: The HTTP request object
        
    Returns:
        str: Timezone name or 'UTC' as default
    """
    # Check user's saved preference
    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'timezone') and request.user.timezone:
            return request.user.timezone
    
    # Check session
    if 'detected_timezone' in request.session:
        return request.session['detected_timezone']
    
    # Check header
    if 'HTTP_X_TIMEZONE' in request.META:
        return request.META['HTTP_X_TIMEZONE']
    
    return 'UTC'
