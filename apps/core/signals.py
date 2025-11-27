"""Signal handlers for core application."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def user_post_save(sender, instance: User, created: bool, **kwargs) -> None:
    """
    Signal handler for User post-save events.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        kwargs: Additional keyword arguments
    """
    if created:
        logger.info(f"New user created: {instance.username} ({instance.email})")
