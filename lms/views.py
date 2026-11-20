from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
import stripe

from users.permissions import IsModerator, IsOwner, MODERATORS_GROUP
from users.models import Payment
from .models import Course, Lesson, Subscription
from .paginators import LmsPagination
from .serializers import CourseSerializer, LessonSerializer
from .services import (
    create_stripe_product_and_price,
    create_stripe_checkout_session,
    get_stripe_session_status,
)
from .tasks import send_course_update_notification  # <-- ИМПОРТ ЗАДАЧИ


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    pagination_class = LmsPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Course.objects.none()
        if user.is_superuser or user.groups.filter(name=MODERATORS_GROUP).exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        # 1. Сохраняем изменения (автоматически обновится поле updated_at)
        instance = serializer.save()
        # 2. ВЫЗЫВАЕМ отложенную задачу рассылки
        send_course_update_notification.delay(instance.id)

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

    def perform_update(self, serializer):
        instance = serializer.save()
        course = instance.course

        # Дополнительное задание: проверка, что курс не обновлялся более 4 часов
        four_hours_ago = timezone.now() - timedelta(hours=4)

        if course.updated_at < four_hours_ago:
            # Вызываем задачу рассылки
            send_course_update_notification.delay(course.id)
            # Сбрасываем таймер, чтобы следующие обновления уроков в течение 4 часов не спамили
            course.updated_at = timezone.now()
            course.save(update_fields=['updated_at'])


class LessonDestroyAPIView(generics.DestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwner, ~IsModerator]


class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Управление подпиской на курс",
        request={'application/json': {'type': 'object', 'properties': {'course_id': {'type': 'integer'}},
                                      'required': ['course_id']}},
        responses={200: OpenApiResponse(description="Успех")}
    )
    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        if course_id is None:
            return Response({'detail': 'Не передан course_id.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course_id = int(course_id)
        except (TypeError, ValueError):
            return Response({'detail': 'course_id должен быть целым числом.'}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, pk=course_id)
        subs_item = Subscription.objects.filter(user=request.user, course=course)

        if subs_item.exists():
            subs_item.delete()
            message = 'подписка удалена'
        else:
            Subscription.objects.create(user=request.user, course=course)
            message = 'подписка добавлена'

        return Response({'message': message}, status=status.HTTP_200_OK)


class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание платежа через Stripe",
        request={'application/json': {'type': 'object',
                                      'properties': {'course_id': {'type': 'integer'}, 'amount': {'type': 'number'}},
                                      'required': ['course_id']}},
        responses={200: OpenApiResponse(description="Ссылка на оплату")}
    )
    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'detail': 'Не передан course_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'detail': 'Курс не найден.'}, status=status.HTTP_404_NOT_FOUND)

        amount = request.data.get('amount', course.price)
        if not amount:
            return Response({'detail': 'Не указана сумма.'}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            user=request.user, course=course, amount=amount, payment_method='stripe', status='pending'
        )

        try:
            create_stripe_product_and_price(course, payment)
            payment_url = create_stripe_checkout_session(payment, course)
        except stripe.error.StripeError as e:
            payment.status = 'canceled'
            payment.save()
            return Response({'detail': f'Ошибка Stripe: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'payment_id': payment.id, 'payment_url': payment_url, 'status': payment.status},
                        status=status.HTTP_200_OK)


class PaymentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверка статуса платежа",
        parameters=[OpenApiParameter(name='payment_id', type=int, location=OpenApiParameter.QUERY)],
        responses={200: OpenApiResponse(description="Статус платежа")}
    )
    def get(self, request, *args, **kwargs):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({'detail': 'Не передан payment_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response({'detail': 'Платеж не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if not payment.stripe_session_id:
            return Response({'detail': 'Отсутствует ID сессии Stripe.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stripe_status = get_stripe_session_status(payment.stripe_session_id)
            payment.status = 'paid' if stripe_status == 'paid' else stripe_status
            payment.save()
        except stripe.error.StripeError as e:
            return Response({'detail': f'Ошибка Stripe: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'payment_id': payment.id, 'status': payment.status, 'stripe_status': stripe_status})