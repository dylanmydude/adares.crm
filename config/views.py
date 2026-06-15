from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
    }
    return render(request, 'dashboard.html', context)
