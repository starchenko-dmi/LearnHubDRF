from django.urls import path
from .views import LessonListCreateView, LessonRetrieveUpdateDestroyView, SubscriptionView

urlpatterns = [
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyView.as_view(), name='lesson-detail'),
    path('subscribe/', SubscriptionView.as_view(), name='subscription'),
]
