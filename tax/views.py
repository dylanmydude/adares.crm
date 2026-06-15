from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import TaxCalculation
from .services import save_tax_calculation


@login_required
def tax_summary(request):
    calculation = save_tax_calculation(request.user)
    history = TaxCalculation.objects.filter(user=request.user)

    return render(
        request,
        'tax/summary.html',
        {
            'calculation': calculation,
            'history': history,
        },
    )
