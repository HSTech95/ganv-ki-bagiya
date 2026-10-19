from django.test import TestCase, Client
from django.urls import reverse
from apps.content.models import SiteSetting, ContactSubmission, VolunteerRegistration


class PublicContentPagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.site_settings = SiteSetting.load()
        self.site_settings.site_name = "गाँव की बगिया"
        self.site_settings.save()

    def test_homepage_renders_successfully(self):
        response = self.client.get(reverse("public:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "गाँव की बगिया")

    def test_about_page_renders_successfully(self):
        response = self.client.get(reverse("public:about"))
        self.assertEqual(response.status_code, 200)

    def test_contact_form_submission(self):
        response = self.client.post(reverse("public:contact"), {
            "name": "Kamil Akhtar",
            "phone": "9812345678",
            "email": "kamil@example.com",
            "category": "SUGGESTION",
            "subject": "सुझाव",
            "message": "बगिया में बच्चों के लिए भी कुछ झूले लगाए जाएं।"
        })
        self.assertEqual(response.status_code, 302)
        submission = ContactSubmission.objects.filter(phone="9812345678").first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.name, "Kamil Akhtar")

    def test_volunteer_registration_submission(self):
        response = self.client.post(reverse("public:volunteer"), {
            "full_name": "Zubair Khan",
            "phone": "9876501234",
            "email": "zubair@example.com",
            "village_mohalla": "उत्तर टोला",
            "skills_interest": "पौधारोपण व नल मरम्मत",
            "availability": "रविवार सुबह"
        })
        self.assertEqual(response.status_code, 302)
        vol = VolunteerRegistration.objects.filter(phone="9876501234").first()
        self.assertIsNotNone(vol)
        self.assertEqual(vol.full_name, "Zubair Khan")
