from django.urls import path
from .enhanced_views import (
    HealthInsuranceListView, HealthInsuranceDetailView,
    EmployeeInsuranceListView, EmployeeInsuranceCreateView,
    DisciplinaryActionListView, DisciplinaryActionCreateView,
    GrievanceListView, GrievanceCreateView, GrievanceDetailView,
    OffboardingListView, OffboardingCreateView,
)

urlpatterns = [
    path('health-insurance/', HealthInsuranceListView.as_view(), name='health-insurance-list'),
    path('health-insurance/<int:pk>/', HealthInsuranceDetailView.as_view(), name='health-insurance-detail'),
    path('employee-insurance/', EmployeeInsuranceListView.as_view(), name='employee-insurance-list'),
    path('employee-insurance/create/', EmployeeInsuranceCreateView.as_view(), name='employee-insurance-create'),
    path('disciplinary/', DisciplinaryActionListView.as_view(), name='disciplinary-list'),
    path('disciplinary/create/', DisciplinaryActionCreateView.as_view(), name='disciplinary-create'),
    path('grievances/', GrievanceListView.as_view(), name='grievance-list'),
    path('grievances/create/', GrievanceCreateView.as_view(), name='grievance-create'),
    path('grievances/<int:pk>/', GrievanceDetailView.as_view(), name='grievance-detail'),
    path('offboarding/', OffboardingListView.as_view(), name='offboarding-list'),
    path('offboarding/create/', OffboardingCreateView.as_view(), name='offboarding-create'),
]
