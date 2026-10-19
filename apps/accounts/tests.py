from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import CustomUser, UserRole, AuditLog


class AccountsRolesAndAccessTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            username="test_admin",
            email="admin@test.com",
            password="Password@123",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.president = CustomUser.objects.create_user(
            username="test_president",
            email="pres@test.com",
            password="Password@123",
            role=UserRole.PRESIDENT,
            is_staff=True
        )
        self.treasurer = CustomUser.objects.create_user(
            username="test_treasurer",
            email="treas@test.com",
            password="Password@123",
            role=UserRole.TREASURER,
            is_staff=True
        )
        self.volunteer = CustomUser.objects.create_user(
            username="test_volunteer",
            email="vol@test.com",
            password="Password@123",
            role=UserRole.VOLUNTEER,
            is_staff=False
        )
        self.public_user = CustomUser.objects.create_user(
            username="test_public",
            email="public@test.com",
            password="Password@123",
            role=UserRole.PUBLIC,
            is_staff=False
        )

    def test_role_properties_and_segregation_of_duties(self):
        # President can approve expenses, cannot record payments
        self.assertTrue(self.president.can_approve_expenses)
        self.assertFalse(self.president.can_record_payments)

        # Treasurer can record payments, cannot approve expenses
        self.assertTrue(self.treasurer.can_record_payments)
        self.assertFalse(self.treasurer.can_approve_expenses)

        # Both can manage finances
        self.assertTrue(self.president.can_manage_finances)
        self.assertTrue(self.treasurer.can_manage_finances)

        # Super Admin has full authority
        self.assertTrue(self.admin.can_approve_expenses)
        self.assertTrue(self.admin.can_record_payments)
        self.assertTrue(self.admin.is_super_admin)

        # Public user has no admin privileges
        self.assertFalse(self.public_user.can_manage_finances)
        self.assertFalse(self.public_user.can_approve_expenses)

    def test_unauthenticated_user_redirected_from_dashboard(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_public_user_redirected_from_dashboard_home(self):
        self.client.force_login(self.public_user)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("public:home"))

    def test_staff_user_can_access_dashboard(self):
        self.client.force_login(self.treasurer)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)

    def test_login_creates_audit_log(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "test_treasurer",
            "password": "Password@123"
        })
        self.assertEqual(response.status_code, 302)
        log = AuditLog.objects.filter(user=self.treasurer, action="USER_LOGIN").first()
        self.assertIsNotNone(log)
