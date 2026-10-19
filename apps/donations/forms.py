from django import forms
from .models import Donation, DonationPurpose, PaymentMethod, PaymentStatus
from apps.projects.models import Project
from apps.finance.models import FundAccount


class PublicDonationForm(forms.ModelForm):
    custom_amount = forms.DecimalField(
        required=False,
        min_value=1,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg text-success fw-bold",
            "placeholder": "अन्य राशि (Custom ₹)"
        })
    )

    class Meta:
        model = Donation
        fields = [
            "donor_name", "donor_phone", "donor_email", "amount",
            "purpose", "related_project", "payment_method",
            "is_anonymous", "message"
        ]
        widgets = {
            "donor_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "आपका शुभ नाम (Full Name)",
                "required": True
            }),
            "donor_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "मोबाइल नंबर (Mobile Number)",
                "required": True
            }),
            "donor_email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "ईमेल (वैकल्पिक / Optional)"
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control form-control-lg fw-bold",
                "placeholder": "राशि (₹)",
                "min": "1"
            }),
            "purpose": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "related_project": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "गाँव या बगिया के नाम कोई संदेश अथवा दुआ (Optional)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_project"].queryset = Project.objects.filter(is_public=True)
        self.fields["related_project"].empty_label = "-- किसी विशेष प्रोजेक्ट से नहीं (सामान्य) --"


class UPISubmitReferenceForm(forms.Form):
    transaction_reference = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "12-अंकों का UPI UTR / Transaction Ref No."
        })
    )
    payment_proof = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"})
    )


class StaffDonationEntryForm(forms.ModelForm):
    donor_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "गाँव / पता"})
    )

    class Meta:
        model = Donation
        fields = [
            "donor_name", "donor_phone", "donor_email", "amount",
            "purpose", "related_project", "payment_method", "destination_account",
            "transaction_reference", "donation_date", "is_anonymous", "message"
        ]
        widgets = {
            "donor_name": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "donor_phone": forms.TextInput(attrs={"class": "form-control"}),
            "donor_email": forms.EmailInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "required": True, "min": "1"}),
            "purpose": forms.Select(attrs={"class": "form-select"}),
            "related_project": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "destination_account": forms.Select(attrs={"class": "form-select"}),
            "transaction_reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cash Receipt / Cheque / UTR"}),
            "donation_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination_account"].queryset = FundAccount.objects.filter(is_active=True)
        self.fields["related_project"].queryset = Project.objects.all()
