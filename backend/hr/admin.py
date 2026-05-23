"""
Admin configuration for the HR module.
Enhanced with Holiday Calendar, Employment History, and Payslip admin configs.
"""

from django.contrib import admin
from .models import (
    Department, Employee, Attendance, LeaveRequest, LeaveBalance,
    PerformanceReview, Shift, EmployeeShift,
    HolidayCalendar, Holiday, EmploymentHistory, Payslip,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'employees_count_display', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_en')

    @admin.display(description='عدد الموظفين')
    def employees_count_display(self, obj):
        return obj.employees_count


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ('date', 'check_in', 'check_out', 'status')
    readonly_fields = ('date', 'check_in', 'check_out', 'status')


class LeaveRequestInline(admin.TabularInline):
    model = LeaveRequest
    extra = 0
    fields = ('leave_type', 'start_date', 'end_date', 'days', 'approval_status')
    readonly_fields = ('leave_type', 'start_date', 'end_date', 'days', 'approval_status')


class EmploymentHistoryInline(admin.TabularInline):
    model = EmploymentHistory
    extra = 0
    fields = ('action_type', 'department', 'position', 'salary', 'effective_date')
    readonly_fields = ('action_type', 'department', 'position', 'salary', 'effective_date')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'full_name', 'department', 'position', 'status', 'total_salary')
    list_filter = ('department', 'status', 'gender')
    search_fields = ('first_name', 'last_name', 'employee_number', 'email')
    inlines = [LeaveRequestInline, EmploymentHistoryInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status', 'hours_worked')
    list_filter = ('status', 'date')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days', 'approval_status')
    list_filter = ('leave_type', 'approval_status')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type_display', 'year', 'total_days', 'used_days', 'remaining_days')
    list_filter = ('leave_type', 'year')
    search_fields = ('employee__first_name', 'employee__last_name')

    @admin.display(description='نوع الإجازة')
    def leave_type_display(self, obj):
        return obj.get_leave_type_display()


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'review_period', 'year', 'quarter', 'overall_rating', 'status')
    list_filter = ('review_period', 'year', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'break_duration', 'is_night', 'is_active')
    list_filter = ('is_active', 'is_night')
    search_fields = ('name', 'name_en')


@admin.register(EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'effective_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'shift')
    search_fields = ('employee__first_name', 'employee__last_name')


class HolidayInline(admin.TabularInline):
    model = Holiday
    extra = 0
    fields = ('name', 'date', 'holiday_type', 'is_recurring')
    readonly_fields = ('name', 'date', 'holiday_type', 'is_recurring')


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'is_active', 'holidays_count_display')
    list_filter = ('year', 'is_active')
    search_fields = ('name',)
    inlines = [HolidayInline]

    @admin.display(description='عدد الإجازات')
    def holidays_count_display(self, obj):
        return obj.holidays.count()


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'calendar', 'date', 'holiday_type_display', 'is_recurring')
    list_filter = ('holiday_type', 'is_recurring', 'calendar__year')
    search_fields = ('name', 'name_en')
    list_editable = ('is_recurring',)

    @admin.display(description='نوع الإجازة')
    def holiday_type_display(self, obj):
        return obj.get_holiday_type_display()


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'action_type_display', 'department', 'position', 'salary', 'effective_date')
    list_filter = ('action_type', 'department')
    search_fields = ('employee__first_name', 'employee__last_name', 'position', 'reason')
    date_hierarchy = 'effective_date'

    @admin.display(description='نوع الإجراء')
    def action_type_display(self, obj):
        return obj.get_action_type_display()


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'month', 'year', 'basic_salary', 'net_pay_display',
        'status_display', 'approved_by', 'payment_date',
    )
    list_filter = ('status', 'year', 'month', 'payment_method')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('generated_at', 'created_at', 'updated_at')

    @admin.display(description='صافي الراتب')
    def net_pay_display(self, obj):
        return obj.net_pay

    @admin.display(description='الحالة')
    def status_display(self, obj):
        return obj.get_status_display()
