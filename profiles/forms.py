from django import forms
from .models import UserProfile
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'instagram']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full h-32'}),
            'instagram': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'avatar': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Save the username
            profile.user.username = self.cleaned_data['username']
            profile.user.save()
            profile.save()
        return profile