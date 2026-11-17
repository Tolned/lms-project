from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from lms.validators import validate_youtube_url
from users.permissions import MODERATORS_GROUP

User = get_user_model()


class ValidatorTestCase(TestCase):
    """Юнит-тесты валидатора ссылок."""

    def test_youtube_links_allowed(self):
        for url in (
            'https://youtube.com/watch?v=123',
            'https://www.youtube.com/watch?v=123',
            'http://youtube.com',
        ):
            self.assertEqual(validate_youtube_url(url), url)

    def test_foreign_links_rejected(self):
        for url in (
            'https://rutube.ru/video/123/',
            'https://vimeo.com/123',
            'https://youtu.be/123',
            'https://evilyoutube.com/watch',
            'https://youtube.com.evil.ru/watch',
        ):
            with self.assertRaises(ValidationError):
                validate_youtube_url(url)

    def test_text_with_foreign_link_rejected(self):
        with self.assertRaises(ValidationError):
            validate_youtube_url('Смотри урок тут: https://my-site.ru/lesson')


class LessonTestCase(APITestCase):
    """CRUD уроков + права доступа для всех групп пользователей."""

    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.ru', password='TestPass123')
        self.other = User.objects.create_user(email='other@test.ru', password='TestPass123')
        self.moderator = User.objects.create_user(email='moder@test.ru', password='TestPass123')

        group, _ = Group.objects.get_or_create(name=MODERATORS_GROUP)
        self.moderator.groups.add(group)

        self.course = Course.objects.create(title='Курс', description='Описание', owner=self.owner)
        self.lesson = Lesson.objects.create(
            course=self.course, title='Урок', description='Текст', owner=self.owner
        )

        self.list_url = reverse('lms:lesson-list')
        self.create_url = reverse('lms:lesson-create')
        self.detail_url = reverse('lms:lesson-detail', args=[self.lesson.id])
        self.update_url = reverse('lms:lesson-update', args=[self.lesson.id])
        self.delete_url = reverse('lms:lesson-delete', args=[self.lesson.id])

    # --- доступ без авторизации ---
    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_401_UNAUTHORIZED)

    # --- создание ---
    def test_owner_can_create_lesson(self):
        self.client.force_authenticate(user=self.owner)
        data = {
            'course': self.course.id,
            'title': 'Новый урок',
            'description': 'Описание',
            'video_url': 'https://www.youtube.com/watch?v=abc',
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['owner'], self.owner.id)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_moderator_cannot_create_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(self.create_url, {'course': self.course.id, 'title': 'Нельзя'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- получение ---
    def test_owner_can_retrieve_own_lesson(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_other_user_cannot_retrieve_foreign_lesson(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_retrieve_any_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_owner_sees_only_own_lessons_in_list(self):
        Lesson.objects.create(course=self.course, title='Чужой урок', owner=self.other)
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_moderator_sees_all_lessons_in_list(self):
        Lesson.objects.create(course=self.course, title='Чужой урок', owner=self.other)
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.list_url)
        self.assertEqual(response.data['count'], 2)

    # --- обновление ---
    def test_owner_can_update_own_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.update_url, {'title': 'Изменено'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Изменено')

    def test_moderator_can_update_any_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(self.update_url, {'title': 'Правка модератора'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_update_foreign_lesson(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(self.update_url, {'title': 'Взлом'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- удаление ---
    def test_owner_can_delete_own_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_moderator_cannot_delete_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_other_user_cannot_delete_foreign_lesson(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- валидация ссылок ---
    def test_create_with_foreign_video_url_fails(self):
        self.client.force_authenticate(user=self.owner)
        data = {'course': self.course.id, 'title': 'Плохой урок',
                'video_url': 'https://rutube.ru/video/123/'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)

    def test_create_with_foreign_link_in_description_fails(self):
        self.client.force_authenticate(user=self.owner)
        data = {'course': self.course.id, 'title': 'Плохой урок',
                'description': 'Материалы тут: https://my-site.ru/lesson'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_with_foreign_link_fails(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.update_url, {'video_url': 'https://vimeo.com/1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SubscriptionTestCase(APITestCase):
    """Подписка: создание, удаление, сообщения, ошибки, признак в курсе."""

    def setUp(self):
        self.user = User.objects.create_user(email='sub@test.ru', password='TestPass123')
        self.course = Course.objects.create(title='Курс', owner=self.user)
        self.subscribe_url = reverse('lms:subscribe')
        self.course_url = reverse('lms:course-detail', args=[self.course.id])

    def test_subscribe_and_unsubscribe(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.subscribe_url, {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка добавлена')
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        response = self.client.post(self.subscribe_url, {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка удалена')
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_is_subscribed_flag_in_course(self):
        self.client.force_authenticate(user=self.user)
        self.assertFalse(self.client.get(self.course_url).data['is_subscribed'])

        self.client.post(self.subscribe_url, {'course_id': self.course.id})
        self.assertTrue(self.client.get(self.course_url).data['is_subscribed'])

    def test_anonymous_cannot_subscribe(self):
        response = self.client.post(self.subscribe_url, {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_without_course_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.subscribe_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_with_invalid_course_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.subscribe_url, {'course_id': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_to_missing_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.subscribe_url, {'course_id': 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_is_unique(self):
        Subscription.objects.create(user=self.user, course=self.course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subscription.objects.create(user=self.user, course=self.course)


class PaginationTestCase(APITestCase):
    """Пагинация курсов и уроков."""

    def setUp(self):
        self.user = User.objects.create_user(email='page@test.ru', password='TestPass123')
        self.course = Course.objects.create(title='Курс', owner=self.user)
        for i in range(12):
            Lesson.objects.create(course=self.course, title=f'Урок {i}', owner=self.user)
        for i in range(7):
            Course.objects.create(title=f'Курс {i}', owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_lessons_paginated(self):
        response = self.client.get(reverse('lms:lesson-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])

    def test_courses_paginated(self):
        response = self.client.get(reverse('lms:course-list'))
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 5)

    def test_page_size_query_param(self):
        response = self.client.get(reverse('lms:lesson-list'), {'page_size': 3})
        self.assertEqual(len(response.data['results']), 3)

    def test_max_page_size_limit(self):
        response = self.client.get(reverse('lms:lesson-list'), {'page_size': 1000})
        self.assertLessEqual(len(response.data['results']), 50)


class CourseTestCase(APITestCase):
    """CRUD курсов и права доступа."""

    def setUp(self):
        self.owner = User.objects.create_user(email='cowner@test.ru', password='TestPass123')
        self.other = User.objects.create_user(email='cother@test.ru', password='TestPass123')
        self.moderator = User.objects.create_user(email='cmoder@test.ru', password='TestPass123')
        group, _ = Group.objects.get_or_create(name=MODERATORS_GROUP)
        self.moderator.groups.add(group)

        self.course = Course.objects.create(title='Курс', owner=self.owner)
        self.detail_url = reverse('lms:course-detail', args=[self.course.id])
        self.list_url = reverse('lms:course-list')

    def test_owner_can_create_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {'title': 'Новый курс'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['owner'], self.owner.id)

    def test_moderator_cannot_create_course(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(self.list_url, {'title': 'Нельзя'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_cannot_delete_course(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_update_any_course(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(self.detail_url, {'title': 'Правка'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_see_foreign_course(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_own_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_course_with_foreign_link_fails(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            'title': 'Курс', 'description': 'Материалы: https://skillbox.ru/course'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)