from django.urls import path
from .reports import (
    WorkforceReportView, TurnoverReportView, EmployeeCostReportView,
    LeaveReportView, AttendanceReportView, PerformanceReportView,
)

urlpatterns = [
    path('workforce/', WorkforceReportView.as_view(), name='report-workforce'),
    path('turnover/', TurnoverReportView.as_view(), name='report-turnover'),
    path('employee-cost/', EmployeeCostReportView.as_view(), name='report-employee-cost'),
    path('leaves/', LeaveReportView.as_view(), name='report-leaves'),
    path('attendance/', AttendanceReportView.as_view(), name='report-attendance'),
    path('performance/', PerformanceReportView.as_view(), name='report-performance'),
]
