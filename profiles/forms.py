
from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'instagram']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'textarea textarea-bordered', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
            'instagram': forms.TextInput(attrs={'class': 'input input-bordered w-full'})
        }