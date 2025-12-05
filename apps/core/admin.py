"""Admin configuration for core models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

# Import Delta admin configurations
from .admin_delta import (
    DeltaWalletAdmin,
    DeltaTransactionAdmin,
    DeltaEarningRuleAdmin,
    DeltaProductAdmin,
    DeltaPurchaseAdmin
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = ["username", "email", "first_name", "last_name", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_superuser", "is_active", "created_at"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login", "date_joined"]

    fieldsets = (
        (None, {"fields": ("id", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
