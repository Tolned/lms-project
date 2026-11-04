from django.db import models
from django.conf import settings


class Course(models.Model):
    """Модель курса."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название курса',
        help_text='Введите название курса'
    )
    preview = models.ImageField(
        upload_to='lms/courses/',
        blank=True,
        null=True,
        verbose_name='Превью',
        help_text='Загрузите превью курса'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание',
        help_text='Введите описание курса'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    """Модель урока."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс',
        help_text='Укажите курс'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название урока',
        help_text='Введите название урока'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание',
        help_text='Введите описание урока'
    )
    preview = models.ImageField(
        upload_to='lms/lessons/',
        blank=True,
        null=True,
        verbose_name='Превью',
        help_text='Загрузите превью урока'
    )
    video_link = models.URLField(
        blank=True,
        null=True,
        verbose_name='Ссылка на видео',
        help_text='Укажите ссылку на видео'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ('course', 'name')

    def __str__(self):
        return f'{self.course.name} — {self.name}'