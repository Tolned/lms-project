from django.conf import settings
from django.db import models

from .validators import validate_youtube_url


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название курса')
    description = models.TextField(blank=True, validators=[validate_youtube_url], verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена курса') # <-- Добавлено
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses', verbose_name='Владелец')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['id']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс',
    )
    title = models.CharField(max_length=200, verbose_name='Название урока')
    description = models.TextField(
        blank=True,
        validators=[validate_youtube_url],
        verbose_name='Описание',
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        validators=[validate_youtube_url],
        verbose_name='Ссылка на видео (только youtube.com)',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Владелец',
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['id']

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Курс',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подписки')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        # Один пользователь не может подписаться на один курс дважды
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'],
                name='unique_user_course_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.course}'