from django import forms
from .models import Result, League, LeagueEvent, Discipline, CSVColumnMapping

class ResultUploadForm(forms.ModelForm):
    results_file = forms.FileField(
        help_text='Upload a CSV file containing the results.'
    )
    is_final = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Check if these are the final official results.'
    )

    class Meta:
        model = Result
        fields = ['result_type', 'is_final']

    def clean_results_file(self):
        file = self.cleaned_data.get('results_file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('Only CSV files are allowed.')
        return file


class CSVColumnMappingForm(forms.Form):
    """Dynamic form for mapping CSV columns to system fields"""
    def __init__(self, *args, csv_headers=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if csv_headers:
            for header in csv_headers:
                field_id = f"map_{header.replace(' ', '_').lower()}"
                self.fields[field_id] = forms.ChoiceField(
                    label=f'Map "{header}" to:',
                    choices=[('IGNORE', 'Ignore')] + [
                        (t[0], t[1]) for t in CSVColumnMapping.FIELD_TYPE_CHOICES 
                        if t[0] != 'IGNORE'
                    ],
                    required=False,
                    widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
                )
                
                # Try to auto-detect field types from header name
                if 'rank' in header.lower() or 'pos' in header.lower():
                    self.initial[field_id] = 'RANK'
                elif 'name' in header.lower() or header.lower() in [
                    'competitor', 'rider', 'athlete', 'skater'
                ]:
                    self.initial[field_id] = 'NAME'
                elif 'point' in header.lower() or 'pnt' in header.lower() or 'pts' in header.lower():
                    self.initial[field_id] = 'POINTS'
                elif 'discipline' in header.lower() or 'category' in header.lower() or header.lower() in [
                    'open skate', 'womens skate', 'luge', 'inline', 'trikes', 'adaptive'
                ]:
                    self.initial[field_id] = 'DISCIPLINE'


class BracketResultUploadForm(ResultUploadForm):
    """Form specifically for bracket results with league & discipline selection"""
    league = forms.ModelChoiceField(
        queryset=League.objects.all(),
        required=True,
        help_text="Select the league these results belong to"
    )
    
    def __init__(self, *args, **kwargs):
        event_id = kwargs.pop('event_id', None)
        super().__init__(*args, **kwargs)
        
        # Limit league choices to those that include this event
        if event_id:
            self.fields['league'].queryset = League.objects.filter(
                league_events__event_id=event_id
            )
            
            # Set initial value if there's only one league
            if self.fields['league'].queryset.count() == 1:
                self.fields['league'].initial = self.fields['league'].queryset.first()


class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        fields = [
            'name', 'season', 'description', 'league_class', 
            'country', 'continent', 'points_system',
            'banner', 'logo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter league name'
            }),
            'season': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '2020',
                'max': '2030'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Brief description of the league'
            }),
            'league_class': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'country': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'continent': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'points_system': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'banner': forms.ClearableFileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            }),
        }


class LeagueEventForm(forms.ModelForm):
    class Meta:
        model = LeagueEvent
        fields = ['event', 'multiplier', 'weight']
        widgets = {
            'event': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'multiplier': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.1',
                'min': '0',
                'max': '10'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '0',
                'max': '100'
            }),
        }


class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g. Open Skate, Women\'s, Luge'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Optional description of this discipline'
            }),
        }
