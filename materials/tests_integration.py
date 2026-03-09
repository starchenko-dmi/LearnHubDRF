import os
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Course

User = get_user_model()


class StripeIntegrationTest(APITestCase):
    def setUp(self):
        # Создаём пользователя и курс независимо от Stripe
        self.user = User.objects.create_user(email='test@example.com', password='pass123')
        self.course = Course.objects.create(
            title='Интеграционный курс',
            description='Курс для теста Stripe',
            owner=self.user,
            price=999.00
        )

    @patch('materials.views.stripe.checkout.Session.create')  # ← замените 'materials.views' на путь к вашему view
    def test_create_payment_session(self, mock_stripe_create):
        """Тест создания сессии оплаты (Stripe мокается)"""
        self.client.force_authenticate(user=self.user)

        # Мокаем ответ Stripe
        mock_stripe_create.return_value = {
            'id': 'cs_test_123abc',
            'url': 'https://checkout.stripe.com/pay/cs_test_123abc'
        }

        # Запрос на создание сессии
        response = self.client.post(f'/api/courses/{self.course.id}/pay/')

        # Проверки
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        self.assertIn('session_id', response.data)
        self.assertEqual(response.data['session_id'], 'cs_test_123abc')
        self.assertEqual(response.data['payment_url'], 'https://checkout.stripe.com/pay/cs_test_123abc')

        # Убедимся, что Stripe был вызван с правильными параметрами
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        self.assertEqual(call_args['mode'], 'payment')
        self.assertIn('line_items', call_args)

    @patch('materials.views.stripe.checkout.Session.retrieve')  # ← замените 'materials.views' на путь к вашему view
    def test_check_payment_status_paid(self, mock_stripe_retrieve):
        """Тест проверки статуса оплаты — успешный платёж"""
        self.client.force_authenticate(user=self.user)

        # Мокаем успешный платёж
        mock_stripe_retrieve.return_value = {'payment_status': 'paid'}

        session_id = 'cs_test_123abc'
        response = self.client.get(f'/api/payment/status/{session_id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')
        mock_stripe_retrieve.assert_called_once_with(session_id)

    @patch('materials.views.stripe.checkout.Session.retrieve')
    def test_check_payment_status_unpaid(self, mock_stripe_retrieve):
        """Тест проверки статуса оплаты — неоплачено"""
        self.client.force_authenticate(user=self.user)

        mock_stripe_retrieve.return_value = {'payment_status': 'unpaid'}

        session_id = 'cs_test_123abc'
        response = self.client.get(f'/api/payment/status/{session_id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unpaid')