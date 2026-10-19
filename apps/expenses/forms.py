from django import forms
from .models import Expense, ExpenseAttachment, ExpenseCategory, ExpenseApprovalStatus
from apps.projects.models import Project
from apps.finance.models import FundAccount


class ExpenseCreateForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "expense_date", "category", "description", "amount",
            "vendor_name", "vendor_phone", "bill_number", "bill_date",
            "bill_file", "related_project", "notes"
        ]
        widgets = {
            "expense_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "खर्च का संक्षिप्त विवरण (e.g. 5 बोरी सीमेंट व रेत)"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "₹ राशि", "min": "1"}),
            "vendor_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "दुकानदार / मिस्त्री / व्यक्ति का नाम"}),
            "vendor_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "मोबाइल नंबर"}),
            "bill_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "बिल / रसीद क्रमांक"}),
            "bill_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "bill_file": forms.FileInput(attrs={"class": "form-control"}),
            "related_project": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "अतिरिक्त टिप्पणी..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_project"].queryset = Project.objects.all()
        self.fields["related_project"].empty_label = "-- कोई विशेष प्रोजेक्ट नहीं (सामान्य कोष) --"


class ExpenseApprovalForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[("APPROVED", "स्वीकृत (Approve)"), ("REJECTED", "अस्वीकृत (Reject)")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"})
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "स्वीकृति / अस्वीकृति का कारण व टिप्पणी..."}),
        required=False
    )


class ExpensePaymentForm(forms.Form):
    paid_from_account = forms.ModelChoiceField(
        queryset=FundAccount.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="भुगतान खाता (Source Account)"
    )
    payment_method = forms.ChoiceField(
        choices=[
            ("CASH", "Cash (नकद)"),
            ("BANK_TRANSFER", "Cheque / NEFT / Bank Transfer"),
            ("UPI", "UPI Transfer (यूपीआई)"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        label="भुगतान माध्यम"
    )
    payment_reference = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "चेक नंबर / UTR / नकद वाउचर नंबर"}),
        label="रेफरेंस नंबर (Reference / Voucher No.)"
    )
    paid_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="भुगतान तिथि (Payment Date)"
    )
