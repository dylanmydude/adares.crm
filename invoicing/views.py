from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvoiceForm, InvoiceItemFormSet
from .models import Invoice


@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(user=request.user).select_related('client').prefetch_related('items')
    return render(request, 'invoicing/invoice_list.html', {'invoices': invoices})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('client').prefetch_related('items'),
        pk=pk,
        user=request.user,
    )
    return render(request, 'invoicing/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.save()
            formset.instance = invoice
            formset.save()
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(user=request.user)
        formset = InvoiceItemFormSet()

    return render(
        request,
        'invoicing/invoice_form.html',
        {'form': form, 'formset': formset, 'title': 'Create Invoice'},
    )


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(instance=invoice)

    return render(
        request,
        'invoicing/invoice_form.html',
        {'form': form, 'formset': formset, 'title': 'Edit Invoice'},
    )


@login_required
@require_POST
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice.delete()
    return redirect('invoice_list')
