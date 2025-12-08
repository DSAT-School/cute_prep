"""
Management command to initialize default roles.
Usage: python manage.py init_roles
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Role, User


class Command(BaseCommand):
    help = "Initialize default roles for simplified RBAC system"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate roles',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("Initializing Simplified RBAC System"))
        self.stdout.write("=" * 70)
        
        with transaction.atomic():
            # Create default roles
            roles_created = self._create_roles(force)
            
            # Assign default role to existing users without roles
            users_updated = self._assign_default_roles()
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✓ RBAC System Initialization Complete"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"Roles created: {roles_created}")
        self.stdout.write(f"Users updated with default role: {users_updated}")
        self.stdout.write("=" * 70)

    def _create_roles(self, force):
        """Create default roles with adjustable weights."""
        self.stdout.write("\n📋 Creating Roles...")
        
        default_roles = [
            {
                "name": "User",
                "weight": 1,
                "description": "Regular user - can access practice features and view own progress"
            },
            {
                "name": "Instructor",
                "weight": 5,
                "description": "Instructor - can view student progress, create content, manage courses"
            },
            {
                "name": "Admin",
                "weight": 10,
                "description": "Administrator - full system access, manage users and roles"
            }
        ]
        
        created_count = 0
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                defaults={
                    "weight": role_data["weight"],
                    "description": role_data["description"]
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {role}"))
            elif force:
                # Only update description, not weight (weight is adjustable by admin)
                role.description = role_data["description"]
                role.save()
                self.stdout.write(f"  ↻ Updated: {role}")
            else:
                self.stdout.write(f"  - Exists: {role}")
        
        return created_count

    def _assign_default_roles(self):
        """Assign default 'User' role to users without roles."""
        self.stdout.write("\n👥 Assigning Default Roles to Users...")
        
        try:
            user_role = Role.objects.get(name="User")
            users_without_role = User.objects.filter(role__isnull=True)
            count = users_without_role.count()
            
            if count > 0:
                users_without_role.update(role=user_role)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Assigned 'User' role to {count} user(s)"))
                return count
            else:
                self.stdout.write("  - All users already have roles assigned")
                return 0
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Default 'User' role not found"))
            return 0
