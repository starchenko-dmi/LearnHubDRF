from rest_framework import serializers
from .models import Course, Lesson

from .validators import validate_youtube_url

class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'preview', 'lessons_count', 'lessons', 'is_subscribed']
        read_only_fields = ['owner']

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.subscriptions.filter(user=user).exists()
        return False

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
        fields = '__all__'
        read_only_fields = ['owner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем валидатор к полю video_url
        self.fields['video_url'].validators.append(validate_youtube_url)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('owner', None)
        return data
