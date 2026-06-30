from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import UserProfile, UserSettings
from accounts.tokens import email_verification_token
from audit.models import AuditLog
from crm.models import Client


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountsTests(TestCase):
    def test_register_creates_unverified_user_and_sends_email(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('login'))
        user = get_user_model().objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertFalse(user.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your ADARES CRM email address', mail.outbox[0].subject)

    def test_valid_token_verifies_account(self):
        user = get_user_model().objects.create_user(
            username='verifyuser',
            email='verify@example.com',
            password='StrongPass123!',
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)

        response = self.client.get(reverse('verify_email', args=[uid, token]))

        self.assertRedirects(response, reverse('login'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_invalid_token_fails_safely(self):
        user = get_user_model().objects.create_user(
            username='invalidverify',
            email='invalidverify@example.com',
            password='StrongPass123!',
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.get(reverse('verify_email', args=[uid, 'invalid-token']))

        self.assertRedirects(response, reverse('login'))
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    @override_settings(PASSWORD_RESET_TIMEOUT=-1)
    def test_expired_token_fails_safely(self):
        user = get_user_model().objects.create_user(
            username='expiredverify',
            email='expiredverify@example.com',
            password='StrongPass123!',
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)

        response = self.client.get(reverse('verify_email', args=[uid, token]))

        self.assertRedirects(response, reverse('login'))
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_unverified_user_cannot_log_in(self):
        get_user_model().objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='StrongPass123!',
            is_active=False,
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'unverified',
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please verify your email address before logging in.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_authenticates_existing_user(self):
        get_user_model().objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'loginuser',
                'password': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_resend_verification_sends_email(self):
        get_user_model().objects.create_user(
            username='resend',
            email='resend@example.com',
            password='StrongPass123!',
            is_active=False,
        )

        response = self.client.post(reverse('resend_verification'), {'email': 'resend@example.com'})

        self.assertRedirects(response, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)

    def test_logout_ends_session(self):
        user = get_user_model().objects.create_user(
            username='logoutuser',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_profile_requires_login_and_loads_for_authenticated_user(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

        user = get_user_model().objects.create_user(
            username='profileuser',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'profileuser')

    def test_profile_update(self):
        user = get_user_model().objects.create_user(
            username='profileupdate',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('profile'),
            {
                'full_name': 'Dylan Tester',
                'business_name': 'ADARES Test Studio',
                'phone_number': '0821234567',
                'tax_reference_number': 'TAX123',
                'date_of_birth': '1985-04-03',
                'default_invoice_note': 'Thank you for your business.',
            },
        )

        self.assertRedirects(response, reverse('profile'))
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, 'Dylan Tester')
        self.assertEqual(profile.business_name, 'ADARES Test Studio')
        self.assertEqual(profile.phone_number, '0821234567')
        self.assertEqual(profile.tax_reference_number, 'TAX123')
        self.assertEqual(profile.date_of_birth.isoformat(), '1985-04-03')
        self.assertEqual(profile.default_invoice_note, 'Thank you for your business.')

    def test_settings_update(self):
        user = get_user_model().objects.create_user(
            username='settingsuser',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('account_settings'),
            {
                'default_currency': 'USD',
                'notification_preference': 'on',
                'default_report_period': UserSettings.REPORT_QUARTERLY,
            },
        )

        self.assertRedirects(response, reverse('account_settings'))
        settings = UserSettings.objects.get(user=user)
        self.assertEqual(settings.default_currency, 'USD')
        self.assertTrue(settings.notification_preference)
        self.assertEqual(settings.default_report_period, UserSettings.REPORT_QUARTERLY)

    def test_settings_requires_login(self):
        response = self.client.get(reverse('account_settings'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('account_settings')}")

    def test_profile_and_settings_are_user_isolated(self):
        user = get_user_model().objects.create_user(username='isolated', password='StrongPass123!')
        other_user = get_user_model().objects.create_user(username='otherisolated', password='StrongPass123!')
        other_profile = UserProfile.objects.create(user=other_user, full_name='Other User')
        other_settings = UserSettings.objects.create(user=other_user, default_currency='EUR')
        self.client.force_login(user)

        self.client.post(
            reverse('profile'),
            {
                'full_name': 'Current User',
                'business_name': '',
                'phone_number': '',
                'tax_reference_number': '',
                'date_of_birth': '',
                'default_invoice_note': '',
            },
        )
        self.client.post(
            reverse('account_settings'),
            {
                'default_currency': 'ZAR',
                'notification_preference': 'on',
                'default_report_period': UserSettings.REPORT_MONTHLY,
            },
        )

        other_profile.refresh_from_db()
        other_settings.refresh_from_db()
        self.assertEqual(other_profile.full_name, 'Other User')
        self.assertEqual(other_settings.default_currency, 'EUR')

    def test_date_picker_inputs_render_for_date_fields(self):
        user = get_user_model().objects.create_user(
            username='datepicker',
            password='StrongPass123!',
        )
        Client.objects.create(user=user, name='Date Client')
        self.client.force_login(user)

        checks = [
            (reverse('income_create'), 'name="date_received"'),
            (reverse('expense_create'), 'name="date_paid"'),
            (reverse('job_create'), 'name="start_date"'),
            (reverse('job_create'), 'name="due_date"'),
            (reverse('invoice_create'), 'name="issue_date"'),
            (reverse('invoice_create'), 'name="due_date"'),
            (reverse('profile'), 'name="date_of_birth"'),
        ]

        for url, field_name in checks:
            with self.subTest(url=url, field_name=field_name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'type="date"')
                self.assertContains(response, field_name)


class UserManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username='staffadmin',
            email='staff@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.normal_user = user_model.objects.create_user(
            username='normal',
            email='normal@example.com',
            password='StrongPass123!',
        )

    def test_normal_users_cannot_access_user_management(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(reverse('management_user_list'))

        self.assertEqual(response.status_code, 403)

    def test_staff_users_can_list_and_search_users(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('management_user_list'), {'q': 'normal'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'normal')
        self.assertNotContains(response, 'missing-user')

    def test_administrator_can_add_edit_activate_deactivate_and_delete_user(self):
        self.client.force_login(self.staff)

        add_response = self.client.post(
            reverse('management_user_add'),
            {
                'username': 'managed',
                'email': 'managed@example.com',
                'first_name': 'Managed',
                'last_name': 'User',
                'is_active': 'on',
                'is_staff': '',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )
        managed = get_user_model().objects.get(username='managed')
        self.assertRedirects(add_response, reverse('management_user_detail', args=[managed.pk]))
        self.assertTrue(AuditLog.objects.filter(user=self.staff, action='user created').exists())

        edit_response = self.client.post(
            reverse('management_user_edit', args=[managed.pk]),
            {
                'username': 'managed',
                'email': 'managed@example.com',
                'first_name': 'Updated',
                'last_name': 'User',
                'is_staff': 'on',
            },
        )
        self.assertRedirects(edit_response, reverse('management_user_detail', args=[managed.pk]))
        managed.refresh_from_db()
        self.assertFalse(managed.is_active)
        self.assertTrue(managed.is_staff)
        self.assertTrue(AuditLog.objects.filter(user=self.staff, action='user deactivated').exists())
        self.assertTrue(AuditLog.objects.filter(user=self.staff, action='staff status changed').exists())

        edit_response = self.client.post(
            reverse('management_user_edit', args=[managed.pk]),
            {
                'username': 'managed',
                'email': 'managed@example.com',
                'first_name': 'Updated',
                'last_name': 'User',
                'is_active': 'on',
                'is_staff': 'on',
            },
        )
        self.assertRedirects(edit_response, reverse('management_user_detail', args=[managed.pk]))
        managed.refresh_from_db()
        self.assertTrue(managed.is_active)
        self.assertTrue(AuditLog.objects.filter(user=self.staff, action='user activated').exists())

        delete_response = self.client.post(reverse('management_user_delete', args=[managed.pk]))
        self.assertRedirects(delete_response, reverse('management_user_list'))
        self.assertFalse(get_user_model().objects.filter(pk=managed.pk).exists())
        self.assertTrue(AuditLog.objects.filter(user=self.staff, action='user deleted').exists())

    def test_self_deletion_is_prevented(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('management_user_delete', args=[self.staff.pk]))

        self.assertRedirects(response, reverse('management_user_detail', args=[self.staff.pk]))
        self.assertTrue(get_user_model().objects.filter(pk=self.staff.pk).exists())

    def test_self_deactivation_is_prevented(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('management_user_edit', args=[self.staff.pk]),
            {
                'username': self.staff.username,
                'email': self.staff.email,
                'first_name': '',
                'last_name': '',
                'is_staff': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_staff_user_cannot_remove_superuser_status(self):
        superuser = get_user_model().objects.create_superuser(
            username='rootadmin',
            email='root@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('management_user_edit', args=[superuser.pk]),
            {
                'username': superuser.username,
                'email': superuser.email,
                'first_name': '',
                'last_name': '',
                'is_active': 'on',
                'is_staff': 'on',
                'is_superuser': '',
            },
        )

        self.assertRedirects(response, reverse('management_user_detail', args=[superuser.pk]))
        superuser.refresh_from_db()
        self.assertTrue(superuser.is_superuser)
