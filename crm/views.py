from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ClientForm, JobForm
from .models import Client, Job


@login_required
def client_list(request):
    clients = Client.objects.filter(user=request.user)
    return render(request, 'crm/client_list.html', {'clients': clients})


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            return redirect('client_list')
    else:
        form = ClientForm()

    return render(request, 'crm/client_form.html', {'form': form, 'title': 'Add Client'})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)

    return render(request, 'crm/client_form.html', {'form': form, 'title': 'Edit Client'})


@login_required
@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    client.delete()
    return redirect('client_list')


@login_required
def job_list(request):
    jobs = Job.objects.filter(user=request.user).select_related('client')
    return render(request, 'crm/job_list.html', {'jobs': jobs})


@login_required
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            return redirect('job_list')
    else:
        form = JobForm(user=request.user)

    return render(request, 'crm/job_form.html', {'form': form, 'title': 'Add Job'})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('job_list')
    else:
        form = JobForm(instance=job, user=request.user)

    return render(request, 'crm/job_form.html', {'form': form, 'title': 'Edit Job'})


@login_required
@require_POST
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    job.delete()
    return redirect('job_list')
