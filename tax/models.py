from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class TaxCalculation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tax_year = models.PositiveIntegerField(default=2027)
    gross_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    deductible_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    taxable_income = models.DecimalField(max_digits=12, decimal_places=2)
    tax_before_rebates = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    rebate_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    estimated_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    bracket_description = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.estimated_tax}"

    @property
    def total_income(self):
        return self.gross_income

    @total_income.setter
    def total_income(self, value):
        self.gross_income = value

    @property
    def total_expenses(self):
        return self.deductible_expenses

    @total_expenses.setter
    def total_expenses(self, value):
        self.deductible_expenses = value

    @property
    def taxable_profit(self):
        return self.taxable_income

    @taxable_profit.setter
    def taxable_profit(self, value):
        self.taxable_income = value
