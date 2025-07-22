"""
Forms for crew management functionality.

Provides forms for creating and managing skateboarding crews.
"""

from django import forms
from django_countries.fields import CountryField
from .models import Crew, CrewMembership, CrewInvitation


class CrewForm(forms.ModelForm):
    """Form for creating and editing crews."""
    
    class Meta:
        model = Crew
        fields = [
            'name', 'description', 'logo', 'banner', 'country', 'city',
            'crew_type', 'primary_discipline', 'website', 'instagram', 'youtube'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your crew name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-24',
                'placeholder': 'Tell us about your crew\'s mission, activities, and what makes you unique...',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            }),
            'country': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your city'
            }),
            'crew_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'primary_discipline': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'website': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://your-crew-website.com'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'input input-bordered w-full rounded-l-none',
                'placeholder': 'your_crew_handle'
            }),
            'youtube': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://youtube.com/@yourcrew'
            }),
        }
        
        help_texts = {
            'name': 'Choose a unique name for your crew',
            'description': 'Describe your crew\'s purpose and activities',
            'logo': 'Square format recommended',
            'banner': 'Wide format recommended',
            'instagram': 'Handle without @ symbol'
        }


class CrewMembershipForm(forms.ModelForm):
    """Form for editing crew memberships."""
    
    class Meta:
        model = CrewMembership
        fields = ['role', 'nickname', 'bio', 'is_public']
        
        widgets = {
            'role': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'nickname': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Crew nickname (optional)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-20',
                'placeholder': 'Your role/bio within the crew',
                'rows': 3
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            }),
        }


class CrewInvitationForm(forms.ModelForm):
    """Form for inviting members to a crew."""
    
    class Meta:
        model = CrewInvitation
        fields = ['invitee_email', 'message', 'proposed_role']
        
        widgets = {
            'invitee_email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'member@example.com'
            }),
            'message': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-20',
                'placeholder': 'Personal message with invitation (optional)',
                'rows': 3
            }),
            'proposed_role': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
        }
        
        help_texts = {
            'invitee_email': 'Email address of the person you want to invite',
            'message': 'Add a personal message to your invitation',
            'proposed_role': 'What role should this member have?'
        }
