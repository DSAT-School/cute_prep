# Role-Based Access Control (RBAC) System

## Overview
A weight-based RBAC system for managing user permissions and access control. No Django admin - all management done through custom UI.

## System Architecture

### Weight-Based Hierarchy
- **User (Weight: 1)** - Basic access to practice features
- **Instructor (Weight: 5)** - Can view student progress, create content
- **Admin (Weight: 10)** - Full system access, manage roles/permissions/users
- **Superuser (Weight: 999)** - Bypasses all checks

Higher weight = More permissions

## Core Components

### Models (`apps/core/models.py`)

#### Role Model
- `name`: Role name (unique)
- `weight`: Integer weight determining access level (unique)
- `description`: What the role can do
- `is_active`: Enable/disable role

#### Permission Model
- `name`: Permission display name
- `codename`: Unique identifier for checking
- `description`: What this permission allows
- `min_role_weight`: Minimum weight required to access
- `category`: Group permissions (practice, instructor, admin)
- `is_active`: Enable/disable permission

#### User Model Extension
- `role`: ForeignKey to Role
- Methods:
  - `get_role_weight()`: Returns user's role weight
  - `has_permission(codename)`: Check if user has specific permission
  - `has_min_role_weight(min_weight)`: Check if user meets minimum weight

### Decorators (`apps/core/decorators.py`)

```python
@require_role_weight(5)  # Requires Instructor or higher
def instructor_view(request):
    ...

@require_permission('manage_users')  # Checks specific permission
def manage_users_view(request):
    ...

@admin_required  # Shortcut for weight 10+
def admin_view(request):
    ...

@instructor_required  # Shortcut for weight 5+
def instructor_view(request):
    ...
```

### Context Processors
Automatically adds to all templates:
- `user_role_weight`: User's role weight
- `user_role_name`: User's role name
- `is_admin`: Boolean (weight >= 10)
- `is_instructor`: Boolean (weight >= 5)

### Template Usage

```django
{% if is_admin %}
  <a href="/rbac/">Admin Panel</a>
{% endif %}

{% if is_instructor %}
  <a href="/instructor/">Instructor Dashboard</a>
{% endif %}

{% if user_role_weight >= 5 %}
  <!-- Instructor or higher content -->
{% endif %}
```

## Management Commands

### Initialize RBAC System
```bash
python manage.py init_roles
```
Creates default roles, permissions, and assigns User role to existing users.

Use `--force` to recreate/update existing roles and permissions.

### Assign Role via Shell
```python
from apps.core.models import User, Role

user = User.objects.get(email='user@example.com')
admin_role = Role.objects.get(name='Admin')
user.role = admin_role
user.save()
```

## Admin UI Routes

All routes require Admin role (weight 10):

- `/rbac/` - RBAC Dashboard (overview)
- `/rbac/roles/` - Manage roles
- `/rbac/permissions/` - Manage permissions
- `/rbac/users/` - Assign user roles
- `/instructor/` - Instructor dashboard (weight 5+)

## Default Permissions

### User Level (Weight: 1)
- `access_practice` - Access practice modules
- `view_own_progress` - View own statistics
- `use_ai_chat` - Use AI chat assistant
- `use_delta_store` - Earn and spend Delta coins

### Instructor Level (Weight: 5)
- `view_all_progress` - View all student progress
- `create_content` - Create/modify questions
- `manage_courses` - Create courses/modules
- `export_reports` - Export progress reports

### Admin Level (Weight: 10)
- `manage_users` - Create/edit/delete users
- `manage_roles` - Create/edit/delete roles
- `manage_permissions` - Create/edit permissions
- `view_system_logs` - View system logs
- `system_config` - Modify system settings

## Usage Examples

### Protect a View
```python
from apps.core.decorators import require_role_weight, require_permission

@require_role_weight(5)
def view_student_progress(request):
    # Only instructors and admins can access
    pass

@require_permission('create_content')
def create_question(request):
    # Checks if user has 'create_content' permission
    pass
```

### Check Permission in View
```python
def my_view(request):
    if request.user.has_permission('manage_users'):
        # Show admin controls
        pass
    
    if request.user.get_role_weight() >= 5:
        # Show instructor features
        pass
```

### AJAX Requests
Decorators automatically return JSON for AJAX:
```json
{
  "error": "Insufficient permissions",
  "required_weight": 10,
  "user_weight": 1
}
```

## Navigation Integration

Sidebar automatically shows:
- **Admin Panel** link (weight >= 10)
- **Instructor Panel** link (weight >= 5)

Links appear in both desktop sidebar and mobile menu.

## Security Features

1. **Backend enforcement** - All checks done server-side
2. **Protected routes** - Decorators prevent unauthorized access
3. **Cascading permissions** - Higher weight includes lower permissions
4. **Role protection** - Cannot delete roles with assigned users
5. **Non-escalation** - Non-superusers can't assign roles higher than their own

## Extending the System

### Add New Permission
1. Via UI: Go to `/rbac/permissions/` and create
2. Via code: Add to `init_roles.py` command

### Add New Role
1. Via UI: Go to `/rbac/roles/` and create
2. Assign appropriate weight (between existing roles)

### Protect New Endpoint
```python
from apps.core.decorators import require_role_weight

@require_role_weight(5)  # Adjust weight as needed
def my_new_feature(request):
    pass
```

## Troubleshooting

### User has no role
Run: `python manage.py init_roles`
This assigns default User role to all users without roles.

### Permission denied
Check:
1. User has correct role assigned
2. Permission `is_active` is True
3. User's role weight >= permission's `min_role_weight`

### Admin links not showing
1. Verify user has role with weight >= 10
2. Check context processor is in settings
3. Clear browser cache

## Future Enhancements

- Role-based dashboard customization
- Permission-based feature flags
- Audit logging for role changes
- Temporary role assignments
- Custom permission groups
