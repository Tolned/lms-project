from rest_framework import serializers
from django.conf import settings
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    # Для красивого вывода названий курса/урока вместо просто ID
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'payment_date', 'course', 'lesson',
            'course_title', 'lesson_title', 'amount', 'payment_method'
        ]


# Дополнительное задание: история платежей в профиле пользователя
class UserPaymentHistorySerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'payment_date', 'course_title', 'lesson_title', 'amount', 'payment_method']


class UserSerializer(serializers.ModelSerializer):
    # Выводим историю платежей пользователя
    payment_history = UserPaymentHistorySerializer(many=True, read_only=True, source='payments')

    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ['id', 'email', 'phone', 'city', 'avatar', 'payment_history']