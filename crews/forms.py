"""
Forms for crew management functionality.

Provides forms for creating and managing skateboarding crews.
"""

from django import forms
from django_countries.fields import CountryField
from django.contrib.auth.models import User
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


class MemberPermissionForm(forms.ModelForm):
    """Form for editing individual member permissions."""
    
    class Meta:
        model = CrewMembership
        fields = [
            'can_create_events', 'can_edit_events', 
            'can_publish_events', 'can_delegate_permissions'
        ]
        widgets = {
            'can_create_events': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
            'can_edit_events': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
            'can_publish_events': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
            'can_delegate_permissions': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
        }
        
        help_texts = {
            'can_create_events': 'Allow member to create new events for this crew',
            'can_edit_events': 'Allow member to edit existing crew events',
            'can_publish_events': 'Allow member to publish/unpublish events',
            'can_delegate_permissions': 'Allow member to grant/revoke permissions to other members',
        }

    def __init__(self, *args, **kwargs):
        self.user_requesting = kwargs.pop('user_requesting', None)
        self.crew = kwargs.pop('crew', None)
        super().__init__(*args, **kwargs)
        
        # Only show delegation permission to owners and those who already have it
        if (self.user_requesting and self.crew and 
            not self._can_manage_delegation_permissions()):
            self.fields.pop('can_delegate_permissions', None)
    
    def _can_manage_delegation_permissions(self):
        """Check if requesting user can manage delegation permissions."""
        if not self.user_requesting or not self.crew:
            return False
            
        try:
            user_membership = self.crew.get_user_membership(self.user_requesting)
            return (user_membership and 
                   (user_membership.role == 'OWNER' or 
                    user_membership.can_delegate_permissions))
        except:
            return False


class BulkPermissionForm(forms.Form):
    """Form for bulk permission management."""
    
    members = forms.ModelMultipleChoiceField(
        queryset=CrewMembership.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary mr-2'
        }),
        required=True,
        help_text='Select members to update'
    )
    
    # Permission fields
    action = forms.ChoiceField(
        choices=[
            ('grant', 'Grant Permission'),
            ('revoke', 'Revoke Permission'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'radio radio-primary mr-2'
        }),
        required=True
    )
    
    permission_type = forms.ChoiceField(
        choices=[
            ('can_create_events', 'Create Events'),
            ('can_edit_events', 'Edit Events'),
            ('can_publish_events', 'Publish Events'),
            ('can_delegate_permissions', 'Delegate Permissions'),
        ],
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        required=True
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full h-20',
            'placeholder': 'Optional: Reason for this permission change...',
            'rows': 3
        }),
        required=False,
        help_text='Optional reason for audit trail'
    )

    def __init__(self, *args, **kwargs):
        self.crew = kwargs.pop('crew', None)
        self.user_requesting = kwargs.pop('user_requesting', None)
        super().__init__(*args, **kwargs)
        
        if self.crew:
            # Only show active members (excluding the requesting user)
            self.fields['members'].queryset = self.crew.memberships.filter(
                is_active=True
            ).exclude(user=self.user_requesting).order_by('role', 'user__username')
            
            # Only show delegation permission to authorized users
            if not self._can_manage_delegation_permissions():
                permission_choices = [
                    ('can_create_events', 'Create Events'),
                    ('can_edit_events', 'Edit Events'),
                    ('can_publish_events', 'Publish Events'),
                ]
                self.fields['permission_type'].choices = permission_choices
    
    def _can_manage_delegation_permissions(self):
        """Check if requesting user can manage delegation permissions."""
        if not self.user_requesting or not self.crew:
            return False
            
        try:
            user_membership = self.crew.get_user_membership(self.user_requesting)
            return (user_membership and 
                   (user_membership.role == 'OWNER' or 
                    user_membership.can_delegate_permissions))
        except:
            return False

    def clean(self):
        cleaned_data = super().clean()
        members = cleaned_data.get('members')
        permission_type = cleaned_data.get('permission_type')
        action = cleaned_data.get('action')
        
        if members and permission_type == 'can_delegate_permissions':
            # Additional validation for delegation permissions
            if not self._can_manage_delegation_permissions():
                raise forms.ValidationError(
                    "You don't have permission to manage delegation permissions."
                )
            
            # Check if trying to modify owners
            for member in members:
                if member.role == 'OWNER':
                    raise forms.ValidationError(
                        "Cannot modify permissions for crew owners."
                    )
        
        return cleaned_data
