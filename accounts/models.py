from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    business_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    tax_reference_number = models.CharField(max_length=80, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    default_invoice_note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username


class UserSettings(models.Model):
    REPORT_MONTHLY = 'monthly'
    REPORT_QUARTERLY = 'quarterly'
    REPORT_YEARLY = 'yearly'

    REPORT_PERIOD_CHOICES = [
        (REPORT_MONTHLY, 'Monthly'),
        (REPORT_QUARTERLY, 'Quarterly'),
        (REPORT_YEARLY, 'Yearly'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    default_currency = models.CharField(max_length=10, default='ZAR')
    default_tax_estimate_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    notification_preference = models.BooleanField(default=True)
    default_report_period = models.CharField(
        max_length=20,
        choices=REPORT_PERIOD_CHOICES,
        default=REPORT_MONTHLY,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} settings"
