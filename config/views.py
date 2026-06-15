from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from finance.models import Expense, Income
from invoicing.models import Invoice
from notifications.models import Notification
from tax.services import calculate_tax_values


@login_required
def dashboard(request):
    tax_values = calculate_tax_values(request.user)
    net_profit = tax_values['taxable_profit']

    context = {
        'total_income': tax_values['total_income'],
        'total_expenses': tax_values['total_expenses'],
        'net_profit': net_profit,
        'estimated_tax': tax_values['estimated_tax'],
        'recent_income': Income.objects.filter(user=request.user).select_related('source')[:5],
        'recent_expenses': Expense.objects.filter(user=request.user).select_related('category')[:5],
        'recent_invoices': Invoice.objects.filter(user=request.user).select_related('client').prefetch_related('items')[:5],
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False)[:5],
    }
    return render(request, 'dashboard.html', context)
