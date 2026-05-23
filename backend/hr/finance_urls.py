from django.urls import path
from .enhanced_views import (
    LoanListView, LoanCreateView, LoanDetailView,
    LoanPaymentListView,
    SalaryAdvanceListView, SalaryAdvanceCreateView,
    OvertimeRequestListView, OvertimeRequestCreateView,
    OvertimeApproveView,
)

urlpatterns = [
    path('loans/', LoanListView.as_view(), name='loan-list'),
    path('loans/create/', LoanCreateView.as_view(), name='loan-create'),
    path('loans/<int:pk>/', LoanDetailView.as_view(), name='loan-detail'),
    path('loan-payments/', LoanPaymentListView.as_view(), name='loan-payment-list'),
    path('salary-advances/', SalaryAdvanceListView.as_view(), name='salary-advance-list'),
    path('salary-advances/create/', SalaryAdvanceCreateView.as_view(), name='salary-advance-create'),
    path('overtime/', OvertimeRequestListView.as_view(), name='overtime-list'),
    path('overtime/create/', OvertimeRequestCreateView.as_view(), name='overtime-create'),
    path('overtime/<int:pk>/approve/', OvertimeApproveView.as_view(), name='overtime-approve'),
]
