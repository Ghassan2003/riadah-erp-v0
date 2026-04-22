"""
URL patterns for the HR module - Phase 5.
"""

from django.urls import path
from .views import (
    DepartmentListView,
    DepartmentDetailView,
    DepartmentDeleteView,
    DepartmentRestoreView,
    EmployeeListView,
    EmployeeDetailView,
    EmployeeDeleteView,
    EmployeeRestoreView,
    AttendanceListView,
    AttendanceCreateView,
    AttendanceUpdateView,
    AttendanceDetailView,
    AttendanceDeleteView,
    LeaveRequestListView,
    LeaveRequestCreateView,
    LeaveRequestApproveView,
    LeaveRequestDetailView,
    LeaveRequestDeleteView,
    HRStatsView,
    EmployeeExportView,
    AttendanceExportView,
    LeaveExportView,
)

urlpatterns = [
    # HR statistics
    path('stats/', HRStatsView.as_view(), name='hr-stats'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department-delete'),
    path('departments/<int:pk>/restore/', DepartmentRestoreView.as_view(), name='department-restore'),

    # Employees
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
    path('employees/<int:pk>/restore/', EmployeeRestoreView.as_view(), name='employee-restore'),

    # Attendance
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/create/', AttendanceCreateView.as_view(), name='attendance-create'),
    path('attendance/<int:pk>/update/', AttendanceUpdateView.as_view(), name='attendance-update'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
    path('attendance/<int:pk>/delete/', AttendanceDeleteView.as_view(), name='attendance-delete'),

    # Leave Requests
    path('leaves/', LeaveRequestListView.as_view(), name='leave-list'),
    path('leaves/create/', LeaveRequestCreateView.as_view(), name='leave-create'),
    path('leaves/<int:pk>/approve/', LeaveRequestApproveView.as_view(), name='leave-approve'),
    path('leaves/<int:pk>/', LeaveRequestDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/delete/', LeaveRequestDeleteView.as_view(), name='leave-delete'),

    # Excel Export
    path('employees/export/', EmployeeExportView.as_view(), name='employee-export'),
    path('attendance/export/', AttendanceExportView.as_view(), name='attendance-export'),
    path('leaves/export/', LeaveExportView.as_view(), name='leave-export'),
]
