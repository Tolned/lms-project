from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.contrib.auth import get_user_model

from .models import Payment
from .serializers import PaymentSerializer, UserSerializer
from .filters import PaymentFilter

User = get_user_model()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для вывода пользователей с историей их платежей (Доп. задание)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer