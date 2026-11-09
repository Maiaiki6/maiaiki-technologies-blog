from django.test import TestCase
from django.urls import reverse

from .models import QuoteRequest


class QuoteRequestTests(TestCase):
    def test_services_page_loads(self):
        response = self.client.get(reverse("shop:services"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Screen repair")
        self.assertContains(response, "Pricing")

    def test_quote_form_saves_request(self):
        response = self.client.post(
            reverse("shop:quote"),
            {
                "full_name": "Jane Doe",
                "phone": "07000000000",
                "device": "iPhone 13",
                "issue": "Cracked screen",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(QuoteRequest.objects.count(), 1)
        self.assertEqual(QuoteRequest.objects.first().device, "iPhone 13")

    def test_quote_form_rejects_honeypot_submission(self):
        response = self.client.post(
            reverse("shop:quote"),
            {
                "full_name": "Bot User",
                "phone": "07000000000",
                "device": "iPhone 14",
                "issue": "Spam",
                "website": "https://example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)
        self.assertContains(response, "Please try again")

    def test_seo_files_are_available(self):
        robots_response = self.client.get("/robots.txt")
        sitemap_response = self.client.get("/sitemap.xml")

        self.assertEqual(robots_response.status_code, 200)
        self.assertContains(robots_response, "User-agent")
        self.assertEqual(sitemap_response.status_code, 200)
        self.assertContains(sitemap_response, "<urlset")

    def test_deploy_security_and_static_settings_are_present(self):
        from django.conf import settings

        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings.MIDDLEWARE)
        self.assertEqual(
            settings.STATICFILES_STORAGE,
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
        )
        self.assertFalse(settings.SECURE_SSL_REDIRECT)
        self.assertFalse(settings.SESSION_COOKIE_SECURE)
        self.assertFalse(settings.CSRF_COOKIE_SECURE)
