from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from apps.donations.models import Donation


class PaymentTransaction(models.Model):
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name="payment_transaction",
        verbose_name=_("Donation")
    )
    gateway_order_id = models.CharField(max_length=100, blank=True, verbose_name=_("Gateway Order ID"))
    gateway_payment_id = models.CharField(max_length=100, blank=True, verbose_name=_("Gateway Payment ID"))
    gateway_signature = models.CharField(max_length=255, blank=True, verbose_name=_("Signature / Checksum"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Amount (₹)"))
    status = models.CharField(
        max_length=30,
        choices=[
            ("CREATED", _("Order Created")),
            ("AUTHORIZED", _("Authorized")),
            ("CAPTURED", _("Captured / Paid")),
            ("FAILED", _("Payment Failed")),
            ("REFUNDED", _("Refunded")),
        ],
        default="CREATED",
        verbose_name=_("Transaction Status")
    )
    raw_response = models.JSONField(default=dict, blank=True, verbose_name=_("Gateway Payload / Logs"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Payment Transaction")
        verbose_name_plural = _("Payment Transactions")

    def __str__(self):
        return f"TXN [{self.gateway_payment_id or self.gateway_order_id}] - ₹{self.amount} ({self.status})"


class UPIReconciliationRecord(models.Model):
    utr_number = models.CharField(max_length=100, unique=True, verbose_name=_("UTR / Transaction ID"))
    bank_statement_date = models.DateField(verbose_name=_("Bank Statement Date"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Credit Amount (₹)"))
    payer_details = models.CharField(max_length=200, blank=True, verbose_name=_("Payer UPI ID / Sender Details"))
    matched_donation = models.OneToOneField(
        Donation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="upi_reconciliation",
        verbose_name=_("Matched Donation")
    )
    is_matched = models.BooleanField(default=False, verbose_name=_("Reconciled"))
    matched_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Reconciled By")
    )
    matched_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Reconciled Timestamp"))
    notes = models.TextField(blank=True, verbose_name=_("Audit Remarks"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-bank_statement_date", "-created_at"]
        verbose_name = _("UPI Reconciliation Entry")
        verbose_name_plural = _("UPI Reconciliation Entries")

    def __str__(self):
        return f"UTR {self.utr_number} - ₹{self.amount} ({'Matched' if self.is_matched else 'Unmatched'})"
