"""
Views for simplified role-based access control admin panel.
Custom admin UI without Django admin.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.core.models import Role, User
from apps.core.decorators import admin_required


@login_required
@admin_required
def rbac_dashboard(request):
    """
    Main RBAC dashboard showing overview of roles and users.
    """
    context = {
        'roles': Role.objects.annotate(user_count=Count('users')).order_by('-weight'),
        'total_users': User.objects.count(),
        'users_by_role': Role.objects.annotate(count=Count('users')).values('name', 'count'),
    }
    return render(request, 'admin/rbac_dashboard.html', context)


@login_required
@admin_required
def role_list(request):
    """
    List all roles with user counts.
    """
    roles = Role.objects.annotate(user_count=Count('users')).order_by('-weight')
    context = {'roles': roles}
    return render(request, 'admin/role_list.html', context)


@login_required
@admin_required
def role_create(request):
    """
    Create a new role.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        weight = request.POST.get('weight', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        errors = []
        if not name:
            errors.append("Role name is required")
        if not weight:
            errors.append("Role weight is required")
        else:
            try:
                weight = int(weight)
                if weight < 1:
                    errors.append("Role weight must be at least 1")
            except ValueError:
                errors.append("Role weight must be a number")
        
        # Check for duplicates
        if name and Role.objects.filter(name=name).exists():
            errors.append(f"Role '{name}' already exists")
        if weight and Role.objects.filter(weight=weight).exists():
            errors.append(f"Role with weight {weight} already exists")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('core:role_list')
        
        # Create role
        role = Role.objects.create(
            name=name,
            weight=weight,
            description=description
        )
        messages.success(request, f"Role '{role.name}' created successfully!")
        return redirect('core:role_list')
    
    return redirect('core:role_list')


@login_required
@admin_required
def role_edit(request, role_id):
    """
    Edit an existing role.
    """
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        weight = request.POST.get('weight', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        if not name:
            errors.append("Role name is required")
        if not weight:
            errors.append("Role weight is required")
        else:
            try:
                weight = int(weight)
                if weight < 1:
                    errors.append("Role weight must be at least 1")
            except ValueError:
                errors.append("Role weight must be a number")
        
        # Check for duplicates (excluding current role)
        if name and Role.objects.filter(name=name).exclude(id=role_id).exists():
            errors.append(f"Role '{name}' already exists")
        if weight and Role.objects.filter(weight=weight).exclude(id=role_id).exists():
            errors.append(f"Role with weight {weight} already exists")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('core:role_list')
        
        # Update role
        role.name = name
        role.weight = weight
        role.description = description
        role.is_active = is_active
        role.save()
        
        messages.success(request, f"Role '{role.name}' updated successfully!")
        return redirect('core:role_list')
    
    return redirect('core:role_list')


@login_required
@admin_required
@require_http_methods(["POST"])
def role_delete(request, role_id):
    """
    Delete a role (if no users are assigned).
    """
    role = get_object_or_404(Role, id=role_id)
    
    # Check if role has users
    if role.users.exists():
        messages.error(request, f"Cannot delete '{role.name}' - it has {role.users.count()} user(s) assigned")
        return redirect('core:role_list')
    
    role_name = role.name
    role.delete()
    messages.success(request, f"Role '{role_name}' deleted successfully!")
    return redirect('core:role_list')


@login_required
@admin_required
def user_role_management(request):
    """
    Manage user role assignments.
    """
    # Search and filter
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.select_related('role').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role_id=role_filter)
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'roles': Role.objects.all().order_by('weight'),
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'admin/user_role_management.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def assign_user_role(request, user_id):
    """
    Assign a role to a user.
    """
    user = get_object_or_404(User, id=user_id)
    role_id = request.POST.get('role_id')
    
    if not role_id:
        messages.error(request, "No role selected")
        return redirect('core:user_role_management')
    
    role = get_object_or_404(Role, id=role_id)
    
    # Prevent non-superusers from assigning roles higher than their own
    if not request.user.is_superuser:
        if role.weight > request.user.get_role_weight():
            messages.error(request, "You cannot assign a role higher than your own")
            return redirect('core:user_role_management')
    
    user.role = role
    user.save()
    
    messages.success(request, f"Assigned '{role.name}' role to {user.username}")
    return redirect('core:user_role_management')


@login_required
@admin_required
@require_http_methods(["POST"])
def remove_user_role(request, user_id):
    """
    Remove role from a user (set to default User role).
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get default User role
    try:
        default_role = Role.objects.get(name="User")
        user.role = default_role
        user.save()
        messages.success(request, f"Reset {user.username} to default User role")
    except Role.DoesNotExist:
        user.role = None
        user.save()
        messages.warning(request, f"Removed role from {user.username} (no default role found)")
    
    return redirect('core:user_role_management')


@login_required
@admin_required
def instructor_dashboard(request):
    """
    Instructor dashboard - accessible to instructors (weight 5+) and admins.
    """
    # Check minimum weight for instructor access
    if not request.user.has_min_role_weight(5):
        messages.error(request, "Access denied. Instructor role or higher required.")
        return redirect('dashboard')
    
    context = {
        'total_students': User.objects.filter(role__weight__lte=1).count(),
        'total_instructors': User.objects.filter(role__weight__gte=5, role__weight__lt=10).count(),
    }
    return render(request, 'admin/instructor_dashboard.html', context)
