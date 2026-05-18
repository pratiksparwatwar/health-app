from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Family


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    family_name = forms.CharField(
        max_length=100,
        required=True,
        help_text='Enter your family name. Members with the same family name will be grouped together.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Get or create family by name
            family, _ = Family.objects.get_or_create(name=self.cleaned_data['family_name'])
            UserProfile.objects.create(user=user, family=family)
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'gender', 'height_cm', 'weight_kg', 'goal', 'dietary_preference', 'medical_notes']
        widgets = {
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
        }
