from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'description', 'owner']
        read_only_fields = ['owner']  # владелец проставляется в perform_create


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'owner', 'lessons_count', 'lessons']
        read_only_fields = ['owner']

    def get_lessons_count(self, obj):
        return obj.lessons.count()