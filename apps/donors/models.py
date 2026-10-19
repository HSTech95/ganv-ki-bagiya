from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser


class Donor(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donor_profile",
        help_text=_("Optional link to registered user")
    )
    name = models.CharField(max_length=150, verbose_name=_("Donor Name"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Mobile Number"))
    email = models.EmailField(blank=True, verbose_name=_("Email Address"))
    address = models.CharField(max_length=255, blank=True, verbose_name=_("Village / Mohalla / City"))
    pan_number = models.CharField(max_length=15, blank=True, verbose_name=_("PAN Number (Optional)"))
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_("Keep Anonymous in Public"),
        help_text=_("Hide identity from public reports and displays")
    )
    notes = models.TextField(blank=True, verbose_name=_("Administrative Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Donor")
        verbose_name_plural = _("Donors")

    def __str__(self):
        return f"{self.name} ({self.phone or 'No phone'})"

    @property
    def public_name(self):
        if self.is_anonymous:
            return _("गुमनाम दानदाता (Well-wisher)")
        return self.name

    @property
    def masked_phone(self):
        if not self.phone or len(self.phone) < 6:
            return "******"
        return f"{self.phone[:2]}******{self.phone[-2:]}"

    def total_contributed(self):
        from apps.donations.models import PaymentStatus
        return (
            self.donations.filter(payment_status=PaymentStatus.CONFIRMED).aggregate(
                total=models.Sum("amount")
            )["total"]
            or 0
        )
