import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .tasks import send_course_update_notification, deactivate_inactive_users
from materials.models import Subscription
from materials.models import Subscription, Course

User = get_user_model()


@override_settings(DEFAULT_FROM_EMAIL='test@example.com')
@patch('users.tasks.send_mail')
def test_send_course_update_notification(self, mock_send_mail):
    # Создаём пользователя
    user = User.objects.create_user(email='subscriber@example.com', password='pass123')

    # Создаём курс (чтобы существовал ID)
    course = Course.objects.create(
        title="Новый курс",
        description="Тест",
        owner=user,
        price=1000.00
    )

    # Создаём подписку
    Subscription.objects.create(user=user, course=course)

    # Вызываем задачу
    send_course_update_notification(course.id, course.title)

    # Проверяем отправку
    mock_send_mail.assert_called_once_with(
        f"Обновление курса: {course.title}",
        f"Курс «{course.title}» был обновлён. Посмотрите новые материалы!",
        'test@example.com',
        ['subscriber@example.com']
    )


class CeleryTasksTest(TestCase):

    @override_settings(DEFAULT_FROM_EMAIL='test@example.com')
    @patch('users.tasks.send_mail')
    def test_send_course_update_notification(self, mock_send_mail):
        # 1. Создаём пользователя
        user = User.objects.create_user(
            email='subscriber@example.com',
            password='pass123'
        )

        # 2. Создаём курс
        course = Course.objects.create(
            title="Курс Python",
            description="Описание",
            owner=user,
            price=1000.00
        )

        # 3. Создаём подписку — ЭТО ОБЯЗАТЕЛЬНО!
        Subscription.objects.create(user=user, course=course)

        # 4. Вызываем задачу
        from users.tasks import send_course_update_notification
        send_course_update_notification(course.id, course.title)

        # 5. Проверяем вызов
        mock_send_mail.assert_called_once_with(
            "Обновление курса: Курс Python",
            "Курс «Курс Python» был обновлён. Посмотрите новые материалы!",
            'test@example.com',
            ['subscriber@example.com']
        )