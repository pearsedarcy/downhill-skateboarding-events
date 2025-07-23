"""
Custom URL configuration for allauth overrides.

This module provides custom URL patterns that override default allauth
behavior to integrate with our enhanced signup process.
"""

from django.urls import path, include
from profiles.signup_views import EnhancedSignupView

# Custom allauth URL patterns
account_urlpatterns = [
    # Override the default signup view with our enhanced version
    path('signup/', EnhancedSignupView.as_view(), name='account_signup'),
    
    # Include all other default allauth URLs
    path('', include('allauth.urls')),
]
