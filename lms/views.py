from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsModerator, IsOwner, MODERATORS_GROUP
from .models import Course, Lesson, Subscription
from .paginators import LmsPagination
from .serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    pagination_class = LmsPagination

    def get_queryset(self):
        """Модератор и админ видят все курсы, обычный пользователь — только свои."""
        user = self.request.user
        if not user.is_authenticated:
            return Course.objects.none()
        if user.is_superuser or user.groups.filter(name=MODERATORS_GROUP).exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated, ~IsModerator]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsOwner, ~IsModerator]
        elif self.action in ('list', 'retrieve', 'update', 'partial_update'):
            permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class LessonCreateAPIView(generics.CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModerator]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LmsPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.is_superuser or user.groups.filter(name=MODERATORS_GROUP).exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModerator | IsOwner]


class LessonUpdateAPIView(generics.UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModerator | IsOwner]


class LessonDestroyAPIView(generics.DestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwner, ~IsModerator]


class SubscriptionAPIView(APIView):
    """Переключатель подписки: нет подписки — создаём, есть — удаляем."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')

        if course_id is None:
            return Response(
                {'detail': 'Не передан обязательный параметр course_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_id = int(course_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'course_id должен быть целым числом.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = get_object_or_404(Course, pk=course_id)
        subs_item = Subscription.objects.filter(user=request.user, course=course)

        if subs_item.exists():
            subs_item.delete()
            message = 'подписка удалена'
        else:
            Subscription.objects.create(user=request.user, course=course)
            message = 'подписка добавлена'

        return Response({'message': message}, status=status.HTTP_200_OK)