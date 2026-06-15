from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_OVERDUE_INVOICE = 'overdue_invoice'
    TYPE_TAX_ESTIMATE = 'tax_estimate'
    TYPE_REPORT_GENERATED = 'report_generated'
    TYPE_BACKUP_CREATED = 'backup_created'

    TYPE_CHOICES = [
        (TYPE_OVERDUE_INVOICE, 'Overdue invoice'),
        (TYPE_TAX_ESTIMATE, 'Tax estimate created'),
        (TYPE_REPORT_GENERATED, 'Report generated'),
        (TYPE_BACKUP_CREATED, 'Backup created'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
