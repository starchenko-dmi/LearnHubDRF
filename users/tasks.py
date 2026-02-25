# users/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from materials.models import Subscription

User = get_user_model()

@shared_task
def send_course_update_notification(course_id, course_title):
    subscriptions = Subscription.objects.filter(course_id=course_id)
    recipients = [sub.user.email for sub in subscriptions if sub.user.email]

    if not recipients:
        return

    subject = f"Обновление курса: {course_title}"
    message = f"Курс «{course_title}» был обновлён. Посмотрите новые материалы!"
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, message, from_email, recipients)


@shared_task
def deactivate_inactive_users():
    one_month_ago = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(
        last_login__lt=one_month_ago,
        is_active=True
    )
    count = inactive_users.update(is_active=False)
    print(f"Deactivated {count} inactive users")