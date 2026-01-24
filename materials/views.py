from rest_framework import viewsets
from .models import Course
from .serializers import CourseSerializer

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Lesson
from .serializers import LessonSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonListCreateView(ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class LessonRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer