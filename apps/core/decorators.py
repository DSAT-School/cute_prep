"""
Decorators for role-based access control.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def require_role_weight(min_weight):
    """
    Decorator to require minimum role weight for view access.
    
    Usage:
        @require_role_weight(5)  # Requires Instructor or higher
        def instructor_view(request):
            ...
    
    Args:
        min_weight: Minimum role weight required (1=User, 5=Instructor, 10=Admin)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            user_weight = request.user.get_role_weight()
            
            if user_weight >= min_weight:
                return view_func(request, *args, **kwargs)
            
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Insufficient permissions',
                    'required_weight': min_weight,
                    'user_weight': user_weight
                }, status=403)
            
            # Regular HTTP request
            messages.error(
                request,
                f"Access denied. You need {_get_role_name(min_weight)} permissions or higher."
            )
            return redirect('core:dashboard')
        
        return wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator to require Admin role (weight 10) for view access.
    Shortcut for @require_role_weight(10)
    """
    return require_role_weight(10)(view_func)


def instructor_required(view_func):
    """
    Decorator to require Instructor role or higher (weight 5+) for view access.
    Shortcut for @require_role_weight(5)
    """
    return require_role_weight(5)(view_func)


def _get_role_name(weight):
    """Helper function to get role name from weight."""
    role_map = {
        1: "User",
        5: "Instructor",
        10: "Admin"
    }
    return role_map.get(weight, f"Role (weight {weight})")
