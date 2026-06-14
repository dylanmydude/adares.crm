from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ExpenseForm, IncomeForm
from .models import Expense, ExpenseCategory, Income, IncomeSource


@login_required
def income_list(request):
    incomes = Income.objects.filter(user=request.user).select_related('source')
    return render(request, 'finance/income_list.html', {'incomes': incomes})


@login_required
def income_create(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.source = _get_income_source(request.user, form.cleaned_data['source_name'])
            income.save()
            return redirect('income_list')
    else:
        form = IncomeForm()

    return render(request, 'finance/income_form.html', {'form': form, 'title': 'Add Income'})


@login_required
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            income = form.save(commit=False)
            income.source = _get_income_source(request.user, form.cleaned_data['source_name'])
            income.save()
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income)

    return render(request, 'finance/income_form.html', {'form': form, 'title': 'Edit Income'})


@login_required
@require_POST
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    income.delete()
    return redirect('income_list')


@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).select_related('category')
    return render(request, 'finance/expense_list.html', {'expenses': expenses})


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.category = _get_expense_category(request.user, form.cleaned_data['category_name'])
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'finance/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.category = _get_expense_category(request.user, form.cleaned_data['category_name'])
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'finance/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    return redirect('expense_list')


def _get_income_source(user, name):
    cleaned_name = name.strip()
    source, _created = IncomeSource.objects.get_or_create(user=user, name=cleaned_name)
    return source


def _get_expense_category(user, name):
    cleaned_name = name.strip()
    category, _created = ExpenseCategory.objects.get_or_create(user=user, name=cleaned_name)
    return category
