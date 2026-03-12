from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Payment, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Поля для отображения в списке
    list_display = ("email", "phone", "city", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "groups")
    search_fields = ("email", "phone", "city")

    # Поля при редактировании пользователя
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Персональная информация", {"fields": ("phone", "city", "avatar")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    # Поля при создании нового пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "phone",
                    "city",
                    "avatar",
                ),
            },
        ),
    )

    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "lesson",
        "amount",
        "payment_method",
        "payment_date",
    )
    list_filter = ("payment_method", "payment_date", "course", "lesson")
    search_fields = ("user__email", "course__title", "lesson__title")
    readonly_fields = ("payment_date",)
