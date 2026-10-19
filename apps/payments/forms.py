from django import forms
from .models import UPIReconciliationRecord


class UPIStatementEntryForm(forms.ModelForm):
    class Meta:
        model = UPIReconciliationRecord
        fields = ["utr_number", "bank_statement_date", "amount", "payer_details", "notes"]
        widgets = {
            "bank_statement_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "utr_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 329012345678"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 1000.00"}),
            "payer_details": forms.TextInput(attrs={"class": "form-control", "placeholder": "UPI ID or sender bank details"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional bank remarks"}),
        }
