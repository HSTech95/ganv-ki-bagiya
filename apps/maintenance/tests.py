from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import CustomUser, UserRole
from apps.maintenance.models import MaintenanceTask, FacilityType, TaskType, TaskPriority, TaskStatus


class MaintenanceTestCase(TestCase):
    def setUp(self):
        self.manager = CustomUser.objects.create_user(
            username="manager_maint",
            email="manager_maint@bagiya.org",
            password="Password@123",
            role=UserRole.PROJECT_MANAGER,
            is_staff=True
        )

    def test_maintenance_task_creation_and_completion(self):
        task = MaintenanceTask.objects.create(
            title="Weekly Garden Watering & Weeding",
            facility=FacilityType.GARDEN,
            task_type=TaskType.WATERING,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            scheduled_date=timezone.now().date() + timedelta(days=2),
            created_by=self.manager
        )
        self.assertEqual(task.status, TaskStatus.PENDING)

        task.status = TaskStatus.COMPLETED
        task.completion_notes = "Watered all sectors and removed weed bushes."
        task.completed_at = timezone.now()
        task.save()

        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
