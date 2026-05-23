"""
URL patterns for the HR module - Phase 5.
Enhanced with Recruitment, Qualifications, Training, Finances, Benefits, Reports, Org Chart.
"""

from django.urls import path, include
from .views import (
    # Existing views
    DepartmentListView,
    DepartmentDetailView,
    DepartmentDeleteView,
    DepartmentRestoreView,
    DepartmentTreeView,
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
    LeaveBalanceListView,
    LeaveBalanceInitializeView,
    PerformanceReviewListView,
    PerformanceReviewCreateView,
    PerformanceReviewDetailView,
    ShiftListView,
    ShiftDetailView,
    EmployeeShiftListView,
    EmployeeShiftDetailView,
    HRStatsView,
    EmployeeExportView,
    AttendanceExportView,
    LeaveExportView,
    # New Holiday Calendar views
    HolidayCalendarListView,
    HolidayCalendarDetailView,
    HolidayListView,
    HolidayCreateView,
    HolidayBulkCreateView,
    HolidayDetailView,
    HolidayDeleteView,
    YearCalendarView,
    # New Employment History views
    EmploymentHistoryListView,
    EmploymentHistoryCreateView,
    EmployeeFullHistoryView,
    # New Payslip views
    PayslipListView,
    PayslipDetailView,
    PayslipGenerateView,
    PayslipApproveView,
    PayslipStatsView,
)

urlpatterns = [
    # HR statistics
    path('stats/', HRStatsView.as_view(), name='hr-stats'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/tree/', DepartmentTreeView.as_view(), name='department-tree'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department-delete'),
    path('departments/<int:pk>/restore/', DepartmentRestoreView.as_view(), name='department-restore'),

    # Employees
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
    path('employees/<int:pk>/restore/', EmployeeRestoreView.as_view(), name='employee-restore'),
    path('employees/<int:pk>/full-history/', EmployeeFullHistoryView.as_view(), name='employee-full-history'),

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

    # Leave Balances
    path('leave-balances/', LeaveBalanceListView.as_view(), name='leave-balance-list'),
    path('leave-balances/initialize/', LeaveBalanceInitializeView.as_view(), name='leave-balance-initialize'),

    # Performance Reviews
    path('performance-reviews/', PerformanceReviewListView.as_view(), name='performance-review-list'),
    path('performance-reviews/create/', PerformanceReviewCreateView.as_view(), name='performance-review-create'),
    path('performance-reviews/<int:pk>/', PerformanceReviewDetailView.as_view(), name='performance-review-detail'),

    # Shifts
    path('shifts/', ShiftListView.as_view(), name='shift-list'),
    path('shifts/<int:pk>/', ShiftDetailView.as_view(), name='shift-detail'),

    # Employee Shifts
    path('employee-shifts/', EmployeeShiftListView.as_view(), name='employee-shift-list'),
    path('employee-shifts/<int:pk>/', EmployeeShiftDetailView.as_view(), name='employee-shift-detail'),

    # Holiday Calendar
    path('holiday-calendars/', HolidayCalendarListView.as_view(), name='holiday-calendar-list'),
    path('holiday-calendars/<int:pk>/', HolidayCalendarDetailView.as_view(), name='holiday-calendar-detail'),
    path('holidays/', HolidayListView.as_view(), name='holiday-list'),
    path('holidays/create/', HolidayCreateView.as_view(), name='holiday-create'),
    path('holidays/bulk-create/', HolidayBulkCreateView.as_view(), name='holiday-bulk-create'),
    path('holidays/<int:pk>/', HolidayDetailView.as_view(), name='holiday-detail'),
    path('holidays/<int:pk>/delete/', HolidayDeleteView.as_view(), name='holiday-delete'),
    path('holidays/year-calendar/', YearCalendarView.as_view(), name='holiday-year-calendar'),

    # Employment History
    path('employment-history/', EmploymentHistoryListView.as_view(), name='employment-history-list'),
    path('employment-history/create/', EmploymentHistoryCreateView.as_view(), name='employment-history-create'),

    # Payslips
    path('payslips/', PayslipListView.as_view(), name='payslip-list'),
    path('payslips/generate/', PayslipGenerateView.as_view(), name='payslip-generate'),
    path('payslips/stats/', PayslipStatsView.as_view(), name='payslip-stats'),
    path('payslips/<int:pk>/', PayslipDetailView.as_view(), name='payslip-detail'),
    path('payslips/<int:pk>/approve/', PayslipApproveView.as_view(), name='payslip-approve'),

    # Excel Export
    path('employees/export/', EmployeeExportView.as_view(), name='employee-export'),
    path('attendance/export/', AttendanceExportView.as_view(), name='attendance-export'),
    path('leaves/export/', LeaveExportView.as_view(), name='leave-export'),

    # Enhanced HR Modules
    path('recruitment/', include('hr.recruitment_urls')),
    path('qualifications/', include('hr.qualification_urls')),
    path('documents/', include('hr.document_urls')),
    path('training/', include('hr.training_urls')),
    path('finances/', include('hr.finance_urls')),
    path('benefits/', include('hr.benefit_urls')),
    path('reports/', include('hr.report_urls')),
    path('org-chart/', include('hr.orgchart_urls')),
]
