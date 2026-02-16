from django.test import TestCase
from django.contrib.auth.models import Group
from .models import Course, Lesson, Subscription

import stripe
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Course

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


User = get_user_model()

class StripePaymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@test.com', password='pass123')
        self.course = Course.objects.create(
            title='Test Course',
            description='Test description',
            owner=self.user,
            price=1000.00  # обязательно добавьте поле price в модель Course
        )

    @patch('materials.services.stripe_service.stripe.Product.create')
    @patch('materials.services.stripe_service.stripe.Price.create')
    @patch('materials.services.stripe_service.stripe.checkout.Session.create')
    def test_create_payment_session(self, mock_session_create, mock_price_create, mock_product_create):
        # Настройка моков
        mock_product_create.return_value = {'id': 'prod_test123'}
        mock_price_create.return_value = {'id': 'price_test456'}
        mock_session_create.return_value = {
            'id': 'cs_test_abc',
            'url': 'https://checkout.stripe.com/pay/cs_test_abc'
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.post(f'/api/courses/{self.course.id}/pay/')

        # Проверки
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        self.assertEqual(response.data['session_id'], 'cs_test_abc')

        # Проверяем, что моки вызывались с правильными аргументами
        mock_product_create.assert_called_once_with(name=self.course.title, description=self.course.description)
        mock_price_create.assert_called_once_with(
            product='prod_test123',
            unit_amount=100000,
            currency='rub'
        )
        mock_session_create.assert_called_once()

    @patch('materials.services.stripe_service.stripe.checkout.Session.retrieve')
    def test_check_payment_status(self, mock_session_retrieve):
        mock_session_retrieve.return_value = {
            'id': 'cs_test_abc',
            'payment_status': 'paid',
            'status': 'complete'
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/payment/status/cs_test_abc/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')
        mock_session_retrieve.assert_called_once_with('cs_test_abc')