from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from notifications.services import notify_tax_estimate_created

from .models import TaxCalculation
from .services import calculate_tax_values, save_tax_calculation


@login_required
def tax_summary(request):
    calculation = save_tax_calculation(request.user)
    notify_tax_estimate_created(calculation)
    history = TaxCalculation.objects.filter(user=request.user)
    tax_values = calculate_tax_values(request.user)

    return render(
        request,
        'tax/summary.html',
        {
            'calculation': calculation,
            'history': history,
            'tax_values': tax_values,
        },
    )
