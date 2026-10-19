# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.utils import timezone
# pyrefly: ignore [missing-import]
from django.utils.translation import gettext_lazy as _


class Announcement(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Announcement Title"))
    content = models.TextField(verbose_name=_("Message / Content"))
    badge_text = models.CharField(
        max_length=50,
        default="सूचना (Notice)",
        verbose_name=_("Badge Label")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    published_at = models.DateTimeField(default=timezone.now, verbose_name=_("Published Date"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expires On"))

    class Meta:
        ordering = ["-published_at"]
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class VolunteerRegistration(models.Model):
    full_name = models.CharField(max_length=150, verbose_name=_("Full Name"))
    phone = models.CharField(max_length=20, verbose_name=_("Mobile Number"))
    email = models.EmailField(blank=True, verbose_name=_("Email Address"))
    village_mohalla = models.CharField(max_length=150, verbose_name=_("Village Mohalla / Hamlet"))
    skills_interest = models.CharField(
        max_length=255,
        verbose_name=_("Skills / Preferred Activity"),
        help_text=_("e.g., Gardening, Cleaning, Painting, Electrical, Accounts, Shramdaan")
    )
    availability = models.CharField(
        max_length=100,
        default="रविवार व अवकाश (Sundays & Holidays)",
        verbose_name=_("Time Availability")
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("NEW", _("New Request")),
            ("CONTACTED", _("Contacted / In Review")),
            ("ACTIVE", _("Active Volunteer")),
            ("INACTIVE", _("Inactive")),
        ],
        default="NEW",
        verbose_name=_("Volunteer Status")
    )
    notes = models.TextField(blank=True, verbose_name=_("Committee Remarks"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Volunteer Registration")
        verbose_name_plural = _("Volunteer Registrations")

    def __str__(self):
        return f"{self.full_name} ({self.phone}) - {self.get_status_display()}"


class ContactSubmission(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("Sender Name"))
    phone = models.CharField(max_length=20, verbose_name=_("Phone Number"))
    email = models.EmailField(blank=True, verbose_name=_("Email Address"))
    subject = models.CharField(max_length=200, verbose_name=_("Subject"))
    category = models.CharField(
        max_length=30,
        choices=[
            ("GENERAL", _("General Inquiry (सामान्य जानकारी)")),
            ("SUGGESTION", _("Suggestion (सुझाव)")),
            ("COMPLAINT", _("Complaint / Grievance (शिकायत)")),
            ("DONATION_QUERY", _("Donation Query (दान संबंधी प्रश्न)")),
            ("OTHER", _("Other (अन्य)")),
        ],
        default="GENERAL",
        verbose_name=_("Inquiry Category")
    )
    message = models.TextField(verbose_name=_("Message"))
    is_resolved = models.BooleanField(default=False, verbose_name=_("Resolved / Handled"))
    resolution_notes = models.TextField(blank=True, verbose_name=_("Resolution Notes"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Contact Submission")
        verbose_name_plural = _("Contact Submissions")

    def __str__(self):
        return f"[{self.get_category_display()}] {self.subject} by {self.name}"


class SiteSetting(models.Model):
    ngo_name = models.CharField(
        max_length=150,
        default="गाँव की बगिया (Ganv Ki Bagiya)",
        verbose_name=_("Initiative Name")
    )
    tagline = models.CharField(
        max_length=255,
        default="गाँव को हरा-भरा बनाना और बगिया व कब्रिस्तान को साफ़-सुथरा व सुरक्षित रखना, हम सबका संकल्प।",
        verbose_name=_("Tagline / Motto")
    )
    hero_title = models.CharField(
        max_length=255,
        default="गाँव की ज़मीन को हरा-भरा और कब्रिस्तान को साफ़-सुथरा बनाने की गाँव वालों की मुहिम",
        verbose_name=_("Hero Title")
    )
    hero_subtitle = models.TextField(
        default="गाँव वालों और दोस्तों की मदद से बेकार पड़ी ज़मीन पर हरी-भरी बगिया तैयार करने और कब्रिस्तान की साफ़-सफ़ाई, बाउंड्री और देखरेख का काम।",
        verbose_name=_("Hero Subtitle")
    )
    about_text = models.TextField(
        default="गाँव की बगिया हम सभी गाँव वालों की एक साझी कोशिश है। इसका मक़सद बेकार पड़ी ज़मीन को सुंदर व छायादार बगिया बनाना और कब्रिस्तान में चारदीवारी, पानी, रोशनी व साफ़-सफ़ाई का पक्का इंतज़ाम करना है। यहाँ मिलने वाले हर एक रुपये के दान का खुला हिसाब-किताब रखा जाता है ताकि हर कोई देख सके।",
        verbose_name=_("About Initiative")
    )
    contact_phone = models.CharField(max_length=50, default="+91 98765 43210", verbose_name=_("Helpline Phone"))
    contact_email = models.EmailField(default="contact@ganvkibagiya.org", verbose_name=_("Email Address"))
    address = models.CharField(
        max_length=255,
        default="ग्राम पंचायत भवन के सामने, मुख्य मार्ग, उत्तर प्रदेश - 226001",
        verbose_name=_("Physical Village Address")
    )
    map_link = models.URLField(
        default="https://maps.google.com",
        blank=True,
        verbose_name=_("Google Maps Link")
    )
    
    # Financial & UPI Details
    upi_id = models.CharField(max_length=100, default="ganvkibagiya@upi", verbose_name=_("UPI VPA ID"))
    upi_merchant_name = models.CharField(
        max_length=150,
        default="गाँव की बगिया कमेटी (Ganv Ki Bagiya)",
        verbose_name=_("UPI Payee Name")
    )
    bank_name = models.CharField(max_length=100, default="State Bank of India", verbose_name=_("Bank Name"))
    bank_account_number = models.CharField(max_length=50, default="38920194857", verbose_name=_("Bank Account Number"))
    bank_ifsc = models.CharField(max_length=25, default="SBIN0002134", verbose_name=_("IFSC Code"))
    bank_branch = models.CharField(max_length=100, default="Rural Main Branch", verbose_name=_("Branch"))
    
    # Committee Leadership
    president_name = models.CharField(max_length=100, default="हाजी मोहम्मद असलम (सदर / अध्यक्ष)", verbose_name=_("Committee President"))
    president_message = models.TextField(
        default="गाँव की भलाई और आने वाली पीढ़ी के लिए हर किसी का साथ बहुत ज़रूरी है। आपके दिए एक-एक रुपये का पूरा हिसाब इस वेबसाइट पर सबके सामने खुला है।",
        verbose_name=_("President's Message")
    )
    treasurer_name = models.CharField(max_length=100, default="जनाब मोहम्मद इरफान (खज़ांची / कोषाध्यक्ष)", verbose_name=_("Treasurer"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Site Setting & Info")
        verbose_name_plural = _("Site Settings & Info")

    def __str__(self):
        return f"{self.ngo_name} Settings"

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
