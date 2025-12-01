"""
Practice app configuration.
"""
from django.apps import AppConfig


class PracticeConfig(AppConfig):
    """Configuration for practice application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.practice'
    verbose_name = 'Practice & Questions'

    def ready(self):
        """Initialize app on startup."""
        pass
