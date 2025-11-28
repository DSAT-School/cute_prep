"""
Django migration to add timezone field to User model.

This migration adds a timezone field to store each user's preferred timezone.
Default is UTC, allowing users worldwide to see times in their local timezone.
"""
# Generated manually for timezone functionality

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add timezone field to User model."""

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(
                default='UTC',
                help_text="User's preferred timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')",
                max_length=63,
                verbose_name='timezone',
            ),
        ),
    ]
