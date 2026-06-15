from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AuditLog


@login_required
def audit_log_list(request):
    audit_logs = AuditLog.objects.filter(user=request.user)
    return render(request, 'audit/audit_log_list.html', {'audit_logs': audit_logs})
