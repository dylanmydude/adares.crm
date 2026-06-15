from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import BackupRecord
from .services import create_database_backup


@login_required
def backup_page(request):
    backups = BackupRecord.objects.filter(user=request.user)
    return render(request, 'backup/backup.html', {'backups': backups})


@login_required
@require_POST
def backup_create(request):
    create_database_backup(request.user)
    return redirect('backup_page')


@login_required
def backup_download(request, pk):
    backup = get_object_or_404(BackupRecord, pk=pk, user=request.user)
    return FileResponse(backup.file.open('rb'), as_attachment=True, filename=backup.file_name)
