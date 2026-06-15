from decimal import Decimal

from django.db.models import Sum

from finance.models import Expense, Income

from .models import TaxCalculation

TAX_RATE = Decimal('0.20')


def calculate_tax_values(user):
    total_income = _sum_amount(Income.objects.filter(user=user))
    total_expenses = _sum_amount(Expense.objects.filter(user=user))
    taxable_profit = total_income - total_expenses
    estimated_tax = max(taxable_profit, Decimal('0.00')) * TAX_RATE

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'taxable_profit': taxable_profit,
        'estimated_tax': estimated_tax,
    }


def save_tax_calculation(user):
    values = calculate_tax_values(user)
    calculation = TaxCalculation.objects.create(user=user, **values)
    return calculation


def _sum_amount(queryset):
    return queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
