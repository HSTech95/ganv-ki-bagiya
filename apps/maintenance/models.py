from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from apps.projects.models import Project


class FacilityType(models.TextChoices):
    GARDEN = "GARDEN", _("Bagiya / Community Garden (गाँव की बगिया)")
    KABRISTAN = "KABRISTAN", _("Kabristan / Cemetery Grounds (कब्रिस्तान)")
    COMMON = "COMMON", _("Common Pathway & Utilities (साझा क्षेत्र व रास्ते)")


class TaskType(models.TextChoices):
    CLEANING = "CLEANING", _("Cleaning & Sanitation (सफाई व स्वच्छता)")
    WATERING = "WATERING", _("Watering Plants & Lawns (सिंचाई व फव्वारा)")
    TREE_PLANTATION = "TREE_PLANTATION", _("Tree Plantation & Care (पौधारोपण व निराई)")
    WALL_GATE_REPAIR = "WALL_GATE_REPAIR", _("Boundary Wall & Gate (चारदीवारी व गेट मरम्मत)")
    LIGHTING_ELECTRICAL = "LIGHTING_ELECTRICAL", _("Lighting & Solar (प्रकाश व सौर ऊर्जा)")
    DRAINAGE_PATHWAY = "DRAINAGE_PATHWAY", _("Drainage & Pathways (नाली व खडंजा मार्ग)")
    OTHER = "OTHER", _("Other Maintenance (अन्य रख-रखाव)")


class TaskPriority(models.TextChoices):
    LOW = "LOW", _("Low Priority (सामान्य)")
    MEDIUM = "MEDIUM", _("Medium Priority (मध्यम)")
    HIGH = "HIGH", _("High Priority (उच्च)")
    URGENT = "URGENT", _("Urgent / Emergency (अति आवश्यक)")


class TaskStatus(models.TextChoices):
    PENDING = "PENDING", _("Scheduled / Pending (लंबित)")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress (प्रगति पर)")
    COMPLETED = "COMPLETED", _("Completed (पूर्ण)")
    CANCELLED = "CANCELLED", _("Cancelled (निरस्त)")


class TaskFrequency(models.TextChoices):
    ONE_TIME = "ONE_TIME", _("One-Time Task (एक बार)")
    DAILY = "DAILY", _("Daily Routine (दैनिक)")
    WEEKLY = "WEEKLY", _("Weekly Schedule (साप्ताहिक)")
    MONTHLY = "MONTHLY", _("Monthly Schedule (मासिक)")


class MaintenanceTask(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Task Title"))
    facility = models.CharField(
        max_length=25,
        choices=FacilityType.choices,
        default=FacilityType.GARDEN,
        verbose_name=_("Facility / Location")
    )
    task_type = models.CharField(
        max_length=30,
        choices=TaskType.choices,
        default=TaskType.CLEANING,
        verbose_name=_("Task Type")
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_tasks",
        verbose_name=_("Linked Project (Optional)")
    )
    description = models.TextField(blank=True, verbose_name=_("Task Details / Instructions"))
    frequency = models.CharField(
        max_length=20,
        choices=TaskFrequency.choices,
        default=TaskFrequency.ONE_TIME,
        verbose_name=_("Frequency")
    )
    scheduled_date = models.DateField(default=timezone.now, verbose_name=_("Scheduled Date"))
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Due Date"))
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        verbose_name=_("Priority")
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        verbose_name=_("Status")
    )
    assigned_volunteer = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_maintenance_tasks",
        verbose_name=_("Assigned Volunteer / In-Charge")
    )
    
    # Progress & Completion
    completed_date = models.DateField(null=True, blank=True, verbose_name=_("Completion Date"))
    completion_notes = models.TextField(blank=True, verbose_name=_("Completion Report / Notes"))
    before_photo = models.ImageField(
        upload_to="maintenance/before/",
        blank=True,
        null=True,
        verbose_name=_("Before Photo")
    )
    after_photo = models.ImageField(
        upload_to="maintenance/after/",
        blank=True,
        null=True,
        verbose_name=_("After Photo")
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="created_tasks",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date", "-priority"]
        verbose_name = _("Maintenance Task")
        verbose_name_plural = _("Maintenance Tasks")

    def __str__(self):
        return f"[{self.get_facility_display()}] {self.title} - {self.get_status_display()}"
