from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        # Укажите здесь реальные поля вашей модели Lesson
        fields = ['id', 'title', 'description']


class CourseSerializer(serializers.ModelSerializer):
    # Задание 1: Поле для подсчета количества уроков
    lessons_count = serializers.SerializerMethodField()

    # Задание 3: Поле для вывода списка уроков через вложенный сериализатор
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'lessons_count', 'lessons']

    def get_lessons_count(self, obj):
        # obj - это экземпляр Course. related_name='lessons' позволяет так делать
        return obj.lessons.count()