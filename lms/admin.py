from django.contrib import admin
from .models import Course, Lesson

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # Используем реальные поля модели: title и description
    list_display = ('title', 'description')
    search_fields = ('title',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    # Используем реальные поля модели: title, course, description
    list_display = ('title', 'course', 'description')
    list_filter = ('course',)
    search_fields = ('title',)