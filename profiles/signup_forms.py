"""
Enhanced signup forms that integrate profile data collection with allauth registration.

This module provides forms that extend the standard allauth signup process
to collect skateboarding profile information during registration.
"""

from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from profiles.models import UserProfile, SKATING_STYLES, PROFILE_VISIBILITY
import re


class EnhancedSignupForm(SignupForm):
    """
    Enhanced signup form that includes profile fields for a better onboarding experience.
    
    This form extends the standard allauth SignupForm to collect additional
    profile information during the registration process.
    """
    
    # Profile fields that we want to collect during signup
    display_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'How should we display your name?'
        }),
        help_text="Leave blank to use your username"
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered h-24',
            'placeholder': 'Tell the community about yourself...',
            'maxlength': '500'
        }),
        help_text="A brief description about yourself"
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., United States'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., San Francisco'
        })
    )
    
    instagram = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'username (without @)'
        }),
        help_text="Your Instagram handle without the @ symbol"
    )
    
    skating_style = forms.ChoiceField(
        choices=[('', 'Select your style...')] + list(SKATING_STYLES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        })
    )
    
    skill_level = forms.IntegerField(
        min_value=1,
        max_value=10,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'range range-primary',
            'min': '1',
            'max': '10',
            'value': '5'
        }),
        help_text="Rate your skill level from 1 (beginner) to 10 (professional)"
    )
    
    years_skating = forms.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'How many years?',
            'min': '0'
        })
    )
    
    profile_visibility = forms.ChoiceField(
        choices=PROFILE_VISIBILITY,
        initial='PUBLIC',
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        help_text="Who can view your profile"
    )
    
    show_location = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text="Show your location on your profile"
    )
    
    email_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text="Receive notifications about events and community updates"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhance the default allauth fields with better styling
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': 'Choose a unique username'
            })
        
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': 'your.email@example.com'
            })
        
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': 'Create a strong password'
            })
        
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': 'Confirm your password'
            })
    
    def clean_bio(self):
        """Validate bio length and content"""
        bio = self.cleaned_data.get('bio')
        if bio:
            # Check word count
            words = bio.split()
            if len(words) > 100:
                raise ValidationError("Bio must be under 100 words.")
            
            # Check for character limit (should be handled by max_length but double-check)
            if len(bio) > 500:
                raise ValidationError("Bio must be under 500 characters.")
        
        return bio
    
    def clean_instagram(self):
        """Validate Instagram username format"""
        instagram = self.cleaned_data.get('instagram')
        if instagram:
            # Remove @ if user included it
            instagram = instagram.lstrip('@')
            
            # Validate Instagram username format
            if not re.match(r'^[a-zA-Z0-9._]{1,30}$', instagram):
                raise ValidationError(
                    "Invalid Instagram username. Use only letters, numbers, dots, and underscores."
                )
        
        return instagram
    
    def clean_skill_level(self):
        """Validate skill level range"""
        skill_level = self.cleaned_data.get('skill_level')
        if skill_level is not None:
            if skill_level < 1 or skill_level > 10:
                raise ValidationError("Skill level must be between 1 and 10.")
        
        return skill_level
    
    def clean_years_skating(self):
        """Validate years skating"""
        years_skating = self.cleaned_data.get('years_skating')
        if years_skating is not None:
            if years_skating < 0:
                raise ValidationError("Years skating cannot be negative.")
            if years_skating > 100:
                raise ValidationError("Years skating seems unrealistic. Please enter a valid number.")
        
        return years_skating
    
    def save(self, request):
        """
        Enhanced save method that creates the user and populates profile data.
        
        Note: The actual profile data saving is handled by the CustomAccountAdapter
        to ensure it happens after the user and profile are created by signals.
        """
        # Save the user using the parent method
        user = super().save(request)
        
        # The profile data will be extracted and saved by the CustomAccountAdapter
        # This ensures proper order of operations and error handling
        
        return user


class ProfileCompletionForm(forms.ModelForm):
    """
    Form for completing profile setup after basic registration.
    
    This form is used when users skip profile details during signup
    or need to complete their profile information later.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'display_name', 'bio', 'country', 'city', 'instagram',
            'skating_style', 'skill_level', 'years_skating', 'stance',
            'primary_setup', 'profile_visibility', 'show_location'
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your display name'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered h-32',
                'placeholder': 'Tell us about yourself...',
                'maxlength': '500'
            }),
            'country': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your country'
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your city'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'username (without @)'
            }),
            'skating_style': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'skill_level': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '1',
                'max': '10'
            }),
            'years_skating': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '0'
            }),
            'stance': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'primary_setup': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered h-24',
                'placeholder': 'Describe your skateboard setup...',
                'maxlength': '300'
            }),
            'profile_visibility': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'show_location': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add empty choice to select fields
        if 'skating_style' in self.fields:
            self.fields['skating_style'].choices = [('', 'Select your style...')] + list(SKATING_STYLES)
        
        if 'stance' in self.fields:
            self.fields['stance'].choices = [('', 'Select your stance...')] + list(self.fields['stance'].choices)[1:]
    
    def save(self, commit=True):
        """Save profile and update completion percentage"""
        profile = super().save(commit=False)
        
        if commit:
            profile.save()
            # Calculate completion percentage after saving
            profile.calculate_completion_percentage()
        
        return profile
