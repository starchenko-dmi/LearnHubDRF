from django.urls import path

from .views import (CoursePaymentView, LessonListCreateView,
                    LessonRetrieveUpdateDestroyView, PaymentStatusView,
                    SubscriptionView)

urlpatterns = [
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list-create"),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyView.as_view(),
        name="lesson-detail",
    ),
    path("subscribe/", SubscriptionView.as_view(), name="subscription"),
    path(
        "courses/<int:course_id>/pay/", CoursePaymentView.as_view(), name="course-pay"
    ),
    path(
        "payment/status/<str:session_id>/",
        PaymentStatusView.as_view(),
        name="payment-status",
    ),
]
