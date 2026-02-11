from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com', password='pass123'
        )
        self.moderator_group = Group.objects.create(name='moderators')
        self.moderator = User.objects.create_user(
            email='mod@test.com', password='pass123'
        )
        self.moderator.groups.add(self.moderator_group)

        self.course = Course.objects.create(
            title='Test Course', description='Desc', owner=self.user
        )

    def test_create_lesson_valid_youtube(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Lesson 1',
            'description': 'Desc',
            'video_url': 'https://www.youtube.com/watch?v=abc123',
            'course': self.course.id
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_lesson_invalid_url(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Lesson 1',
            'description': 'Desc',
            'video_url': 'https://vimeo.com/123',
            'course': self.course.id
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_moderator_cannot_create_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        data = {
            'title': 'Lesson 1',
            'description': 'Desc',
            'video_url': 'https://youtu.be/abc123',
            'course': self.course.id
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@test.com', password='pass123')
        self.course = Course.objects.create(title='Course', description='Desc', owner=self.user)

    def test_subscribe_and_unsubscribe(self):
        self.client.force_authenticate(user=self.user)

        # Подписка
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        # Отписка
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())