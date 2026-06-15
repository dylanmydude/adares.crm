from .models import Notification


def create_notification(user, notification_type, title, message):
    if not getattr(user, 'is_authenticated', False):
        return None

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
    )


def unread_notification_count(user):
    if not getattr(user, 'is_authenticated', False):
        return 0

    return Notification.objects.filter(user=user, is_read=False).count()


def notify_overdue_invoice(invoice):
    return create_notification(
        invoice.user,
        Notification.TYPE_OVERDUE_INVOICE,
        'Overdue invoice',
        f'Invoice {invoice.invoice_number} is overdue.',
    )


def notify_tax_estimate_created(calculation):
    return create_notification(
        calculation.user,
        Notification.TYPE_TAX_ESTIMATE,
        'Tax estimate created',
        f'Estimated tax is R{calculation.estimated_tax:.2f}.',
    )


def notify_report_generated(report):
    return create_notification(
        report.user,
        Notification.TYPE_REPORT_GENERATED,
        'Report generated',
        f'{report.title} is ready to download.',
    )


def notify_backup_created(backup):
    return create_notification(
        backup.user,
        Notification.TYPE_BACKUP_CREATED,
        'Backup created',
        f'Backup file {backup.file_name} is ready to download.',
    )
