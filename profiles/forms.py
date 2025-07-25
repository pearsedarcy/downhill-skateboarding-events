from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from .models import UserProfile, SKATING_STYLES, STANCE_CHOICES, PROFILE_VISIBILITY
from django.contrib.auth.models import User
import re


class UserProfileForm(forms.ModelForm):
    """Enhanced user profile form with validation and all new fields"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your username'
        }),
        help_text="Your unique username for the platform"
    )

    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'display_name', 'bio', 'country', 'city',
            'instagram', 'youtube', 'website',
            'skating_style', 'skill_level', 'years_skating', 'stance', 'primary_setup',
            'profile_visibility', 'show_real_name', 'show_location'
        ]
        widgets = {
            # Core information
            'display_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your display name (optional)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered h-32',
                'placeholder': 'Tell us about yourself and your skating journey...',
                'maxlength': '500'
            }),
            
            # Avatar handled separately by AvatarUploadForm
            
            # Location
            'country': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your country'
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your city'
            }),
            
            # Social Media
            'instagram': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'username (without @)'
            }),
            'youtube': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://youtube.com/channel/...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://yoursite.com'
            }),
            
            # Skateboarding Information
            'skating_style': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'skill_level': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '1',
                'max': '10',
                'placeholder': '1-10 scale'
            }),
            'years_skating': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '0',
                'placeholder': 'How many years?'
            }),
            'stance': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'primary_setup': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered h-24',
                'placeholder': 'Describe your skateboard setup...',
                'maxlength': '300'
            }),
            
            # Privacy Controls
            'profile_visibility': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'show_real_name': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'show_location': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial username from the related user
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def clean_username(self):
        """Validate username uniqueness"""
        username = self.cleaned_data['username']
        
        # Check if username is taken by another user
        current_user = self.instance.user if self.instance else None
        if User.objects.filter(username=username).exclude(id=current_user.id if current_user else None).exists():
            raise ValidationError("This username is already taken.")
        
        return username

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

    def save(self, commit=True):
        """Save profile and update related user data"""
        profile = super().save(commit=False)
        
        if commit:
            # Save the username
            if 'username' in self.cleaned_data:
                profile.user.username = self.cleaned_data['username']
                profile.user.save()
            
            profile.save()
            
            # Calculate completion percentage after saving
            profile.calculate_completion_percentage()
        
        return profile


class AvatarUploadForm(forms.Form):
    """Separate form for avatar uploads with validation"""
    
    avatar = forms.ImageField(
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/*'
        }),
        help_text="Upload JPG, PNG, or WebP files only. Max size: 10MB"
    )
    
    def clean_avatar(self):
        """Validate avatar file size and type"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Check file size (10MB limit)
            if avatar.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise ValidationError("File size cannot exceed 10MB.")
            
            # Additional validation can be added here
            
        return avatar