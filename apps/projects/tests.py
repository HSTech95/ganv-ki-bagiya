from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.projects.models import Project, ProjectStatus
from apps.expenses.models import Expense, ExpenseCategory, ExpensePaymentStatus


class ProjectsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = CustomUser.objects.create_user(
            username="manager_proj",
            email="manager_proj@bagiya.org",
            password="Password@123",
            role=UserRole.PROJECT_MANAGER,
            is_staff=True
        )
        self.project = Project.objects.create(
            name="Kabristan Boundary Wall & Gate",
            slug="kabristan-boundary-wall",
            project_type="KABRISTAN",
            description="Boundary wall construction and gate",
            estimated_budget=Decimal("150000.00"),
            start_date=date.today(),
            status=ProjectStatus.ACTIVE,
            progress_percentage=60,
            manager=self.manager,
            is_public=True
        )
        # Create paid expense to test actual_expenditure & remaining_budget
        Expense.objects.create(
            category=ExpenseCategory.BOUNDARY_WALL,
            description="Bricks & Cement for Wall",
            amount=Decimal("45000.00"),
            vendor_name="National Traders",
            related_project=self.project,
            payment_status=ExpensePaymentStatus.PAID,
            paid_date=date.today(),
            created_by=self.manager
        )

    def test_project_budget_calculations(self):
        self.assertEqual(self.project.actual_expenditure, Decimal("45000.00"))
        self.assertEqual(self.project.remaining_budget, 105000.00)
        self.assertEqual(self.project.progress_percentage, 60)

    def test_public_projects_list_view(self):
        response = self.client.get(reverse("projects:public_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kabristan Boundary Wall &amp; Gate")
