from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, Payment
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    PaymentSerializer,
)


class UserCreateAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя."""
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация пользователя",
        description="Создает нового пользователя и возвращает JWT токены.",
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(description="Пользователь создан, возвращены токены"),
            400: OpenApiResponse(description="Ошибка валидации"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserListAPIView(generics.ListAPIView):
    """Список всех пользователей."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    @extend_schema(
        summary="Список пользователей",
        description="Возвращает список всех пользователей.",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Получение, обновление и удаление пользователя."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    @extend_schema(
        summary="Получение пользователя",
        description="Возвращает данные конкретного пользователя.",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Обновление пользователя",
        description="Позволяет обновить данные пользователя.",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление пользователя",
        description="Позволяет частично обновить данные пользователя.",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление пользователя",
        description="Удаляет пользователя.",
        responses={204: OpenApiResponse(description="Пользователь удален")}
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра платежей."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Защита от ошибки при генерации схемы drf-spectacular (fake view)
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        return Payment.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Список платежей",
        description="Возвращает все платежи текущего пользователя.",
        responses={200: PaymentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Детали платежа",
        description="Возвращает информацию о конкретном платеже.",
        responses={200: PaymentSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)