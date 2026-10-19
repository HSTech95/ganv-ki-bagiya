# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.utils.text import slugify
# pyrefly: ignore [missing-import]
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser


class ProjectType(models.TextChoices):
    GARDEN = "GARDEN", _("बगिया विकास (Garden Development)")
    KABRISTAN = "KABRISTAN", _("कब्रिस्तान की देखरेख (Kabristan Care)")
    INFRASTRUCTURE = "INFRASTRUCTURE", _("साझा निर्माण कार्य (Joint Infrastructure)")


class ProjectStatus(models.TextChoices):
    PLANNING = "PLANNING", _("तैयारी चल रही है (Planning)")
    ACTIVE = "ACTIVE", _("काम चालू है (In Progress)")
    COMPLETED = "COMPLETED", _("काम पूरा हुआ (Completed)")
    ON_HOLD = "ON_HOLD", _("कुछ समय के लिए रुका (On Hold)")


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("प्रोजेक्ट का नाम (Project Name)"))
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    project_type = models.CharField(
        max_length=30,
        choices=ProjectType.choices,
        default=ProjectType.GARDEN,
        verbose_name=_("प्रोजेक्ट का प्रकार (Category)")
    )
    description = models.TextField(verbose_name=_("विस्तार से जानकारी (Description)"))
    objectives = models.TextField(verbose_name=_("मुख्य लक्ष्य (Objectives)"), blank=True)
    estimated_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("तय बजट (Budget ₹)")
    )
    start_date = models.DateField(verbose_name=_("शुरू होने की तारीख (Start Date)"))
    target_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("पूरा होने की तारीख (Target Date)")
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        verbose_name=_("काम की स्थिति (Status)")
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        verbose_name=_("कितना काम हुआ (% Progress)"),
        help_text=_("0 से 100 प्रतिशत")
    )
    featured_image = models.ImageField(
        upload_to="projects/",
        blank=True,
        null=True,
        verbose_name=_("मुख्य फ़ोटो (Photo)")
    )
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
        verbose_name=_("देखरेख करने वाले (Manager)")
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_("वेबसाइट पर दिखाएं (Public)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("प्रोजेक्ट (Project)")
        verbose_name_plural = _("प्रोजेक्ट्स (Projects)")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "project"
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def actual_expenditure(self):
        """Sum of actual paid expenses allocated to this project"""
        from apps.expenses.models import ExpensePaymentStatus
        total = self.expenses.filter(
            payment_status=ExpensePaymentStatus.PAID
        ).aggregate(total=models.Sum("amount"))["total"]
        return total or 0

    @property
    def total_funds_received(self):
        """Sum of confirmed donations specifically earmarked for this project"""
        from apps.donations.models import PaymentStatus
        total = self.donations.filter(
            payment_status=PaymentStatus.CONFIRMED
        ).aggregate(total=models.Sum("amount"))["total"]
        return total or 0

    @property
    def remaining_budget(self):
        return max(0, float(self.estimated_budget) - float(self.actual_expenditure))


class ProjectUpdate(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="updates",
        verbose_name=_("प्रोजेक्ट (Project)")
    )
    title = models.CharField(max_length=200, verbose_name=_("अपडेट की हेडिंग (Title)"))
    content = models.TextField(verbose_name=_("काम का विवरण (Progress Details)"))
    update_date = models.DateField(verbose_name=_("तारीख (Date)"))
    photo = models.ImageField(
        upload_to="project_updates/",
        blank=True,
        null=True,
        verbose_name=_("काम की फ़ोटो (Photo)")
    )
    posted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("अपडेट करने वाले (Posted By)")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-update_date", "-created_at"]
        verbose_name = _("प्रोजेक्ट अपडेट (Project Update)")
        verbose_name_plural = _("प्रोजेक्ट अपडेट्स (Project Updates)")

    def __str__(self):
        return f"{self.project.name} - {self.title} ({self.update_date})"
