"""
Admin configuration for the Payroll module.
"""

from django.contrib import admin
from .models import (
    PayrollPeriod,
    PayrollRecord,
    SalaryAdvance,
    EmployeeLoan,
    EndOfServiceBenefit,
)


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'month', 'year', 'status', 'total_employees', 'total_net')
    list_filter = ('status', 'year', 'month')
    search_fields = ('name',)


class PayrollRecordInline(admin.TabularInline):
    model = PayrollRecord
    extra = 0
    fields = ('employee', 'basic_salary', 'total_earnings', 'total_deductions_amount', 'net_salary', 'payment_status')
    readonly_fields = ('employee', 'basic_salary', 'total_earnings', 'total_deductions_amount', 'net_salary', 'payment_status')
    can_delete = False


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'basic_salary', 'total_earnings', 'total_deductions_amount', 'net_salary', 'payment_status', 'payment_date')
    list_filter = ('payment_status', 'payment_method', 'period')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'period__name')


@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'purpose', 'status', 'monthly_deduction', 'months_remaining', 'advance_date')
    list_filter = ('status',)
    search_fields = ('employee__first_name', 'employee__last_name', 'purpose')


@admin.register(EmployeeLoan)
class EmployeeLoanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'monthly_installment', 'months', 'months_remaining', 'purpose', 'status', 'start_date')
    list_filter = ('status',)
    search_fields = ('employee__first_name', 'employee__last_name', 'purpose')


@admin.register(EndOfServiceBenefit)
class EndOfServiceBenefitAdmin(admin.ModelAdmin):
    list_display = ('employee', 'years_of_service', 'total_service_days', 'last_salary', 'total_benefit', 'deduction_amount', 'net_benefit', 'status')
    list_filter = ('status',)
    search_fields = ('employee__first_name', 'employee__last_name')
