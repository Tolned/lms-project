from rest_framework.permissions import BasePermission

MODERATORS_GROUP = 'moderators'


class IsModerator(BasePermission):
    """Пользователь состоит в группе модераторов."""

    message = 'Доступ разрешён только модераторам.'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.groups.filter(name=MODERATORS_GROUP).exists()
        )

    # ВАЖНО: без этого метода оператор ~IsModerator всегда запрещал бы доступ
    # на объектном уровне (BasePermission.has_object_permission возвращает True,
    # а инверсия превращает его в False).
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwner(BasePermission):
    """Доступ только владельцу объекта. Применяется к Course и Lesson."""

    message = 'Вы не являетесь владельцем этого объекта.'

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id