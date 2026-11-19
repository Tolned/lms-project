from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Course


@shared_task
def send_course_update_notification(course_id):
    """Отправляет уведомление подписчикам об обновлении курса."""
    try:
        course = Course.objects.select_related('owner').prefetch_related('subscriptions__user').get(id=course_id)
        subscribers = course.subscriptions.all()

        recipient_list = [sub.user.email for sub in subscribers if sub.user.email]

        if recipient_list:
            send_mail(
                subject=f'Обновление курса: {course.title}',
                message=f'Здравствуйте! В курсе "{course.title}" появились новые материалы.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
    except Course.DoesNotExist:
        pass