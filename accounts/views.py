from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes

from audit.services import record_action
from .forms import (
    RegistrationForm,
    ResendVerificationForm,
    UserManagementCreateForm,
    UserManagementEditForm,
    UserProfileForm,
    UserSettingsForm,
    VerifiedAuthenticationForm,
)
from .models import UserProfile, UserSettings
from .tokens import email_verification_token


def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def admin_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if not _is_admin(request.user):
            return HttpResponseForbidden('Administrator access is required.')
        return view_func(request, *args, **kwargs)

    return wrapped


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verification_url = request.build_absolute_uri(
        reverse('verify_email', args=[uid, token])
    )
    send_mail(
        'Verify your ADARES CRM email address',
        (
            'Verify your ADARES CRM account by opening this link:\n\n'
            f'{verification_url}\n\n'
            'If you did not create this account, you can ignore this email.'
        ),
        django_settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def _token_is_expired(user, token):
    try:
        ts_b36 = token.split('-')[0]
        timestamp = PasswordResetTokenGenerator()._num_seconds(
            PasswordResetTokenGenerator()._now()
        )
        token_timestamp = int(ts_b36, 36)
    except (IndexError, TypeError, ValueError):
        return False
    return (timestamp - token_timestamp) > django_settings.PASSWORD_RESET_TIMEOUT


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            messages.success(request, 'Verification email sent. Please verify your email address before logging in.')
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = VerifiedAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            record_action(user, 'login', 'User logged in.')
            return redirect('dashboard')
    else:
        form = VerifiedAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def verify_email(request, uidb64, token):
    user_model = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = user_model.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
        user = None

    if user is None:
        messages.error(request, 'Invalid verification link.')
        return redirect('login')

    if email_verification_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        messages.success(request, 'Email verification completed. You can now log in.')
        return redirect('login')

    if _token_is_expired(user, token):
        messages.error(request, 'Expired verification link. Please request a new verification email.')
    else:
        messages.error(request, 'Invalid verification link.')
    return redirect('login')


def resend_verification(request):
    if request.method == 'POST':
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            user = get_user_model().objects.filter(email__iexact=form.cleaned_data['email']).first()
            if user and not user.is_active:
                _send_verification_email(request, user)
            messages.success(request, 'Verification email sent if the account exists and is not already verified.')
            return redirect('login')
    else:
        form = ResendVerificationForm()

    return render(request, 'accounts/resend_verification.html', {'form': form})


def logout_view(request):
    record_action(request.user, 'logout', 'User logged out.')
    logout(request)
    return redirect('login')


@login_required
def profile(request):
    profile_record, _created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile_record)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile_record)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def settings(request):
    settings_record, _created = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=settings_record)
        if form.is_valid():
            form.save()
            return redirect('account_settings')
    else:
        form = UserSettingsForm(instance=settings_record)

    return render(request, 'accounts/settings.html', {'form': form})


@admin_required
def management_user_list(request):
    query = request.GET.get('q', '').strip()
    users = get_user_model().objects.all().order_by('username')
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    return render(request, 'accounts/management/user_list.html', {'users': users, 'query': query})


@admin_required
def management_user_add(request):
    if request.method == 'POST':
        form = UserManagementCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            record_action(request.user, 'user created', f'Created user {user.pk}.')
            if user.is_active:
                record_action(request.user, 'user activated', f'Activated user {user.pk}.')
            if user.is_staff:
                record_action(request.user, 'staff status changed', f'Granted staff status to user {user.pk}.')
            return redirect('management_user_detail', pk=user.pk)
    else:
        form = UserManagementCreateForm()
    return render(request, 'accounts/management/user_form.html', {'form': form, 'title': 'Add User'})


@admin_required
def management_user_detail(request, pk):
    managed_user = get_object_or_404(get_user_model(), pk=pk)
    return render(request, 'accounts/management/user_detail.html', {'managed_user': managed_user})


@admin_required
def management_user_edit(request, pk):
    managed_user = get_object_or_404(get_user_model(), pk=pk)
    old_is_active = managed_user.is_active
    old_is_staff = managed_user.is_staff
    if request.method == 'POST':
        form = UserManagementEditForm(request.POST, instance=managed_user, actor=request.user)
        if form.is_valid():
            if managed_user.pk == request.user.pk and not form.cleaned_data['is_active']:
                form.add_error('is_active', 'You cannot deactivate your own account.')
            else:
                user = form.save()
                record_action(request.user, 'user updated', f'Updated user {user.pk}.')
                if old_is_active != user.is_active:
                    action = 'user activated' if user.is_active else 'user deactivated'
                    record_action(request.user, action, f'{action.title()} {user.pk}.')
                if old_is_staff != user.is_staff:
                    status = 'Granted' if user.is_staff else 'Removed'
                    record_action(request.user, 'staff status changed', f'{status} staff status for user {user.pk}.')
                return redirect('management_user_detail', pk=user.pk)
    else:
        form = UserManagementEditForm(instance=managed_user, actor=request.user)
    return render(request, 'accounts/management/user_form.html', {'form': form, 'title': 'Edit User'})


@admin_required
def management_user_delete(request, pk):
    managed_user = get_object_or_404(get_user_model(), pk=pk)
    if managed_user.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('management_user_detail', pk=managed_user.pk)
    if request.method == 'POST':
        deleted_pk = managed_user.pk
        managed_user.delete()
        record_action(request.user, 'user deleted', f'Deleted user {deleted_pk}.')
        return redirect('management_user_list')
    return render(request, 'accounts/management/user_confirm_delete.html', {'managed_user': managed_user})
