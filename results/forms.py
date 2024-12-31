from django import forms
from .models import Result, League

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

class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ['name', 'description', 'events']
        widgets = {
            'events': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
