"""
Admin configuration for the HR module.
"""

from django.contrib import admin
from .models import Department, Employee, Attendance, LeaveRequest


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


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'full_name', 'department', 'position', 'status', 'total_salary')
    list_filter = ('department', 'status', 'gender')
    search_fields = ('first_name', 'last_name', 'employee_number', 'email')
    inlines = [LeaveRequestInline]


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
