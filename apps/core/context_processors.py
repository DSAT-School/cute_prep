"""
Template context processors for adding global data to template contexts.

This module provides context processors that inject useful data
into all template contexts automatically.
"""

from django.utils import timezone
from django.conf import settings


def user_timezone(request):
    """
    Add timezone information to template context.
    
    Makes the current activated timezone and user's timezone preference
    available to all templates.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Context dictionary with timezone data
    """
    context = {
        'TIMEZONE_ENABLED': getattr(settings, 'USER_TIME_ZONE_ENABLED', False),
        'current_timezone': timezone.get_current_timezone_name(),
    }
    
    # Add user's saved timezone if authenticated
    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'timezone'):
            context['user_timezone'] = request.user.timezone
    
    return context


def user_role(request):
    """
    Add user role and permissions information to template context.
    
    Makes role weight and permission checking available in all templates.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Context dictionary with role data
    """
    context = {
        'user_role_weight': 0,
        'user_role_name': None,
        'is_admin': False,
        'is_instructor': False,
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        context['user_role_weight'] = request.user.get_role_weight()
        
        if request.user.role:
            context['user_role_name'] = request.user.role.name
        
        # Role shortcuts for template conditionals
        context['is_admin'] = context['user_role_weight'] >= 10
        context['is_instructor'] = context['user_role_weight'] >= 5
    
    return context
