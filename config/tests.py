from django.test import SimpleTestCase
from django.urls import reverse


class DashboardShellTests(SimpleTestCase):
    def test_dashboard_loads_frontend_shell(self):
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
