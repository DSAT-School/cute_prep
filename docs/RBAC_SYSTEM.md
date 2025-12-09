# Simplified Role-Based Access Control (RBAC) System

## Overview
A simplified weight-based RBAC system for managing user access control. No Django admin - all management done through custom UI. No complex permissions - just simple role weights.

## System Architecture

### Weight-Based Hierarchy (Adjustable)
- **User (Weight: 1)** - Basic access to practice features
- **Instructor (Weight: 5)** - Can view student progress, create content  
- **Admin (Weight: 10)** - Full system access, manage roles and users
- **Superuser (Weight: 999)** - Bypasses all checks

**Key Feature:** Role weights are fully adjustable by admins. Change weight to instantly change access level.

## Core Components

### Models (`apps/core/models.py`)

#### Role Model
- `name`: Role name (unique)
- `weight`: Integer weight determining access level (unique, **adjustable**)
- `description`: What the role can do
- `is_active`: Enable/disable role

#### User Model Extension
- `role`: ForeignKey to Role
- Methods:
  - `get_role_weight()`: Returns user's role weight
  - `has_min_role_weight(min_weight)`: Check if user meets minimum weight

### Decorators (`apps/core/decorators.py`)

```python
@require_role_weight(5)  # Requires weight 5 or higher
def instructor_view(request):
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

- `/rbac/` - RBAC Dashboard (overview) - Admin only (weight 10+)
- `/rbac/roles/` - Manage roles (create/edit/delete, **adjust weights**) - Admin only
- `/rbac/users/` - Assign user roles - Admin only
- `/instructor/` - Instructor dashboard - Instructor+ (weight 5+)

## Access Levels by Role

### User (Weight: 1)
- Access practice modules
- View own progress
- Use AI chat assistant
- Earn and spend Delta coins

### Instructor (Weight: 5+)
- All User features
- View all student progress
- Create content
- Manage courses
- Export reports

### Admin (Weight: 10+)
- All Instructor features
- Manage users
- Manage roles (create/edit/delete)
- **Adjust role weights**
- System configuration

**Note:** Changing a role's weight instantly changes what users with that role can access. No need to manage individual permissions.

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
