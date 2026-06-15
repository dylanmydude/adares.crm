from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connections
from django.utils import timezone

from .models import BackupRecord


def create_database_backup(user):
    database_path = _database_path()
    backup_bytes = database_path.read_bytes()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    filename = f'database-backup-{user.pk}-{timestamp}.sqlite3'

    record = BackupRecord.objects.create(
        user=user,
        file_name=filename,
        file_size=len(backup_bytes),
    )
    record.file.save(filename, ContentFile(backup_bytes), save=True)
    return record


def _database_path():
    db_name = connections['default'].settings_dict['NAME']
    return Path(db_name)
