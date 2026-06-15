from .models import AuditLog


def record_action(user, action, description=''):
    if not getattr(user, 'is_authenticated', False):
        return None

    return AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
    )
