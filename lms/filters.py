import django_filters
from .models import Payment
from lms.models import Course, Lesson


class PaymentFilter(django_filters.FilterSet):
    # Сортировка по дате (возрастание/убывание)
    # Позволяет передавать ?ordering=payment_date или ?ordering=-payment_date
    payment_date = django_filters.OrderingFilter(
        fields=('payment_date',),
        field_labels={'payment_date': 'Дата оплаты'}
    )

    # Фильтрация по курсу (принимает ID курса)
    course = django_filters.ModelChoiceFilter(
        queryset=Course.objects.all(),
        field_name='course'
    )

    # Фильтрация по уроку (принимает ID урока)
    lesson = django_filters.ModelChoiceFilter(
        queryset=Lesson.objects.all(),
        field_name='lesson'
    )

    # Фильтрация по способу оплаты
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        field_name='payment_method'
    )

    class Meta:
        model = Payment
        fields = ['course', 'lesson', 'payment_method', 'payment_date']