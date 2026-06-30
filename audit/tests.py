from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from finance.models import Income

from .models import AuditLog
from .services import record_action


class AuditTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='audit_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_audit_user',
            password='StrongPass123!',
        )
        self.staff_user = user_model.objects.create_user(
            username='staff_audit_user',
            password='StrongPass123!',
            is_staff=True,
        )

    def test_record_action_creates_audit_log(self):
        log = record_action(self.user, 'create income', 'Created income record.')

        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'create income')
        self.assertEqual(log.description, 'Created income record.')

    def test_record_action_ignores_anonymous_user(self):
        log = record_action(AnonymousUser(), 'login', 'Anonymous attempt.')

        self.assertIsNone(log)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_normal_users_cannot_access_audit_logs(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('audit_log_list'))

        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_view_all_audit_logs(self):
        AuditLog.objects.create(user=self.user, action='create income', description='Mine')
        AuditLog.objects.create(user=self.other_user, action='create expense', description='Other')
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse('audit_log_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audit Logs')
        self.assertContains(response, 'create income')
        self.assertContains(response, 'Mine')
        self.assertContains(response, 'create expense')
        self.assertContains(response, 'Other')

    def test_audit_filters_work(self):
        AuditLog.objects.create(user=self.user, action='create income', description='Mine')
        AuditLog.objects.create(user=self.other_user, action='delete expense', description='Other')
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse('audit_log_list'), {'user': self.user.pk, 'action': 'create'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'create income')
        self.assertNotContains(response, 'delete expense')

    def test_audit_page_requires_login(self):
        response = self.client.get(reverse('audit_log_list'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('audit_log_list')}")

    def test_income_create_records_audit_log(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('income_create'),
            {
                'source_name': 'Delivery',
                'amount': '100.00',
                'date_received': '2026-06-15',
                'description': 'Shift',
            },
        )

        self.assertRedirects(response, reverse('income_list'))
        self.assertTrue(Income.objects.filter(user=self.user).exists())
        self.assertTrue(AuditLog.objects.filter(user=self.user, action='create income').exists())

    def test_login_and_logout_record_audit_logs(self):
        login_response = self.client.post(
            reverse('login'),
            {
                'username': 'audit_user',
                'password': 'StrongPass123!',
            },
        )
        self.assertRedirects(login_response, reverse('dashboard'))
        self.assertTrue(AuditLog.objects.filter(user=self.user, action='login').exists())

        logout_response = self.client.get(reverse('logout'))
        self.assertRedirects(logout_response, reverse('login'))
        self.assertTrue(AuditLog.objects.filter(user=self.user, action='logout').exists())
