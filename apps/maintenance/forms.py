from django import forms
from .models import MaintenanceTask, FacilityType, TaskType, TaskPriority, TaskStatus, TaskFrequency
from apps.projects.models import Project
from apps.accounts.models import CustomUser


class MaintenanceTaskForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = [
            "title", "facility", "task_type", "project", "description",
            "frequency", "scheduled_date", "due_date", "priority",
            "status", "assigned_volunteer", "before_photo", "after_photo"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "कार्य का नाम (जैसे: बगिया में नई घास व फव्वारा लगाना)"}),
            "facility": forms.Select(attrs={"class": "form-select"}),
            "task_type": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "frequency": forms.Select(attrs={"class": "form-select"}),
            "scheduled_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assigned_volunteer": forms.Select(attrs={"class": "form-select"}),
            "before_photo": forms.FileInput(attrs={"class": "form-control"}),
            "after_photo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all()
        self.fields["project"].empty_label = "-- कोई प्रोजेक्ट नहीं (स्वतंत्र रख-रखाव) --"
        self.fields["assigned_volunteer"].queryset = CustomUser.objects.filter(is_active=True)
        self.fields["assigned_volunteer"].empty_label = "-- स्वयंसेवक चुनें (वैकल्पिक) --"


class TaskCompleteForm(forms.Form):
    completion_date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    completion_notes = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "कार्य समाप्ति विवरण व अनुभव..."}))
    after_photo = forms.FileField(required=False, widget=forms.FileInput(attrs={"class": "form-control"}))
