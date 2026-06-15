import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from crm.models import Client
from finance.models import ExpenseCategory, IncomeSource
from invoicing.models import Invoice

from .models import Notification
from .services import create_notification, unread_notification_count


TEMP_MEDIA_ROOT = tempfile.mkdtemp()
TEMP_DB_DIR = tempfile.mkdtemp()
TEMP_DB_PATH = Path(TEMP_DB_DIR) / 'test-notification-backup.sqlite3'
TEMP_DB_PATH.write_bytes(b'notification backup database')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class NotificationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        shutil.rmtree(TEMP_DB_DIR, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='notify_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_notify_user',
            password='StrongPass123!',
        )
        self.client_record = Client.objects.create(user=self.user, name='Notify Client')
        self.source = IncomeSource.objects.create(user=self.user, name='Work')
        self.category = ExpenseCategory.objects.create(user=self.user, name='Fuel')

    def test_notification_creation_helper(self):
        notification = create_notification(
            self.user,
            Notification.TYPE_REPORT_GENERATED,
            'Report generated',
            'Income report is ready.',
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)
        self.assertEqual(unread_notification_count(self.user), 1)

    def test_notification_helper_ignores_anonymous_user(self):
        notification = create_notification(
            AnonymousUser(),
            Notification.TYPE_BACKUP_CREATED,
            'Backup created',
            'Ignored.',
        )

        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notification_page_shows_logged_in_user_history(self):
        Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_REPORT_GENERATED,
            title='Mine',
            message='My notification',
        )
        Notification.objects.create(
            user=self.other_user,
            notification_type=Notification.TYPE_BACKUP_CREATED,
            title='Other',
            message='Other notification',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('notification_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notification History')
        self.assertContains(response, 'Mine')
        self.assertContains(response, '1 unread')
        self.assertNotContains(response, 'Other notification')

    def test_mark_notification_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_TAX_ESTIMATE,
            title='Tax estimate created',
            message='Tax estimate ready.',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('notification_mark_read', args=[notification.pk]))

        self.assertRedirects(response, reverse('notification_list'))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertEqual(unread_notification_count(self.user), 0)

    def test_delete_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_BACKUP_CREATED,
            title='Backup created',
            message='Backup ready.',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('notification_delete', args=[notification.pk]))

        self.assertRedirects(response, reverse('notification_list'))
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_notification_page_requires_login(self):
        response = self.client.get(reverse('notification_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('notification_list')}")

    def test_user_data_isolation_for_notification_actions(self):
        my_notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_REPORT_GENERATED,
            title='Mine',
            message='Mine',
        )
        other_notification = Notification.objects.create(
            user=self.other_user,
            notification_type=Notification.TYPE_BACKUP_CREATED,
            title='Other',
            message='Other',
        )
        self.client.force_login(self.user)

        self.assertEqual(self.client.post(reverse('notification_mark_read', args=[other_notification.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('notification_delete', args=[other_notification.pk])).status_code, 404)
        self.assertTrue(Notification.objects.filter(pk=other_notification.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=my_notification.pk).exists())

    def test_unread_count_is_user_scoped_in_sidebar(self):
        Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_REPORT_GENERATED,
            title='Mine',
            message='Mine',
        )
        Notification.objects.create(
            user=self.other_user,
            notification_type=Notification.TYPE_BACKUP_CREATED,
            title='Other',
            message='Other',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Notifications')
        self.assertContains(response, 'nav-count')
        self.assertContains(response, '>1</span>')

    def test_overdue_invoice_creates_notification(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('invoice_create'),
            {
                'client': self.client_record.pk,
                'invoice_number': 'INV-NOTIFY',
                'status': Invoice.STATUS_OVERDUE,
                'issue_date': '2026-06-15',
                'due_date': '2026-06-30',
                'notes': '',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '0',
                'items-MIN_NUM_FORMS': '1',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-description': 'Work',
                'items-0-quantity': '1',
                'items-0-unit_price': '100.00',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                notification_type=Notification.TYPE_OVERDUE_INVOICE,
                title='Overdue invoice',
            ).exists()
        )

    def test_tax_report_and_backup_create_notifications(self):
        self.client.force_login(self.user)

        self.client.get(reverse('tax_summary'))
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type=Notification.TYPE_TAX_ESTIMATE).exists())

        self.client.post(reverse('report_generate', args=['tax']))
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type=Notification.TYPE_REPORT_GENERATED).exists())

        with patch('backup.services._database_path', return_value=TEMP_DB_PATH):
            self.client.post(reverse('backup_create'))
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type=Notification.TYPE_BACKUP_CREATED).exists())
