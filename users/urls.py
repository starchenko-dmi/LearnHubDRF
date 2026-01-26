from django.urls import path
from .views import UserCreateView, UserListView, PaymentListAPIView

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('', UserListView.as_view(), name='user-lisr'),
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
]