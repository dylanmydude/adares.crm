from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardShellTests(TestCase):
    def test_dashboard_loads_frontend_shell(self):
        user = get_user_model().objects.create_user(
            username='dashboard_user',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ADARES CRM')
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Total Income')
        self.assertContains(response, 'Total Expenses')
        self.assertContains(response, 'Net Profit')
        self.assertContains(response, 'Estimated Tax')
        self.assertContains(response, 'css/adares-theme.css')
        self.assertContains(response, 'js/app.js')
