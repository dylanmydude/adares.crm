from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Client, Job


class CRMTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='crm_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_crm_user',
            password='StrongPass123!',
        )

    def test_client_crud(self):
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('client_create'),
            {
                'name': 'Acme Client',
                'email': 'acme@example.com',
                'phone': '0820000000',
                'company_name': 'Acme Co',
                'notes': 'Important client',
            },
        )

        self.assertRedirects(create_response, reverse('client_list'))
        client = Client.objects.get(user=self.user)
        self.assertEqual(client.name, 'Acme Client')

        list_response = self.client.get(reverse('client_list'))
        self.assertContains(list_response, 'Acme Client')
        self.assertContains(list_response, 'Acme Co')

        edit_response = self.client.post(
            reverse('client_edit', args=[client.pk]),
            {
                'name': 'Updated Client',
                'email': 'updated@example.com',
                'phone': '0830000000',
                'company_name': 'Updated Co',
                'notes': 'Updated notes',
            },
        )

        self.assertRedirects(edit_response, reverse('client_list'))
        client.refresh_from_db()
        self.assertEqual(client.name, 'Updated Client')
        self.assertEqual(client.company_name, 'Updated Co')

        delete_response = self.client.post(reverse('client_delete', args=[client.pk]))

        self.assertRedirects(delete_response, reverse('client_list'))
        self.assertFalse(Client.objects.filter(pk=client.pk).exists())

    def test_job_crud(self):
        client = Client.objects.create(user=self.user, name='Job Client')
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('job_create'),
            {
                'client': client.pk,
                'title': 'Website Fix',
                'status': Job.STATUS_QUOTED,
                'value': '1500.00',
                'notes': 'Initial quoted work',
            },
        )

        self.assertRedirects(create_response, reverse('job_list'))
        job = Job.objects.get(user=self.user)
        self.assertEqual(job.client, client)
        self.assertEqual(job.value, Decimal('1500.00'))

        list_response = self.client.get(reverse('job_list'))
        self.assertContains(list_response, 'Website Fix')
        self.assertContains(list_response, 'Job Client')
        self.assertContains(list_response, 'Quoted')

        edit_response = self.client.post(
            reverse('job_edit', args=[job.pk]),
            {
                'client': client.pk,
                'title': 'Website Fix Updated',
                'status': Job.STATUS_IN_PROGRESS,
                'value': '1750.00',
                'notes': 'Work started',
            },
        )

        self.assertRedirects(edit_response, reverse('job_list'))
        job.refresh_from_db()
        self.assertEqual(job.title, 'Website Fix Updated')
        self.assertEqual(job.status, Job.STATUS_IN_PROGRESS)
        self.assertEqual(job.value, Decimal('1750.00'))

        delete_response = self.client.post(reverse('job_delete', args=[job.pk]))

        self.assertRedirects(delete_response, reverse('job_list'))
        self.assertFalse(Job.objects.filter(pk=job.pk).exists())

    def test_user_data_isolation_for_clients_and_jobs(self):
        client = Client.objects.create(user=self.user, name='My Client')
        other_client = Client.objects.create(user=self.other_user, name='Other Client')
        job = Job.objects.create(
            user=self.user,
            client=client,
            title='My Job',
            status=Job.STATUS_COMPLETED,
            value='500.00',
        )
        other_job = Job.objects.create(
            user=self.other_user,
            client=other_client,
            title='Other Job',
            status=Job.STATUS_CANCELLED,
            value='999.00',
        )

        self.client.force_login(self.user)

        client_response = self.client.get(reverse('client_list'))
        self.assertContains(client_response, 'My Client')
        self.assertNotContains(client_response, 'Other Client')

        job_response = self.client.get(reverse('job_list'))
        self.assertContains(job_response, 'My Job')
        self.assertNotContains(job_response, 'Other Job')

        self.assertEqual(self.client.get(reverse('client_edit', args=[other_client.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('client_delete', args=[other_client.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('job_edit', args=[other_job.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('job_delete', args=[other_job.pk])).status_code, 404)
        self.assertTrue(Client.objects.filter(pk=client.pk).exists())
        self.assertTrue(Job.objects.filter(pk=job.pk).exists())

    def test_job_form_rejects_other_users_client(self):
        other_client = Client.objects.create(user=self.other_user, name='Other Client')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('job_create'),
            {
                'client': other_client.pk,
                'title': 'Invalid Job',
                'status': Job.STATUS_QUOTED,
                'value': '100.00',
                'notes': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Job.objects.filter(title='Invalid Job').exists())

    def test_crm_pages_require_login(self):
        protected_urls = [
            reverse('client_list'),
            reverse('client_create'),
            reverse('job_list'),
            reverse('job_create'),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")
