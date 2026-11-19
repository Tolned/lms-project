from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import User


@shared_task
def deactivate_inactive_users():
    """
    Периодическая задача: блокирует пользователей,
    которые не заходили в систему более 30 дней.
    Обновление происходит батчем (одним SQL-запросом).
    """
    threshold = timezone.now() - timedelta(days=30)

    deactivated_count = User.objects.filter(
        last_login__lt=threshold,
        is_active=True
    ).update(is_active=False)

    return f"Deactivated {deactivated_count} inactive users."