from django.urls import path

from .views import (PaymentListAPIView, UserCreateView, UserProfileView,
                    UserPublicProfileView)

app_name = "users"

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="user-register"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("<int:pk>/", UserPublicProfileView.as_view(), name="user-public-detail"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
]
