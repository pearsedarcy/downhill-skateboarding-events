
"""
Custom allauth adapter for enhanced user registration and profile management.

This adapter handles the enhanced signup process that collects profile data
during registration and creates a more complete user profile automatically.
"""

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib import messages
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that enhances the signup process with profile data collection.
    """
    
    def get_signup_redirect_url(self, request):
        """
        Redirect to profile completion or dashboard after signup.
        """
        # Check if we have profile data to save
        if hasattr(request, 'session') and 'pending_profile_data' in request.session:
            return '/profiles/complete-signup/'
        
        return getattr(settings, 'ACCOUNT_SIGNUP_REDIRECT_URL', '/profiles/')
    
    def save_user(self, request, user, form, commit=True):
        """
        Enhanced user saving that also handles profile data from the enhanced signup form.
        """
        logger.debug(f"CustomAccountAdapter.save_user called for user: {user.username if hasattr(user, 'username') else 'unknown'}")
        logger.debug(f"Form data keys: {list(request.POST.keys()) if request.POST else 'No POST data'}")
        
        # Save the user first using the default behavior
        user = super().save_user(request, user, form, commit)
        
        if commit:
            # Extract profile data from the request POST data
            profile_data = self.extract_profile_data(request)
            
            logger.debug(f"Extracted profile data: {profile_data}")
            
            if profile_data:
                self.save_profile_data(user, profile_data, request)
                messages.success(
                    request, 
                    f"Welcome to the community, {user.username}! Your profile has been created."
                )
            else:
                messages.info(
                    request,
                    f"Welcome {user.username}! Complete your profile to connect with the community."
                )
        
        return user
    
    def extract_profile_data(self, request) -> Dict[str, Any]:
        """
        Extract profile-related data from the signup form.
        
        Args:
            request: The HTTP request containing form data
            
        Returns:
            Dictionary of profile data to be saved
        """
        if not hasattr(request, 'POST'):
            return {}
        
        profile_fields = {
            'display_name': request.POST.get('display_name', '').strip(),
            'bio': request.POST.get('bio', '').strip(),
            'country': request.POST.get('country', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'instagram': request.POST.get('instagram', '').strip(),
            'skating_style': request.POST.get('skating_style', ''),
            'skill_level': request.POST.get('skill_level'),
            'years_skating': request.POST.get('years_skating'),
            'profile_visibility': request.POST.get('profile_visibility', 'PUBLIC'),
            'show_location': request.POST.get('show_location') == 'on',
        }
        
        # Filter out empty values and convert numeric fields
        cleaned_data = {}
        for key, value in profile_fields.items():
            if value:
                if key in ['skill_level', 'years_skating']:
                    try:
                        cleaned_data[key] = int(value) if value else None
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid numeric value for {key}: {value}")
                        continue
                elif key == 'show_location':
                    cleaned_data[key] = value
                else:
                    cleaned_data[key] = value
        
        return cleaned_data
    
    def save_profile_data(self, user, profile_data: Dict[str, Any], request):
        """
        Save the extracted profile data to the user's profile.
        
        Args:
            user: The User instance
            profile_data: Dictionary of profile data
            request: The HTTP request
        """
        try:
            # The profile should already exist due to the signal
            profile = user.profile
            
            # Update profile fields
            for field, value in profile_data.items():
                if hasattr(profile, field) and value is not None:
                    setattr(profile, field, value)
            
            # Save the profile
            profile.save()
            
            # Calculate initial completion percentage
            completion = profile.calculate_completion_percentage()
            
            logger.info(
                f"Enhanced signup completed for user {user.username}. "
                f"Profile completion: {completion}%"
            )
            
            # Store success info for potential onboarding flow
            if hasattr(request, 'session'):
                request.session['signup_completion'] = completion
                request.session['is_new_signup'] = True
            
        except Exception as e:
            logger.error(f"Error saving profile data for user {user.username}: {e}")
            # Don't fail the signup if profile saving fails
            messages.warning(
                request,
                "Your account was created successfully, but there was an issue saving your profile. "
                "You can update your profile information from your dashboard."
            )
    
    def is_safe_url(self, url):
        """
        Enhanced URL safety check for redirects.
        """
        if not url:
            return False
        return super().is_safe_url(url)
    
    def get_signup_form_initial_data(self, request):
        """
        Provide initial data for the signup form if needed.
        """
        initial = super().get_signup_form_initial_data(request)
        
        # Add any pre-filled data if coming from a referral or pre-registration
        if hasattr(request, 'session') and 'prefill_data' in request.session:
            initial.update(request.session.pop('prefill_data', {}))
        
        return initial