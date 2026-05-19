from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        name_parts = self.cleaned_data['full_name'].split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass


class ProfileEditForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ('avatar', 'bio', 'website', 'is_private')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['full_name'].initial = self.instance.get_full_name()

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        if commit:
            user.save()
        return user