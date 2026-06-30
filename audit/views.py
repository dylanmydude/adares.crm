from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.dateparse import parse_date

from .models import AuditLog


@login_required
def audit_log_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden('Administrator access is required.')

    audit_logs = AuditLog.objects.select_related('user').all()
    user_id = request.GET.get('user', '').strip()
    action = request.GET.get('action', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    if user_id:
        audit_logs = audit_logs.filter(user_id=user_id)
    if action:
        audit_logs = audit_logs.filter(action__icontains=action)
    parsed_start = parse_date(start_date) if start_date else None
    parsed_end = parse_date(end_date) if end_date else None
    if parsed_start:
        audit_logs = audit_logs.filter(created_at__date__gte=parsed_start)
    if parsed_end:
        audit_logs = audit_logs.filter(created_at__date__lte=parsed_end)

    return render(
        request,
        'audit/audit_log_list.html',
        {
            'audit_logs': audit_logs,
            'users': AuditLog.objects.select_related('user').order_by('user__username').values('user_id', 'user__username').distinct(),
            'filters': {
                'user': user_id,
                'action': action,
                'start_date': start_date,
                'end_date': end_date,
            },
        },
    )
