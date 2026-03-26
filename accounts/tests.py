from django.test import TestCase
from django.urls import reverse

from .models import Account


class AccountDashboardTests(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            first_name="Amy",
            last_name="Buyer",
            username="amy",
            email="amy@example.com",
            password="secret123",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Overview")

    def test_orders_tab_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("account_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order History")
