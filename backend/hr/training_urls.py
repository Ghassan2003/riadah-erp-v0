from django.urls import path
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .enhanced_views import (
    TrainingNeedListView, TrainingNeedCreateView,
    CourseListView, CourseDetailView,
    TrainingSessionListView, TrainingSessionCreateView,
    TrainingEnrollmentListView, TrainingEnrollmentCreateView,
    TrainingBudgetListView, TrainingBudgetDetailView,
)


class TrainingOverviewView(APIView):
    """Returns available training sub-endpoints."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'module': 'training',
            'endpoints': [
                'needs/', 'courses/', 'sessions/',
                'enrollments/', 'budgets/',
            ]
        })


urlpatterns = [
    path('', TrainingOverviewView.as_view(), name='training-overview'),
    path('needs/', TrainingNeedListView.as_view(), name='training-need-list'),
    path('needs/create/', TrainingNeedCreateView.as_view(), name='training-need-create'),
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('sessions/', TrainingSessionListView.as_view(), name='session-list'),
    path('sessions/create/', TrainingSessionCreateView.as_view(), name='session-create'),
    path('enrollments/', TrainingEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/create/', TrainingEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('budgets/', TrainingBudgetListView.as_view(), name='budget-list'),
    path('budgets/<int:pk>/', TrainingBudgetDetailView.as_view(), name='budget-detail'),
]
