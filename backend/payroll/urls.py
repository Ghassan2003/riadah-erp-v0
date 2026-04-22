"""
URL patterns for the Payroll module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Payroll statistics
    path('stats/', views.PayrollStatsView.as_view(), name='payroll-stats'),

    # Payroll Periods
    path('periods/', views.PayrollPeriodListView.as_view(), name='payroll-periods'),
    path('periods/<int:pk>/', views.PayrollPeriodDetailView.as_view(), name='payroll-period-detail'),
    path('periods/<int:pk>/delete/', views.PayrollPeriodDeleteView.as_view(), name='payroll-period-delete'),
    path('periods/<int:pk>/generate/', views.PayrollGenerateView.as_view(), name='payroll-generate'),
    path('periods/<int:pk>/close/', views.PayrollCloseView.as_view(), name='payroll-close'),

    # Payroll Records
    path('records/', views.PayrollRecordListView.as_view(), name='payroll-records'),
    path('records/<int:pk>/', views.PayrollRecordDetailView.as_view(), name='payroll-record-detail'),
    path('records/<int:pk>/update/', views.PayrollRecordUpdateView.as_view(), name='payroll-record-update'),
    path('records/<int:pk>/pay/', views.PayrollPayRecordView.as_view(), name='payroll-record-pay'),

    # Salary Advances
    path('advances/', views.SalaryAdvanceListView.as_view(), name='salary-advances'),
    path('advances/<int:pk>/', views.SalaryAdvanceDetailView.as_view(), name='salary-advance-detail'),
    path('advances/<int:pk>/delete/', views.SalaryAdvanceDeleteView.as_view(), name='salary-advance-delete'),
    path('advances/<int:pk>/approve/', views.SalaryAdvanceApproveView.as_view(), name='salary-advance-approve'),

    # Employee Loans
    path('loans/', views.EmployeeLoanListView.as_view(), name='employee-loans'),
    path('loans/<int:pk>/', views.EmployeeLoanDetailView.as_view(), name='employee-loan-detail'),
    path('loans/<int:pk>/delete/', views.EmployeeLoanDeleteView.as_view(), name='employee-loan-delete'),
    path('loans/<int:pk>/approve/', views.EmployeeLoanApproveView.as_view(), name='employee-loan-approve'),

    # End of Service
    path('end-of-service/', views.EndOfServiceListView.as_view(), name='end-of-service'),
    path('end-of-service/<int:pk>/', views.EndOfServiceDetailView.as_view(), name='end-of-service-detail'),
    path('end-of-service/<int:pk>/delete/', views.EndOfServiceDeleteView.as_view(), name='end-of-service-delete'),

    # Export
    path('export/', views.PayrollExportView.as_view(), name='payroll-export'),
]
