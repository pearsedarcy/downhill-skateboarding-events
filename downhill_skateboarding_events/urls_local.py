"""
URLs configuration for development environment with Debug Toolbar
"""

from django.urls import path, include
from django.conf import settings
from .urls import urlpatterns  # Import the main URL patterns

# Add Debug Toolbar URLs in development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
