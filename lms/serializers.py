from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import Course, Lesson
from .validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        required=False, allow_blank=True, validators=[validate_youtube_url]
    )
    video_url = serializers.URLField(
        required=False, allow_blank=True, allow_null=True,
        validators=[validate_youtube_url],
    )

    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'description', 'video_url', 'owner']
        read_only_fields = ['owner']


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    description = serializers.CharField(
        required=False, allow_blank=True, validators=[validate_youtube_url]
    )

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'owner',
            'lessons_count', 'lessons', 'is_subscribed', 'updated_at'
        ]
        read_only_fields = ['owner']

    @extend_schema_field(int)
    def get_lessons_count(self, obj):
        return obj.lessons.count()

    @extend_schema_field(bool)
    def get_is_subscribed(self, obj):
        """Подписан ли текущий пользователь на обновления этого курса."""
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.subscriptions.filter(user=request.user).exists()