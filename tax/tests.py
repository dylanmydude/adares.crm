from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Expense, ExpenseCategory, Income, IncomeSource

from .models import TaxCalculation
from .services import calculate_tax_values


class TaxTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='tax_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_tax_user',
            password='StrongPass123!',
        )
        self.source = IncomeSource.objects.create(user=self.user, name='Work')
        self.category = ExpenseCategory.objects.create(user=self.user, name='Fuel')
        self.other_source = IncomeSource.objects.create(user=self.other_user, name='Other Work')
        self.other_category = ExpenseCategory.objects.create(user=self.other_user, name='Other Fuel')

    def add_finance_records(self):
        Income.objects.create(
            user=self.user,
            source=self.source,
            amount='1000.00',
            date_received='2026-06-15',
        )
        Expense.objects.create(
            user=self.user,
            category=self.category,
            amount='250.00',
            date_paid='2026-06-15',
        )
        Income.objects.create(
            user=self.other_user,
            source=self.other_source,
            amount='9999.00',
            date_received='2026-06-15',
        )
        Expense.objects.create(
            user=self.other_user,
            category=self.other_category,
            amount='100.00',
            date_paid='2026-06-15',
        )

    def test_tax_summary_saves_calculation_and_shows_disclaimer(self):
        self.add_finance_records()
        self.client.force_login(self.user)

        response = self.client.get(reverse('tax_summary'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tax Summary')
        self.assertContains(response, 'not official tax advice')
        self.assertContains(response, 'R1000.00')
        self.assertContains(response, 'R250.00')
        self.assertContains(response, 'R750.00')
        self.assertContains(response, 'R150.00')
        calculation = TaxCalculation.objects.get(user=self.user)
        self.assertEqual(calculation.total_income, Decimal('1000.00'))
        self.assertEqual(calculation.total_expenses, Decimal('250.00'))
        self.assertEqual(calculation.taxable_profit, Decimal('750.00'))
        self.assertEqual(calculation.estimated_tax, Decimal('150.00'))

    def test_tax_calculation_negative_profit_has_zero_estimated_tax(self):
        Income.objects.create(
            user=self.user,
            source=self.source,
            amount='100.00',
            date_received='2026-06-15',
        )
        Expense.objects.create(
            user=self.user,
            category=self.category,
            amount='250.00',
            date_paid='2026-06-15',
        )

        values = calculate_tax_values(self.user)

        self.assertEqual(values['total_income'], Decimal('100.00'))
        self.assertEqual(values['total_expenses'], Decimal('250.00'))
        self.assertEqual(values['taxable_profit'], Decimal('-150.00'))
        self.assertEqual(values['estimated_tax'], Decimal('0.0000'))

    def test_user_data_isolation_for_tax_history(self):
        self.add_finance_records()
        TaxCalculation.objects.create(
            user=self.other_user,
            total_income='9999.00',
            total_expenses='100.00',
            taxable_profit='9899.00',
            estimated_tax='1979.80',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('tax_summary'))

        self.assertContains(response, 'R150.00')
        self.assertNotContains(response, 'R1979.80')
        self.assertEqual(TaxCalculation.objects.filter(user=self.user).count(), 1)

    def test_tax_page_requires_login(self):
        response = self.client.get(reverse('tax_summary'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('tax_summary')}")

    def test_dashboard_tax_value_uses_same_calculation(self):
        self.add_finance_records()
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'R1000.00')
        self.assertContains(response, 'R250.00')
        self.assertContains(response, 'R750.00')
        self.assertContains(response, 'R150.00')
        self.assertNotContains(response, 'R9999.00')
