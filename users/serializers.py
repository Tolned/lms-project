from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers

from .models import Payment

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'payment_date', 'course', 'lesson',
                  'course_title', 'lesson_title', 'amount', 'payment_method']


class UserPaymentHistorySerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'payment_date', 'course_title', 'lesson_title', 'amount', 'payment_method']


class UserSerializer(serializers.ModelSerializer):
    """Чтение профиля пользователя + история платежей."""
    payment_history = UserPaymentHistorySerializer(many=True, read_only=True, source='payments')

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'city', 'payment_history']


class UserCreateSerializer(serializers.ModelSerializer):
    """Регистрация пользователя."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'city', 'password']

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return value

    def create(self, validated_data):
        try:
            return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email уже зарегистрирован.'}
            )


class UserUpdateSerializer(serializers.ModelSerializer):
    """Обновление профиля, в том числе смена пароля."""
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'city', 'password']
        read_only_fields = ['id']

    def validate_email(self, value):
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Этот email уже занят другим пользователем.')
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance