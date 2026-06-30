from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crm.models import Client
from finance.models import Expense, ExpenseCategory, Income, IncomeSource
from invoicing.models import Invoice, InvoiceItem
from notifications.models import Notification


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
        self.assertContains(response, 'images/adares-logo.png')

    def test_dashboard_shows_recent_records(self):
        user = get_user_model().objects.create_user(
            username='recent_user',
            password='StrongPass123!',
        )
        source = IncomeSource.objects.create(user=user, name='Delivery')
        category = ExpenseCategory.objects.create(user=user, name='Fuel')
        client = Client.objects.create(user=user, name='Recent Client')
        invoice = Invoice.objects.create(
            user=user,
            client=client,
            invoice_number='INV-RECENT',
            status=Invoice.STATUS_SENT,
            issue_date='2026-06-15',
            due_date='2026-06-30',
        )
        InvoiceItem.objects.create(invoice=invoice, description='Work', quantity=2, unit_price='100.00')
        Income.objects.create(user=user, source=source, amount='300.00', date_received='2026-06-15')
        Expense.objects.create(user=user, category=category, amount='75.00', date_paid='2026-06-15')
        Notification.objects.create(
            user=user,
            notification_type=Notification.TYPE_REPORT_GENERATED,
            title='Report generated',
            message='Ready.',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Recent Income')
        self.assertContains(response, 'Delivery')
        self.assertContains(response, 'Recent Expenses')
        self.assertContains(response, 'Fuel')
        self.assertContains(response, 'Recent Invoices')
        self.assertContains(response, 'INV-RECENT')
        self.assertContains(response, 'Unread Notifications')
        self.assertContains(response, 'Report generated')


class FinalNavigationAndAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='nav_user',
            password='StrongPass123!',
        )

    def test_main_navigation_links_render_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        expected_links = [
            reverse('dashboard'),
            reverse('income_list'),
            reverse('expense_list'),
            reverse('client_list'),
            reverse('job_list'),
            reverse('invoice_list'),
            reverse('tax_summary'),
            reverse('report_list'),
            reverse('backup_page'),
            reverse('notification_list'),
            reverse('profile'),
            reverse('account_settings'),
            reverse('logout'),
        ]
        for link in expected_links:
            with self.subTest(link=link):
                self.assertContains(response, f'href="{link}"')
        self.assertNotContains(response, f'href="{reverse("audit_log_list")}"')
        self.assertNotContains(response, f'href="{reverse("management_user_list")}"')

    def test_admin_navigation_links_render_for_staff_user(self):
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, f'href="{reverse("audit_log_list")}"')
        self.assertContains(response, f'href="{reverse("management_user_list")}"')

    def test_protected_pages_redirect_to_login(self):
        protected_urls = [
            reverse('dashboard'),
            reverse('profile'),
            reverse('account_settings'),
            reverse('income_list'),
            reverse('income_create'),
            reverse('expense_list'),
            reverse('expense_create'),
            reverse('client_list'),
            reverse('client_create'),
            reverse('job_list'),
            reverse('job_create'),
            reverse('invoice_list'),
            reverse('invoice_create'),
            reverse('tax_summary'),
            reverse('report_list'),
            reverse('backup_page'),
            reverse('notification_list'),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_main_pages_load_for_authenticated_user(self):
        self.client.force_login(self.user)
        main_pages = [
            reverse('dashboard'),
            reverse('profile'),
            reverse('account_settings'),
            reverse('income_list'),
            reverse('expense_list'),
            reverse('client_list'),
            reverse('job_list'),
            reverse('invoice_list'),
            reverse('tax_summary'),
            reverse('report_list'),
            reverse('backup_page'),
            reverse('notification_list'),
        ]

        for url in main_pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_admin_pages_load_for_staff_user(self):
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        self.client.force_login(self.user)

        for url in [reverse('audit_log_list'), reverse('management_user_list')]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
