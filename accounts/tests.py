from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


class AccountsTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_authenticates_existing_user(self):
        get_user_model().objects.create_user(
            username='loginuser',
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
