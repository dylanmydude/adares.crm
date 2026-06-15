from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from audit.services import record_action

from .models import GeneratedReport
from .services import generate_report


@login_required
def report_list(request):
    reports = GeneratedReport.objects.filter(user=request.user)
    return render(request, 'reports/report_list.html', {'reports': reports})


@login_required
@require_POST
def report_generate(request, report_type):
    valid_types = {choice[0] for choice in GeneratedReport.REPORT_CHOICES}
    if report_type in valid_types:
        report = generate_report(request.user, report_type)
        record_action(request.user, 'generate report', f'Generated report {report.pk}.')
    return redirect('report_list')


@login_required
def report_download(request, pk):
    report = get_object_or_404(GeneratedReport, pk=pk, user=request.user)
    return FileResponse(report.file.open('rb'), as_attachment=True, filename=report.file.name.split('/')[-1])
