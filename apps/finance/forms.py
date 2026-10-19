from django import forms
from .models import FundAccount, AccountTransfer, BankReconciliation, AccountType


class AccountTransferForm(forms.ModelForm):
    class Meta:
        model = AccountTransfer
        fields = ["transfer_date", "from_account", "to_account", "amount", "reason"]
        widgets = {
            "transfer_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "from_account": forms.Select(attrs={"class": "form-select"}),
            "to_account": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "₹ राशि", "min": "1"}),
            "reason": forms.TextInput(attrs={"class": "form-control", "placeholder": "स्थानांतरण का कारण (उदा. बैंक से नकद निकासी पेटी हेतु)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["from_account"].queryset = FundAccount.objects.filter(is_active=True)
        self.fields["to_account"].queryset = FundAccount.objects.filter(is_active=True)


class BankReconciliationForm(forms.ModelForm):
    class Meta:
        model = BankReconciliation
        fields = ["account", "statement_date", "statement_balance", "notes"]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select"}),
            "statement_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "statement_balance": forms.NumberInput(attrs={"class": "form-control", "placeholder": "बैंक पासबुक/स्टेटमेंट का अंतिम बैलेंस (₹)"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "यदि कोई अंतर हो तो उसका विवरण..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = FundAccount.objects.filter(account_type__in=["BANK", "ONLINE", "UPI"], is_active=True)


class FundAccountForm(forms.ModelForm):
    class Meta:
        model = FundAccount
        fields = ["name", "account_type", "bank_name", "branch_name", "account_number", "ifsc_code", "current_balance", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "account_type": forms.Select(attrs={"class": "form-select"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "branch_name": forms.TextInput(attrs={"class": "form-control"}),
            "account_number": forms.TextInput(attrs={"class": "form-control"}),
            "ifsc_code": forms.TextInput(attrs={"class": "form-control"}),
            "current_balance": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ReversalForm(forms.Form):
    entry_id = forms.CharField(widget=forms.HiddenInput())
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "निरस्तीकरण का कारण (Audit Reason)"}),
        required=True
    )
