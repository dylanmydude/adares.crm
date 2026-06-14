from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from decimal import Decimal

from finance.models import Expense, Income


@login_required
def dashboard(request):
    total_income = _sum_amount(Income.objects.filter(user=request.user))
    total_expenses = _sum_amount(Expense.objects.filter(user=request.user))
    net_profit = total_income - total_expenses
    estimated_tax = max(net_profit, Decimal('0.00')) * Decimal('0.20')

    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'estimated_tax': estimated_tax,
    }
    return render(request, 'dashboard.html', context)


def _sum_amount(queryset):
    return queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
