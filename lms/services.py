import stripe
from decimal import Decimal
from django.conf import settings
from .models import Course
from users.models import Payment


def get_stripe_client():
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    return stripe


def create_stripe_product_and_price(course: Course, payment: Payment):
    stripe_client = get_stripe_client()
    try:
        product = stripe_client.Product.create(
            name=course.title,
            description=course.description or 'Описание курса',
        )
        payment.stripe_product_id = product.id

        # Цена передается в копейках (или центах)
        amount_in_cents = int(Decimal(str(payment.amount)) * 100)

        price = stripe_client.Price.create(
            product=product.id,
            unit_amount=amount_in_cents,
            currency='rub',  # Можно изменить на 'usd' для тестов, если rub недоступен в аккаунте
        )
        payment.stripe_price_id = price.id
        payment.save()

        return price.id
    except stripe_client.error.StripeError as e:
        raise e


def create_stripe_checkout_session(payment: Payment, course: Course):
    stripe_client = get_stripe_client()
    try:
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': payment.stripe_price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=getattr(settings, 'STRIPE_SUCCESS_URL', 'http://localhost:8000/lms/payment/success/'),
            cancel_url=getattr(settings, 'STRIPE_CANCEL_URL', 'http://localhost:8000/lms/payment/cancel/'),
            metadata={
                'payment_id': payment.id,
                'course_id': course.id,
                'user_id': payment.user.id,
            }
        )
        payment.stripe_session_id = session.id
        payment.payment_url = session.url
        payment.save()

        return session.url
    except stripe_client.error.StripeError as e:
        raise e


def get_stripe_session_status(session_id: str):
    stripe_client = get_stripe_client()
    try:
        session = stripe_client.checkout.Session.retrieve(session_id)
        return session.payment_status
    except stripe_client.error.StripeError as e:
        raise e