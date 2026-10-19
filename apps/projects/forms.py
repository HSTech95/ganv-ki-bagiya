from django import forms
from .models import Project, ProjectUpdate, ProjectType, ProjectStatus


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name", "project_type", "description", "objectives",
            "estimated_budget", "start_date", "target_completion_date",
            "status", "progress_percentage", "featured_image", "manager", "is_public"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "project_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "objectives": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "estimated_budget": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "target_completion_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "progress_percentage": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
            "featured_image": forms.FileInput(attrs={"class": "form-control"}),
            "manager": forms.Select(attrs={"class": "form-select"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectUpdate
        fields = ["title", "content", "update_date", "photo"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "update_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
        }
