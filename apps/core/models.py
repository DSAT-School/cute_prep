"""
Core models for the practice_portal application.

This module contains the custom User model and base models
that are used throughout the application.
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating created and modified fields.
    
    This model should be inherited by all models that need timestamp tracking.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this object")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when this object was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when this object was last updated")
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class User(AbstractUser, TimeStampedModel):
    """
    Custom User model for the application.
    
    Extends Django's AbstractUser with UUID primary key and additional fields.
    This model should be used for all user-related operations.
    
    Attributes:
        email: User's email address (required and unique)
        timezone: User's preferred timezone (detected or set by user)
        is_active: Boolean indicating if the user account is active
        is_staff: Boolean indicating if user can access admin site
        is_superuser: Boolean indicating if user has all permissions
    """

    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("User's email address")
    )
    
    timezone = models.CharField(
        _("timezone"),
        max_length=63,
        default="UTC",
        help_text=_("User's preferred timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')")
    )
    
    # Override id from TimeStampedModel to avoid conflicts
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this user")
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the user."""
        return self.username

    def get_full_name(self) -> str:
        """
        Return the first_name plus the last_name, with a space in between.
        
        Returns:
            Full name of the user
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
