from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Expense, ExpenseCategory, Income, IncomeSource


class FinanceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='finance_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_user',
            password='StrongPass123!',
        )

    def test_income_crud(self):
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('income_create'),
            {
                'source_name': 'Delivery App',
                'amount': '450.50',
                'date_received': '2026-06-14',
                'description': 'Weekend deliveries',
            },
        )

        self.assertRedirects(create_response, reverse('income_list'))
        income = Income.objects.get(user=self.user)
        self.assertEqual(income.source.name, 'Delivery App')
        self.assertEqual(income.amount, Decimal('450.50'))

        list_response = self.client.get(reverse('income_list'))
        self.assertContains(list_response, 'Delivery App')
        self.assertContains(list_response, 'R450.50')

        edit_response = self.client.post(
            reverse('income_edit', args=[income.pk]),
            {
                'source_name': 'Private Client',
                'amount': '500.00',
                'date_received': '2026-06-15',
                'description': 'Updated income',
            },
        )

        self.assertRedirects(edit_response, reverse('income_list'))
        income.refresh_from_db()
        self.assertEqual(income.source.name, 'Private Client')
        self.assertEqual(income.amount, Decimal('500.00'))

        delete_response = self.client.post(reverse('income_delete', args=[income.pk]))

        self.assertRedirects(delete_response, reverse('income_list'))
        self.assertFalse(Income.objects.filter(pk=income.pk).exists())

    def test_expense_crud(self):
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('expense_create'),
            {
                'category_name': 'Fuel',
                'amount': '120.25',
                'date_paid': '2026-06-14',
                'description': 'Fuel for work trips',
            },
        )

        self.assertRedirects(create_response, reverse('expense_list'))
        expense = Expense.objects.get(user=self.user)
        self.assertEqual(expense.category.name, 'Fuel')
        self.assertEqual(expense.amount, Decimal('120.25'))

        list_response = self.client.get(reverse('expense_list'))
        self.assertContains(list_response, 'Fuel')
        self.assertContains(list_response, 'R120.25')

        edit_response = self.client.post(
            reverse('expense_edit', args=[expense.pk]),
            {
                'category_name': 'Airtime',
                'amount': '80.00',
                'date_paid': '2026-06-15',
                'description': 'Updated expense',
            },
        )

        self.assertRedirects(edit_response, reverse('expense_list'))
        expense.refresh_from_db()
        self.assertEqual(expense.category.name, 'Airtime')
        self.assertEqual(expense.amount, Decimal('80.00'))

        delete_response = self.client.post(reverse('expense_delete', args=[expense.pk]))

        self.assertRedirects(delete_response, reverse('expense_list'))
        self.assertFalse(Expense.objects.filter(pk=expense.pk).exists())

    def test_user_data_isolation_for_income_and_expenses(self):
        source = IncomeSource.objects.create(user=self.user, name='My Source')
        other_source = IncomeSource.objects.create(user=self.other_user, name='Other Source')
        category = ExpenseCategory.objects.create(user=self.user, name='My Category')
        other_category = ExpenseCategory.objects.create(user=self.other_user, name='Other Category')
        income = Income.objects.create(
            user=self.user,
            source=source,
            amount='100.00',
            date_received='2026-06-14',
        )
        other_income = Income.objects.create(
            user=self.other_user,
            source=other_source,
            amount='999.00',
            date_received='2026-06-14',
        )
        expense = Expense.objects.create(
            user=self.user,
            category=category,
            amount='40.00',
            date_paid='2026-06-14',
        )
        other_expense = Expense.objects.create(
            user=self.other_user,
            category=other_category,
            amount='888.00',
            date_paid='2026-06-14',
        )

        self.client.force_login(self.user)

        income_response = self.client.get(reverse('income_list'))
        self.assertContains(income_response, 'My Source')
        self.assertNotContains(income_response, 'Other Source')

        expense_response = self.client.get(reverse('expense_list'))
        self.assertContains(expense_response, 'My Category')
        self.assertNotContains(expense_response, 'Other Category')

        self.assertEqual(self.client.get(reverse('income_edit', args=[other_income.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('income_delete', args=[other_income.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('expense_edit', args=[other_expense.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('expense_delete', args=[other_expense.pk])).status_code, 404)
        self.assertTrue(Income.objects.filter(pk=income.pk).exists())
        self.assertTrue(Expense.objects.filter(pk=expense.pk).exists())

    def test_finance_pages_require_login(self):
        protected_urls = [
            reverse('income_list'),
            reverse('income_create'),
            reverse('expense_list'),
            reverse('expense_create'),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_dashboard_uses_current_user_totals(self):
        source = IncomeSource.objects.create(user=self.user, name='Work')
        other_source = IncomeSource.objects.create(user=self.other_user, name='Other Work')
        category = ExpenseCategory.objects.create(user=self.user, name='Fuel')
        other_category = ExpenseCategory.objects.create(user=self.other_user, name='Other Fuel')
        Income.objects.create(user=self.user, source=source, amount='300.00', date_received='2026-06-14')
        Expense.objects.create(user=self.user, category=category, amount='60.00', date_paid='2026-06-14')
        Income.objects.create(user=self.other_user, source=other_source, amount='900.00', date_received='2026-06-14')
        Expense.objects.create(user=self.other_user, category=other_category, amount='100.00', date_paid='2026-06-14')

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'R300.00')
        self.assertContains(response, 'R60.00')
        self.assertContains(response, 'R240.00')
        self.assertContains(response, 'R48.00')
        self.assertNotContains(response, 'R900.00')
