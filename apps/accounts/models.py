from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", _("Super Admin")
    TREASURER = "TREASURER", _("Treasurer (खजांची / कोषाध्यक्ष)")
    PRESIDENT = "PRESIDENT", _("Committee President (सदर / अध्यक्ष)")
    PROJECT_MANAGER = "PROJECT_MANAGER", _("Project Manager (कार्य प्रबंधक)")
    VOLUNTEER = "VOLUNTEER", _("Volunteer (स्वयंसेवक)")
    PUBLIC = "PUBLIC", _("Public Donor / Resident (ग्रामीण / दानदाता)")


class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=25,
        choices=UserRole.choices,
        default=UserRole.PUBLIC,
        help_text=_("Designated system role and permission tier")
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Primary contact mobile number")
    )
    village_address = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Mohalla / Hamlet / Village address")
    )
    profile_photo = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        full = self.get_full_name()
        return f"{full or self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.is_superuser or self.role == UserRole.SUPER_ADMIN

    @property
    def is_treasurer(self):
        return self.is_super_admin or self.role == UserRole.TREASURER

    @property
    def is_president(self):
        return self.is_super_admin or self.role == UserRole.PRESIDENT

    @property
    def is_project_manager(self):
        return self.is_super_admin or self.role in [UserRole.PROJECT_MANAGER, UserRole.PRESIDENT]

    @property
    def is_volunteer(self):
        return self.role in [UserRole.VOLUNTEER, UserRole.PROJECT_MANAGER, UserRole.TREASURER, UserRole.PRESIDENT, UserRole.SUPER_ADMIN]

    @property
    def can_manage_finances(self):
        return self.is_super_admin or self.role in [UserRole.TREASURER, UserRole.PRESIDENT]

    @property
    def can_approve_expenses(self):
        """Committee President and Super Admin approve expenses; Treasurer cannot approve their own paid entries"""
        return self.is_super_admin or self.role == UserRole.PRESIDENT

    @property
    def can_record_payments(self):
        return self.is_super_admin or self.role == UserRole.TREASURER


class AuditLog(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=100)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} - {self.action}"
