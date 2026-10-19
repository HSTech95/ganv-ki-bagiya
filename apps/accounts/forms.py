from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, UserRole


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control form-control-lg",
        "placeholder": "उपयोगकर्ता नाम (Username)"
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control form-control-lg",
        "placeholder": "पासवर्ड (Password)"
    }))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone_number", "village_address", "profile_photo"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "village_address": forms.TextInput(attrs={"class": "form-control"}),
            "profile_photo": forms.FileInput(attrs={"class": "form-control"}),
        }


class UserAdminCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "role", "phone_number", "village_address"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "village_address": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
