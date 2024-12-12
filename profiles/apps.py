"""
Django app configuration for the profiles application.

Handles app-specific configuration and signal registration.
"""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Configuration class for the profiles application."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"
    verbose_name = "User Profiles"

    def ready(self) -> None:
        """
        Initialize app and register signals.
        
        Imports and activates signal handlers when the app is ready.
        """
        import profiles.signals  # noqa