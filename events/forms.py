from django import forms
from django.forms import inlineformset_factory
from .models import Event, Location
from django.core.exceptions import ValidationError

class LocationForm(forms.ModelForm):
    def clean_location_title(self):
        location_title = self.cleaned_data.get('location_title')
        if not location_title:
            raise forms.ValidationError("Location name is required.")
        return location_title

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not city:
            raise forms.ValidationError("City is required.")
        return city

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError("Country is required.")
        return country

    class Meta:
        model = Location
        fields = [
            'location_title',
            'start_latitude',
            'start_longitude',
            'finish_latitude',
            'finish_longitude',
            'address',
            'country',
            'city',
        ]
        widgets = {
            'location_title': forms.TextInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'placeholder': 'Enter a name for this location'
            }),
            'start_latitude': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': 'any', 'placeholder': 'Latitude'}),
            'start_longitude': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': 'any', 'placeholder': 'Longitude'}),
            'finish_latitude': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': 'any', 'placeholder': 'Latitude'}),
            'finish_longitude': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': 'any', 'placeholder': 'Longitude'}),
            'address': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'country': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }

class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].required = False
        self.fields['end_date'].required = False
        self.fields['tickets_link'].required = False
        self.fields['cost'].required = False
        self.fields['max_attendees'].required = False
        self.fields['published'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Required fields specific to event
        required_fields = {
            'title': 'Event title',
            'description': 'Event description', 
            'event_type': 'Event type',
            'skill_level': 'Skill level',
            'start_date': 'Start date',
        }
        
        errors = []
        
        # Check required fields
        for field, name in required_fields.items():
            if not cleaned_data.get(field):
                errors.append(f"{name} is required.")
        
        # Validate cost
        cost = cleaned_data.get('cost')
        if cost and cost < 0:
            errors.append("Cost cannot be negative.")
            
        # Validate max_attendees
        max_attendees = cleaned_data.get('max_attendees')
        if max_attendees and max_attendees < 1:
            errors.append("Maximum attendees must be at least 1.")
            
        # Validate dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            errors.append("End date cannot be before start date.")
            
        if errors:
            raise ValidationError(' '.join(errors))
            
        return cleaned_data

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'skill_level',
            'start_date', 'end_date', 'tickets_link', 'cover_image',
            'cost', 'max_attendees', 'published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'placeholder': 'Enter event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-primary w-full h-32',
                'placeholder': 'Describe your event'
            }),
            'event_type': forms.Select(attrs={
                'class': 'select select-bordered select-primary w-full'
            }),
            'skill_level': forms.Select(attrs={
                'class': 'select select-bordered select-primary w-full'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'type': 'date',
                'onchange': 'updateEndDateMin(this.value)'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'type': 'date'
            }),
            'tickets_link': forms.URLInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'placeholder': 'https://'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-primary w-full'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Leave empty for free event'
            }),
            'max_attendees': forms.NumberInput(attrs={
                'class': 'input input-bordered input-primary w-full',
                'min': '1',
                'placeholder': 'Leave empty for unlimited spots'
            }),
            'published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
                'role': 'switch'
            })
        }
