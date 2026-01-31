from rest_framework import serializers
from .models import Course, Lesson

class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'preview', 'lessons_count', 'lessons', 'owner']
        read_only_fields = ['owner']  # ←←← КЛЮЧЕВАЯ СТРОКА

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_lessons(self, obj):
        return LessonSerializer(obj.lessons.all(), many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data.pop('owner', None)  # скрываем из ответа
        return data


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'preview', 'video_url', 'course', 'owner']
        read_only_fields = ['owner']  # ←←← ОБЯЗАТЕЛЬНО

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data.pop('owner', None)
        return data
