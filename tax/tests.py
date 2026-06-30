from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from finance.models import Expense, ExpenseCategory, Income, IncomeSource

from .models import TaxCalculation
from .services import calculate_tax_before_rebates, calculate_tax_values


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

    def add_finance_records(self, income='300000.00', expense='0.00'):
        Income.objects.create(user=self.user, source=self.source, amount=income, date_received='2026-06-15')
        if Decimal(expense) > 0:
            Expense.objects.create(user=self.user, category=self.category, amount=expense, date_paid='2026-06-15')
        Income.objects.create(user=self.other_user, source=self.other_source, amount='999999.00', date_received='2026-06-15')
        Expense.objects.create(user=self.other_user, category=self.other_category, amount='100.00', date_paid='2026-06-15')

    def test_tax_summary_saves_calculation_and_shows_disclaimer(self):
        self.add_finance_records()
        self.client.force_login(self.user)

        response = self.client.get(reverse('tax_summary'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tax Summary')
        self.assertContains(response, 'not official tax advice')
        self.assertContains(response, 'assumes the user is younger than 65')
        self.assertContains(response, 'R300000.00')
        self.assertContains(response, 'R58392.00')
        self.assertContains(response, 'R17820.00')
        self.assertContains(response, 'R40572.00')
        calculation = TaxCalculation.objects.get(user=self.user)
        self.assertEqual(calculation.tax_year, 2027)
        self.assertEqual(calculation.gross_income, Decimal('300000.00'))
        self.assertEqual(calculation.deductible_expenses, Decimal('0.00'))
        self.assertEqual(calculation.taxable_income, Decimal('300000.00'))
        self.assertEqual(calculation.tax_before_rebates, Decimal('58392.00'))
        self.assertEqual(calculation.rebate_amount, Decimal('17820.00'))
        self.assertEqual(calculation.estimated_tax, Decimal('40572.00'))

    def test_each_tax_bracket_before_rebates(self):
        cases = [
            ('245100.00', '44118.00'),
            ('300000.00', '58392.00'),
            ('400000.00', '85237.00'),
            ('600000.00', '150727.00'),
            ('800000.00', '225853.00'),
            ('1000000.00', '306113.00'),
            ('2000000.00', '720969.00'),
        ]

        for taxable_income, expected_tax in cases:
            with self.subTest(taxable_income=taxable_income):
                tax, _description = calculate_tax_before_rebates(Decimal(taxable_income))
                self.assertEqual(tax, Decimal(expected_tax))

    def test_bracket_boundaries(self):
        cases = [
            ('245099.00', '44117.82'),
            ('245100.00', '44118.00'),
            ('245101.00', '44118.26'),
            ('383100.00', '79998.00'),
            ('383101.00', '79998.31'),
            ('530200.00', '125599.00'),
            ('530201.00', '125599.36'),
            ('695800.00', '185215.00'),
            ('695801.00', '185215.39'),
            ('887000.00', '259783.00'),
            ('887001.00', '259783.41'),
            ('1878600.00', '666339.00'),
            ('1878601.00', '666339.45'),
        ]

        for taxable_income, expected_tax in cases:
            with self.subTest(taxable_income=taxable_income):
                tax, _description = calculate_tax_before_rebates(Decimal(taxable_income))
                self.assertEqual(tax, Decimal(expected_tax))

    def test_under_65_rebate_and_threshold(self):
        self.add_finance_records(income='99000.00')

        values = calculate_tax_values(self.user)

        self.assertEqual(values['rebate_amount'], Decimal('17820.00'))
        self.assertEqual(values['threshold'], Decimal('99000.00'))
        self.assertEqual(values['estimated_tax'], Decimal('0.00'))

    def test_age_65_rebate_and_threshold(self):
        UserProfile.objects.create(user=self.user, date_of_birth=date(1961, 2, 28))
        self.add_finance_records(income='153250.00')

        values = calculate_tax_values(self.user)

        self.assertEqual(values['rebate_amount'], Decimal('27585.00'))
        self.assertEqual(values['threshold'], Decimal('153250.00'))
        self.assertEqual(values['estimated_tax'], Decimal('0.00'))

    def test_age_75_rebate_and_threshold(self):
        UserProfile.objects.create(user=self.user, date_of_birth=date(1951, 2, 28))
        self.add_finance_records(income='171300.00')

        values = calculate_tax_values(self.user)

        self.assertEqual(values['rebate_amount'], Decimal('30834.00'))
        self.assertEqual(values['threshold'], Decimal('171300.00'))
        self.assertEqual(values['estimated_tax'], Decimal('0.00'))

    def test_tax_calculation_negative_profit_has_zero_estimated_tax(self):
        self.add_finance_records(income='100.00', expense='250.00')

        values = calculate_tax_values(self.user)

        self.assertEqual(values['gross_income'], Decimal('100.00'))
        self.assertEqual(values['deductible_expenses'], Decimal('250.00'))
        self.assertEqual(values['taxable_income'], Decimal('-150.00'))
        self.assertEqual(values['estimated_tax'], Decimal('0.00'))

    def test_user_data_isolation_for_tax_history(self):
        self.add_finance_records()
        TaxCalculation.objects.create(
            user=self.other_user,
            tax_year=2027,
            gross_income='999999.00',
            deductible_expenses='100.00',
            taxable_income='999899.00',
            tax_before_rebates='306071.59',
            rebate_amount='17820.00',
            estimated_tax='288251.59',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('tax_summary'))

        self.assertContains(response, 'R40572.00')
        self.assertNotContains(response, 'R288251.59')
        self.assertEqual(TaxCalculation.objects.filter(user=self.user).count(), 1)

    def test_tax_page_requires_login(self):
        response = self.client.get(reverse('tax_summary'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('tax_summary')}")

    def test_dashboard_tax_value_uses_same_calculation(self):
        self.add_finance_records()
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'R300000.00')
        self.assertContains(response, 'R40572.00')
        self.assertNotContains(response, 'R999999.00')
