from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, UserViewSet

app_name = 'users'  # <-- ДОБАВИТЬ ЭТУ СТРОКУ!

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]