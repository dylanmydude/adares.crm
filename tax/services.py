from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum

from accounts.models import UserProfile
from finance.models import Expense, Income

from .models import TaxCalculation


CENT = Decimal('0.01')
CURRENT_TAX_YEAR = 2027

TAX_YEAR_CONFIGS = {
    2027: {
        'label': '2027',
        'start_date': date(2026, 3, 1),
        'end_date': date(2027, 2, 28),
        'brackets': [
            {'lower': Decimal('0.00'), 'upper': Decimal('245100.00'), 'base': Decimal('0.00'), 'rate': Decimal('0.18')},
            {'lower': Decimal('245100.00'), 'upper': Decimal('383100.00'), 'base': Decimal('44118.00'), 'rate': Decimal('0.26')},
            {'lower': Decimal('383100.00'), 'upper': Decimal('530200.00'), 'base': Decimal('79998.00'), 'rate': Decimal('0.31')},
            {'lower': Decimal('530200.00'), 'upper': Decimal('695800.00'), 'base': Decimal('125599.00'), 'rate': Decimal('0.36')},
            {'lower': Decimal('695800.00'), 'upper': Decimal('887000.00'), 'base': Decimal('185215.00'), 'rate': Decimal('0.39')},
            {'lower': Decimal('887000.00'), 'upper': Decimal('1878600.00'), 'base': Decimal('259783.00'), 'rate': Decimal('0.41')},
            {'lower': Decimal('1878600.00'), 'upper': None, 'base': Decimal('666339.00'), 'rate': Decimal('0.45')},
        ],
        'rebates': {
            'primary': Decimal('17820.00'),
            'secondary': Decimal('9765.00'),
            'tertiary': Decimal('3249.00'),
        },
        'thresholds': {
            'under_65': Decimal('99000.00'),
            'age_65_to_74': Decimal('153250.00'),
            'age_75_plus': Decimal('171300.00'),
        },
    }
}


def calculate_tax_values(user, tax_year=CURRENT_TAX_YEAR):
    config = TAX_YEAR_CONFIGS[tax_year]
    gross_income = _sum_amount(Income.objects.filter(user=user))
    deductible_expenses = _sum_amount(Expense.objects.filter(user=user))
    taxable_income = gross_income - deductible_expenses
    positive_taxable_income = max(taxable_income, Decimal('0.00'))
    age = _age_at_tax_year_end(user, config)
    age_band = _age_band(age)
    threshold = config['thresholds'][age_band]
    tax_before_rebates, bracket_description = calculate_tax_before_rebates(positive_taxable_income, tax_year)
    rebate_amount = _rebate_amount(age, config)

    if positive_taxable_income <= threshold:
        estimated_tax = Decimal('0.00')
    else:
        estimated_tax = max(tax_before_rebates - rebate_amount, Decimal('0.00'))

    missing_date_of_birth = age is None
    values = {
        'tax_year': tax_year,
        'gross_income': _money(gross_income),
        'deductible_expenses': _money(deductible_expenses),
        'taxable_income': _money(taxable_income),
        'tax_before_rebates': _money(tax_before_rebates),
        'rebate_amount': _money(rebate_amount),
        'estimated_tax': _money(estimated_tax),
        'bracket_description': bracket_description,
        'age': age,
        'age_band': age_band,
        'threshold': threshold,
        'missing_date_of_birth': missing_date_of_birth,
        # Backward-compatible context aliases.
        'total_income': _money(gross_income),
        'total_expenses': _money(deductible_expenses),
        'taxable_profit': _money(taxable_income),
    }
    return values


def calculate_tax_before_rebates(taxable_income, tax_year=CURRENT_TAX_YEAR):
    taxable_income = max(Decimal(str(taxable_income)), Decimal('0.00'))
    config = TAX_YEAR_CONFIGS[tax_year]
    for bracket in config['brackets']:
        if bracket['upper'] is None or taxable_income <= bracket['upper']:
            amount_above = max(taxable_income - bracket['lower'], Decimal('0.00'))
            tax = bracket['base'] + (amount_above * bracket['rate'])
            rate_percent = int(bracket['rate'] * 100)
            if bracket['base'] == Decimal('0.00'):
                description = f'{rate_percent}% of taxable income'
            else:
                description = f'R{bracket["base"]:.2f} plus {rate_percent}% above R{bracket["lower"]:.2f}'
            return _money(tax), description
    return Decimal('0.00'), 'No tax bracket'


def save_tax_calculation(user, tax_year=CURRENT_TAX_YEAR):
    values = calculate_tax_values(user, tax_year)
    calculation = TaxCalculation.objects.create(
        user=user,
        tax_year=values['tax_year'],
        gross_income=values['gross_income'],
        deductible_expenses=values['deductible_expenses'],
        taxable_income=values['taxable_income'],
        tax_before_rebates=values['tax_before_rebates'],
        rebate_amount=values['rebate_amount'],
        estimated_tax=values['estimated_tax'],
        bracket_description=values['bracket_description'],
    )
    return calculation


def _sum_amount(queryset):
    return queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')


def _age_at_tax_year_end(user, config):
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return None
    if not profile.date_of_birth:
        return None
    end_date = config['end_date']
    born = profile.date_of_birth
    return end_date.year - born.year - ((end_date.month, end_date.day) < (born.month, born.day))


def _age_band(age):
    if age is None or age < 65:
        return 'under_65'
    if age < 75:
        return 'age_65_to_74'
    return 'age_75_plus'


def _rebate_amount(age, config):
    rebates = config['rebates']
    amount = rebates['primary']
    if age is not None and age >= 65:
        amount += rebates['secondary']
    if age is not None and age >= 75:
        amount += rebates['tertiary']
    return amount


def _money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
