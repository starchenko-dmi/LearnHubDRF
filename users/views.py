from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     RetrieveAPIView, RetrieveUpdateAPIView)
from rest_framework.permissions import AllowAny

from .models import Payment, User
from .serializers import (PaymentSerializer, UserProfileSerializer,
                          UserPublicSerializer, UserSerializer)


class UserCreateView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserProfileView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer  # ← используем новый
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserPublicProfileView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer  # ← только публичные поля
    permission_classes = [permissions.IsAuthenticated]


class PaymentListAPIView(ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "course": ["exact"],
        "lesson": ["exact"],
        "payment_method": ["exact"],
    }
    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]  # по умолчанию — новые сверху

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
