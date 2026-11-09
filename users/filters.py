import django_filters
from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    # Сортировка по дате
    payment_date = django_filters.OrderingFilter(fields=('payment_date',))

    # Фильтры по связанным моделям (используем строковые ссылки, чтобы избежать циклического импорта)
    course = django_filters.ModelChoiceFilter(
        queryset=lambda: Payment._meta.get_field('course').related_model.objects.all(),
        field_name='course'
    )
    lesson = django_filters.ModelChoiceFilter(
        queryset=lambda: Payment._meta.get_field('lesson').related_model.objects.all(),
        field_name='lesson'
    )

    # Фильтр по способу оплаты
    payment_method = django_filters.ChoiceFilter(choices=Payment.PAYMENT_METHOD_CHOICES, field_name='payment_method')

    class Meta:
        model = Payment
        fields = ['course', 'lesson', 'payment_method', 'payment_date']