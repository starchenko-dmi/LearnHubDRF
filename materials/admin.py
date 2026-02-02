from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Course, Lesson

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'lessons_count', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('title', 'description', 'owner__email')
    readonly_fields = ('preview_tag',)  # если хотите показывать превью как картинку

    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = 'Количество уроков'

    # Опционально: отображение превью как картинки в админке
    def preview_tag(self, obj):
        if obj.preview:
            return f'<img src="{obj.preview.url}" style="max-height: 100px; max-width: 100px;" />'
        return "-"
    preview_tag.short_description = 'Превью'
    preview_tag.allow_tags = True

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'owner', 'created_at')
    list_filter = ('course', 'owner', 'created_at')
    search_fields = ('title', 'description', 'course__title', 'owner__email')
    readonly_fields = ('preview_tag',)

    def preview_tag(self, obj):
        if obj.preview:
            return mark_safe(f'<img src="{obj.preview.url}" style="max-height: 100px; max-width: 100px;" />')
        return "-"
