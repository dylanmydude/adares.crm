import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .models import BackupRecord


TEMP_MEDIA_ROOT = tempfile.mkdtemp()
TEMP_DB_DIR = tempfile.mkdtemp()
TEMP_DB_PATH = Path(TEMP_DB_DIR) / 'test-backup-source.sqlite3'
TEMP_DB_PATH.write_bytes(b'backup database content')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BackupTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        shutil.rmtree(TEMP_DB_DIR, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='backup_user',
            password='StrongPass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_backup_user',
            password='StrongPass123!',
        )

    def test_backup_page_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('backup_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Database Backups')
        self.assertContains(response, 'Create Backup')
        self.assertContains(response, 'media/backups/')

    def test_backup_creation_creates_record_and_file(self):
        self.client.force_login(self.user)

        with patch('backup.services._database_path', return_value=TEMP_DB_PATH):
            response = self.client.post(reverse('backup_create'))

        self.assertRedirects(response, reverse('backup_page'))
        backup = BackupRecord.objects.get(user=self.user)
        self.assertTrue(backup.file.name.startswith('backups/'))
        self.assertEqual(backup.file_size, len(b'backup database content'))
        with backup.file.open('rb') as backup_file:
            self.assertEqual(backup_file.read(), b'backup database content')

    def test_backup_download_returns_own_file(self):
        self.client.force_login(self.user)
        with patch('backup.services._database_path', return_value=TEMP_DB_PATH):
            self.client.post(reverse('backup_create'))
        backup = BackupRecord.objects.get(user=self.user)

        response = self.client.get(reverse('backup_download', args=[backup.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_backup_page_requires_login(self):
        response = self.client.get(reverse('backup_page'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('backup_page')}")

    def test_user_data_isolation_for_backup_history_and_download(self):
        self.client.force_login(self.user)
        with patch('backup.services._database_path', return_value=TEMP_DB_PATH):
            self.client.post(reverse('backup_create'))
        my_backup = BackupRecord.objects.get(user=self.user)

        self.client.force_login(self.other_user)
        with patch('backup.services._database_path', return_value=TEMP_DB_PATH):
            self.client.post(reverse('backup_create'))
        other_backup = BackupRecord.objects.get(user=self.other_user)

        list_response = self.client.get(reverse('backup_page'))
        self.assertContains(list_response, other_backup.file_name)
        self.assertNotContains(list_response, my_backup.file_name)
        self.assertEqual(self.client.get(reverse('backup_download', args=[my_backup.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('backup_download', args=[other_backup.pk])).status_code, 200)
