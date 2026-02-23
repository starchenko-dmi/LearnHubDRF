import stripe
from rest_framework import viewsets, generics, permissions

from .paginators import MaterialsPagination
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator

from django.shortcuts import get_object_or_404
from .models import Course, Subscription, Lesson
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.stripe_service import create_stripe_product, create_stripe_price, create_stripe_checkout_session
from users.models import Payment

from users.tasks import send_course_update_notification
from django.utils import timezone
from datetime import timedelta





class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class CourseViewSet(viewsets.ModelViewSet):
    pagination_class = MaterialsPagination
    serializer_class = CourseSerializer
    queryset = Course.objects.all()  # ←←← ОБЯЗАТЕЛЬНО!

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Все авторизованные могут смотреть
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            # Модераторы или владельцы — могут редактировать
            permission_classes = [permissions.IsAuthenticated, IsModerator | IsOwner]
        elif self.action in ['create', 'destroy']:
            # Только владельцы (не модераторы!)
            permission_classes = [permissions.IsAuthenticated, ~IsModerator & IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        course = serializer.save()

        # Доп. задание: отправлять только если прошло >4 часов с последнего обновления
        if not course.last_updated or (timezone.now() - course.last_updated) > timedelta(hours=4):
            # Обновляем метку времени
            course.last_updated = timezone.now()
            course.save(update_fields=['last_updated'])

            # Запускаем асинхронную рассылку
            send_course_update_notification.delay(course.id, course.title)

class LessonListCreateView(generics.ListCreateAPIView):
    pagination_class = MaterialsPagination
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            # Создание — только не модераторы
            permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            permission_classes = [permissions.IsAuthenticated, IsModerator | IsOwner]
        elif self.request.method == 'DELETE':
            permission_classes = [permissions.IsAuthenticated, ~IsModerator & IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class SubscriptionView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            subscription.delete()
            message = "подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course)
            message = "подписка добавлена"

        return Response({"message": message})


class CoursePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = Course.objects.get(id=course_id)
        user = request.user

        # 1. Создаём продукт
        product = create_stripe_product(course.title, course.description)

        # 2. Создаём цену
        price = create_stripe_price(product['id'], int(course.price))  # предполагается, что у Course есть поле price

        # 3. Создаём сессию
        success_url = "http://127.0.0.1:8000/payment/success/"
        cancel_url = "http://127.0.0.1:8000/payment/cancel/"
        session = create_stripe_checkout_session(price['id'], success_url, cancel_url)

        # 4. Сохраняем в БД
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            payment_method='transfer',
            stripe_session_id=session['id'],
            stripe_payment_url=session['url']
        )

        return Response({
            "message": "Переходите к оплате",
            "payment_url": session['url'],
            "session_id": session['id']
        })


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = stripe.checkout.Session.retrieve(session_id)
        return Response({
            "status": session["payment_status"],
            "session": session
        })