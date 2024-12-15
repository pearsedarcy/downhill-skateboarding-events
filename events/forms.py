from django import forms
from django.forms import inlineformset_factory
from .models import Event, Location
from django.core.exceptions import ValidationError

class LocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_line'].required = False
        self.fields['finish_line'].required = False

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get('city')
        country = cleaned_data.get('country')
        address = cleaned_data.get('address')
        
        if not all([city, country, address]):
            raise ValidationError('City, country and address are required for event location.')
        
        return cleaned_data

    class Meta:
        model = Location
        fields = ['city', 'country', 'address', 'start_line', 'finish_line']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'country': forms.Select(attrs={'class': 'select select-bordered select-primary border-primary w-full'}),
            'address': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'start_line': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'finish_line': forms.TextInput(attrs={'class': 'input input-bordered w-full'})
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
        
        # Required fields
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
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-primary border-primary w-full focus:outline-primary', 'rows': 6}),
            'event_type': forms.Select(attrs={'class': 'select select-bordered select-primary border-primary w-full'}),
            'skill_level': forms.Select(attrs={'class': 'select select-bordered select-primary border-primary w-full'}),
            'start_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date', 'onchange': 'updateEndDateMin(this.value)'}),
            'end_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'tickets_link': forms.URLInput(attrs={'class': 'input input-bordered w-full'}),
            'cover_image': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
            'cost': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '0.00',
                'onfocus': 'this.value=""'
            }),
            'max_attendees': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full', 
                'min': '0',
                'placeholder': '0',
                'onfocus': 'this.value=""'
            }),
            'published': forms.CheckboxInput(attrs={'class': 'toggle toggle-primary', 'onchange': 'this.blur()'}),
            'slug': forms.HiddenInput()
        }
