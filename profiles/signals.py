"""
Signal handlers for automatically creating and updating user profiles.

This module ensures that a UserProfile is created whenever a new User is created,
and that profile changes are saved properly.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from typing import Any
from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(
    sender: Any,
    instance: User,
    created: bool,
    **kwargs: Any
) -> None:
    """
    Signal handler to create or update UserProfile when User is saved.

    Args:
        sender: The model class
        instance: The actual instance being saved
        created: Boolean; True if a new record was created
        **kwargs: Additional keyword arguments
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()