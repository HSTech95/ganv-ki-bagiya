from django import forms
from .models import ContactSubmission, VolunteerRegistration, SiteSetting


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ["name", "phone", "email", "subject", "category", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "आपका पूरा नाम (Full Name)"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "मोबाइल नंबर (Mobile Number)"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "ईमेल (वैकल्पिक / Optional)"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "विषय (Subject)"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "संदेश अथवा विवरण लिखें..."}),
        }


class VolunteerForm(forms.ModelForm):
    class Meta:
        model = VolunteerRegistration
        fields = ["full_name", "phone", "email", "village_mohalla", "skills_interest", "availability"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "पूरा नाम"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "मोबाइल नंबर"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "ईमेल पता (वैकल्पिक)"}),
            "village_mohalla": forms.TextInput(attrs={"class": "form-control", "placeholder": "गाँव / टोला / मोहल्ला"}),
            "skills_interest": forms.TextInput(attrs={"class": "form-control", "placeholder": "रुचि (जैसे: पौधरोपण, साफ-सफाई, मिस्त्री कार्य, प्रचार)"}),
            "availability": forms.TextInput(attrs={"class": "form-control", "placeholder": "उपलब्ध समय (जैसे: केवल रविवार, सुबह 8-11)"}),
        }


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = "__all__"
        widgets = {
            "about_text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "hero_subtitle": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "president_message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
