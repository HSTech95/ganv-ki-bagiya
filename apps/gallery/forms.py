from django import forms
from .models import GalleryAlbum, GalleryItem, AlbumCategory


class GalleryAlbumForm(forms.ModelForm):
    class Meta:
        model = GalleryAlbum
        fields = ["title", "category", "description", "cover_image", "event_date", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
            "event_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class GalleryItemForm(forms.ModelForm):
    class Meta:
        model = GalleryItem
        fields = [
            "album", "title", "media_type", "image", "video_url",
            "caption", "is_before_after", "before_image", "after_image", "order"
        ]
        widgets = {
            "album": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "media_type": forms.Select(attrs={"class": "form-select"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "video_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://youtube.com/..."}),
            "caption": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_before_after": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "before_image": forms.FileInput(attrs={"class": "form-control"}),
            "after_image": forms.FileInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
