from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from .models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@test.com', password='pass123')
        self.moderator_group = Group.objects.create(name='moderators')
        self.moderator = User.objects.create_user(email='mod@test.com', password='pass123')
        self.moderator.groups.add(self.moderator_group)
        self.course = Course.objects.create(title='Test Course', description='Desc', owner=self.user)

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

        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())


class StripePaymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@test.com', password='pass123')
        self.course = Course.objects.create(
            title='Test Course',
            description='Test description',
            owner=self.user,
            price=1000.00
        )

    @patch('materials.services.stripe_service.stripe.Product.create')
    @patch('materials.services.stripe_service.stripe.Price.create')
    @patch('materials.services.stripe_service.stripe.checkout.Session.create')
    def test_create_payment_session(self, mock_session, mock_price, mock_product):
        mock_product.return_value = {'id': 'prod_test'}
        mock_price.return_value = {'id': 'price_test'}
        mock_session.return_value = {
            'id': 'cs_test_abc',
            'url': 'https://checkout.stripe.com/pay/cs_test_abc'
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/courses/{self.course.id}/pay/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], 'cs_test_abc')
        self.assertIn('payment_url', response.data)

    @patch('materials.services.stripe_service.stripe.checkout.Session.retrieve')
    def test_check_payment_status(self, mock_retrieve):
        mock_retrieve.return_value = {'payment_status': 'paid'}

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/payment/status/cs_test_abc/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')


class CourseUpdateNotificationTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='pass123')
        self.subscriber = User.objects.create_user(email='sub@example.com', password='pass123')
        self.course = Course.objects.create(
            title='Course', description='Desc', owner=self.owner, price=1000.00
        )
        Subscription.objects.create(user=self.subscriber, course=self.course)

    @patch('materials.views.send_course_update_notification')
    def test_course_update_triggers_email_task(self, mock_task):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/courses/{self.course.id}/',
            {'title': 'Updated'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.delay.assert_called_once_with(self.course.id, 'Updated')

    @patch('materials.views.send_course_update_notification')
    def test_no_email_if_updated_within_4_hours(self, mock_task):
        from django.utils import timezone
        self.course.last_updated = timezone.now()
        self.course.save()

        self.client.force_authenticate(user=self.owner)
        self.client.patch(f'/api/courses/{self.course.id}/', {'description': 'New'}, format='json')

        mock_task.delay.assert_not_called()
