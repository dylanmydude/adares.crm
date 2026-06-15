from django.db import models
from django.conf import settings


class GeneratedReport(models.Model):
    REPORT_INCOME = 'income'
    REPORT_EXPENSE = 'expense'
    REPORT_TAX = 'tax'

    REPORT_CHOICES = [
        (REPORT_INCOME, 'Income report'),
        (REPORT_EXPENSE, 'Expense report'),
        (REPORT_TAX, 'Tax summary report'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_CHOICES)
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to='reports/')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return self.title
