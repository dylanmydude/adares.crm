from django.test import TestCase

# Create your tests here.
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from finance.models import Expense, ExpenseCategory, Income, IncomeSource
from reports.models import GeneratedReport


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ReportsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='reports_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_reports_user',
            password='StrongPass123!',
        )
        self.source = IncomeSource.objects.create(user=self.user, name='Client Work')
        self.category = ExpenseCategory.objects.create(user=self.user, name='Fuel')
        self.other_source = IncomeSource.objects.create(user=self.other_user, name='Other Work')
        self.other_category = ExpenseCategory.objects.create(user=self.other_user, name='Other Fuel')
        Income.objects.create(
            user=self.user,
            source=self.source,
            amount='800.00',
            date_received='2026-06-15',
            description='Design work',
        )
        Expense.objects.create(
            user=self.user,
            category=self.category,
            amount='120.00',
            date_paid='2026-06-15',
            description='Trip fuel',
        )
        Income.objects.create(
            user=self.other_user,
            source=self.other_source,
            amount='999.00',
            date_received='2026-06-15',
        )
        Expense.objects.create(
            user=self.other_user,
            category=self.other_category,
            amount='99.00',
            date_paid='2026-06-15',
        )

    def test_report_page_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('report_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PDF Reports')
        self.assertContains(response, 'Income PDF report')
        self.assertContains(response, 'Expense PDF report')
        self.assertContains(response, 'Tax Summary PDF report')

    def test_pdf_generation_creates_report_record_and_file(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('report_generate', args=['income']))

        self.assertRedirects(response, reverse('report_list'))
        report = GeneratedReport.objects.get(user=self.user)
        self.assertEqual(report.report_type, GeneratedReport.REPORT_INCOME)
        self.assertTrue(report.file.name.startswith('reports/'))
        with report.file.open('rb') as pdf_file:
            content = pdf_file.read()
        self.assertTrue(content.startswith(b'%PDF-1.4'))
        self.assertIn(b'ADARES CRM', content)
        self.assertIn(b'Income report', content)
        self.assertIn(b'reports_user', content)
        self.assertIn(b'R800.00', content)
        self.assertIn(b'Design work', content)

    def test_all_required_report_types_generate(self):
        self.client.force_login(self.user)

        for report_type in ['income', 'expense', 'tax']:
            with self.subTest(report_type=report_type):
                response = self.client.post(reverse('report_generate', args=[report_type]))
                self.assertRedirects(response, reverse('report_list'))

        self.assertEqual(GeneratedReport.objects.filter(user=self.user).count(), 3)
        self.assertTrue(GeneratedReport.objects.filter(title='Income report').exists())
        self.assertTrue(GeneratedReport.objects.filter(title='Expense report').exists())
        self.assertTrue(GeneratedReport.objects.filter(title='Tax summary report').exists())

    def test_tax_pdf_contains_progressive_tax_values(self):
        self.client.force_login(self.user)

        self.client.post(reverse('report_generate', args=['tax']))

        report = GeneratedReport.objects.get(user=self.user, report_type=GeneratedReport.REPORT_TAX)
        with report.file.open('rb') as pdf_file:
            content = pdf_file.read()
        self.assertIn(b'Tax year: 2027', content)
        self.assertIn(b'Taxable income: R680.00', content)
        self.assertIn(b'Bracket calculation:', content)
        self.assertIn(b'Rebate: R17820.00', content)
        self.assertIn(b'Final estimated tax: R0.00', content)

    def test_reports_page_requires_login(self):
        response = self.client.get(reverse('report_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('report_list')}")

    def test_user_data_isolation_for_reports_and_downloads(self):
        self.client.force_login(self.user)
        self.client.post(reverse('report_generate', args=['income']))
        my_report = GeneratedReport.objects.get(user=self.user)

        self.client.force_login(self.other_user)
        self.client.post(reverse('report_generate', args=['expense']))
        other_report = GeneratedReport.objects.get(user=self.other_user)

        list_response = self.client.get(reverse('report_list'))
        self.assertContains(list_response, 'Expense report')
        self.assertNotContains(list_response, 'Income report')

        self.assertEqual(self.client.get(reverse('report_download', args=[my_report.pk])).status_code, 404)
        download_response = self.client.get(reverse('report_download', args=[other_report.pk]))
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response['Content-Type'], 'application/pdf')
