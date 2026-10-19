from django import forms
from .models import Donor


class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ["name", "phone", "email", "address", "pan_number", "is_anonymous", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "दानदाता का पूरा नाम"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "10 अंकों का मोबाइल नंबर"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com (वैकल्पिक)"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "गांव / मोहल्ला / शहर"}),
            "pan_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "PAN नंबर (वैकल्पिक)"}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "समिति के लिए आंतरिक विवरण / नोट"}),
        }
