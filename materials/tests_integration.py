import os
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Course

User = get_user_model()

# Запускать только при наличии ключа
@override_settings(
    STRIPE_SECRET_KEY=os.getenv('STRIPE_SECRET_KEY'),
    STRIPE_PUBLIC_KEY=os.getenv('STRIPE_PUBLIC_KEY')
)
class StripeIntegrationTest(APITestCase):
    def setUp(self):
        if not os.getenv('STRIPE_SECRET_KEY'):
            self.skipTest("Тестовые ключи Stripe не заданы")

        self.user = User.objects.create_user(email='test@example.com', password='pass123')
        self.course = Course.objects.create(
            title='Интеграционный курс',
            description='Курс для теста Stripe',
            owner=self.user,
            price=999.00  # 999 рублей
        )

    def test_full_stripe_payment_flow(self):
        """Полный цикл: создание продукта → цены → сессии → получение статуса"""
        self.client.force_authenticate(user=self.user)

        # 1. Создаём сессию оплаты
        response = self.client.post(f'/api/courses/{self.course.id}/pay/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        self.assertIn('session_id', response.data)

        session_id = response.data['session_id']

        # 2. Проверяем статус сессии (до оплаты — unpaid)
        status_response = self.client.get(f'/api/payment/status/{session_id}/')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertIn('status', status_response.data)
        # До оплаты: 'unpaid' или 'no_payment_required'
        self.assertIn(status_response.data['status'], ['unpaid', 'no_payment_required'])

        # 3. (Опционально) Проверка вручную:
        print(f"\n👉 Перейдите по ссылке для тестовой оплаты:\n{response.data['payment_url']}")
        print("Используйте карту: 4242 4242 4242 4242")
        input("После оплаты нажмите Enter для проверки статуса...")

        # 4. Повторная проверка статуса (после оплаты — paid)
        final_status = self.client.get(f'/api/payment/status/{session_id}/')
        print("Финальный статус:", final_status.data)
        # После успешной оплаты: 'paid'
        # self.assertEqual(final_status.data['status'], 'paid')  # раскомментируйте, если хотите строгую проверку