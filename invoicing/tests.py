from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crm.models import Client

from .models import Invoice, InvoiceItem


class InvoicingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='invoice_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_invoice_user',
            password='StrongPass123!',
        )
        self.client_record = Client.objects.create(user=self.user, name='Client One')
        self.other_client = Client.objects.create(user=self.other_user, name='Other Client')

    def invoice_payload(self, client_id=None, invoice_number='INV-001', status=Invoice.STATUS_DRAFT):
        return {
            'client': client_id or self.client_record.pk,
            'invoice_number': invoice_number,
            'status': status,
            'issue_date': '2026-06-15',
            'due_date': '2026-06-30',
            'notes': 'Test invoice',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-description': 'Design work',
            'items-0-quantity': '2',
            'items-0-unit_price': '150.00',
        }

    def test_invoice_crud(self):
        self.client.force_login(self.user)

        create_response = self.client.post(reverse('invoice_create'), self.invoice_payload())

        invoice = Invoice.objects.get(user=self.user)
        self.assertRedirects(create_response, reverse('invoice_detail', args=[invoice.pk]))
        self.assertEqual(invoice.client, self.client_record)
        self.assertEqual(invoice.status, Invoice.STATUS_DRAFT)
        self.assertEqual(invoice.items.count(), 1)

        detail_response = self.client.get(reverse('invoice_detail', args=[invoice.pk]))
        self.assertContains(detail_response, 'INV-001')
        self.assertContains(detail_response, 'Design work')
        self.assertContains(detail_response, 'R300.00')

        list_response = self.client.get(reverse('invoice_list'))
        self.assertContains(list_response, 'INV-001')
        self.assertContains(list_response, 'Client One')

        edit_payload = self.invoice_payload(invoice_number='INV-002', status=Invoice.STATUS_SENT)
        edit_payload.update(
            {
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '1',
                'items-0-id': invoice.items.first().pk,
                'items-0-invoice': invoice.pk,
                'items-0-description': 'Updated work',
                'items-0-quantity': '3',
                'items-0-unit_price': '200.00',
            }
        )
        edit_response = self.client.post(reverse('invoice_edit', args=[invoice.pk]), edit_payload)

        self.assertRedirects(edit_response, reverse('invoice_detail', args=[invoice.pk]))
        invoice.refresh_from_db()
        self.assertEqual(invoice.invoice_number, 'INV-002')
        self.assertEqual(invoice.status, Invoice.STATUS_SENT)
        self.assertEqual(invoice.total, Decimal('600.00'))

        delete_response = self.client.post(reverse('invoice_delete', args=[invoice.pk]))

        self.assertRedirects(delete_response, reverse('invoice_list'))
        self.assertFalse(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_invoice_item_totals(self):
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.client_record,
            invoice_number='INV-TOTAL',
            status=Invoice.STATUS_DRAFT,
            issue_date='2026-06-15',
            due_date='2026-06-30',
        )
        item_one = InvoiceItem.objects.create(
            invoice=invoice,
            description='Consulting',
            quantity=2,
            unit_price='125.50',
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Support',
            quantity=1,
            unit_price='49.00',
        )

        self.assertEqual(item_one.line_total, Decimal('251.00'))
        self.assertEqual(invoice.total, Decimal('300.00'))

    def test_invoice_pages_require_login(self):
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.client_record,
            invoice_number='INV-PROTECTED',
            status=Invoice.STATUS_DRAFT,
            issue_date='2026-06-15',
            due_date='2026-06-30',
        )
        protected_urls = [
            reverse('invoice_list'),
            reverse('invoice_create'),
            reverse('invoice_detail', args=[invoice.pk]),
            reverse('invoice_edit', args=[invoice.pk]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_user_data_isolation(self):
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.client_record,
            invoice_number='INV-MINE',
            status=Invoice.STATUS_DRAFT,
            issue_date='2026-06-15',
            due_date='2026-06-30',
        )
        other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=self.other_client,
            invoice_number='INV-OTHER',
            status=Invoice.STATUS_PAID,
            issue_date='2026-06-15',
            due_date='2026-06-30',
        )

        self.client.force_login(self.user)

        list_response = self.client.get(reverse('invoice_list'))
        self.assertContains(list_response, 'INV-MINE')
        self.assertNotContains(list_response, 'INV-OTHER')

        self.assertEqual(self.client.get(reverse('invoice_detail', args=[other_invoice.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('invoice_edit', args=[other_invoice.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('invoice_delete', args=[other_invoice.pk])).status_code, 404)
        self.assertTrue(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_invoice_form_rejects_other_users_client(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('invoice_create'),
            self.invoice_payload(client_id=self.other_client.pk, invoice_number='INV-BAD'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Invoice.objects.filter(invoice_number='INV-BAD').exists())
