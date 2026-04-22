"""
Serializers for the Payroll module.
Handles PayrollPeriod, PayrollRecord, SalaryAdvance, EmployeeLoan, and EndOfServiceBenefit
data transformation.
"""

from rest_framework import serializers
from .models import (
    PayrollPeriod,
    PayrollRecord,
    SalaryAdvance,
    EmployeeLoan,
    EndOfServiceBenefit,
)


# =============================================
# Payroll Period Serializers
# =============================================

class PayrollPeriodListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payroll periods."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = PayrollPeriod
        fields = (
            'id', 'name', 'month', 'year', 'start_date', 'end_date',
            'status', 'status_display', 'total_employees', 'total_salaries',
            'total_deductions', 'total_net', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class PayrollPeriodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payroll period."""

    class Meta:
        model = PayrollPeriod
        fields = ('name', 'month', 'year', 'start_date', 'end_date')

    def validate(self, attrs):
        if PayrollPeriod.objects.filter(month=attrs['month'], year=attrs['year']).exists():
            raise serializers.ValidationError('توجد فترة رواتب لهذا الشهر والسنة مسبقاً')
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class PayrollPeriodUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payroll period."""

    class Meta:
        model = PayrollPeriod
        fields = ('name', 'start_date', 'end_date', 'status')

    def validate(self, attrs):
        if 'start_date' in attrs and 'end_date' in attrs:
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class PayrollPeriodDetailSerializer(PayrollPeriodListSerializer):
    """Detailed payroll period serializer with records count."""

    records_count = serializers.SerializerMethodField()

    class Meta(PayrollPeriodListSerializer.Meta):
        fields = PayrollPeriodListSerializer.Meta.fields + ('records_count',)

    def get_records_count(self, obj):
        return obj.records.count()


# =============================================
# Payroll Record Serializers
# =============================================

class PayrollRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payroll records."""

    employee_name = serializers.SerializerMethodField()
    employee_number = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    period_name = serializers.CharField(source='period.name', read_only=True)
    status_display = serializers.CharField(source='period.get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = PayrollRecord
        fields = (
            'id', 'period', 'period_name', 'employee', 'employee_name',
            'employee_number', 'department_name', 'basic_salary',
            'housing_allowance', 'transport_allowance', 'food_allowance',
            'overtime_hours', 'overtime_amount', 'bonus', 'commission',
            'deductions_gosi', 'deductions_tax', 'deductions_absence',
            'deductions_loan', 'deductions_other', 'total_earnings',
            'total_deductions_amount', 'net_salary', 'payment_method',
            'payment_method_display', 'payment_status', 'payment_status_display',
            'payment_date', 'bank_reference', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_employee_name(self, obj):
        return obj.employee.full_name if obj.employee else ''

    def get_employee_number(self, obj):
        return obj.employee.employee_number if obj.employee else ''

    def get_department_name(self, obj):
        if obj.employee and obj.employee.department:
            return obj.employee.department.name
        return ''


class PayrollRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payroll record."""

    class Meta:
        model = PayrollRecord
        fields = (
            'period', 'employee', 'basic_salary', 'housing_allowance',
            'transport_allowance', 'food_allowance', 'overtime_hours',
            'overtime_amount', 'bonus', 'commission', 'deductions_gosi',
            'deductions_tax', 'deductions_absence', 'deductions_loan',
            'deductions_other', 'deductions_other_description',
            'payment_method', 'payment_status', 'payment_date',
            'bank_reference', 'notes',
        )

    def validate(self, attrs):
        # Check for duplicate record
        if PayrollRecord.objects.filter(
            period=attrs['period'],
            employee=attrs['employee'],
        ).exists():
            raise serializers.ValidationError('يوجد سجل راتب لهذا الموظف في هذه الفترة مسبقاً')
        # Ensure period is in processing status
        if attrs['period'].status not in ('draft', 'processing'):
            raise serializers.ValidationError(
                'لا يمكن إضافة سجلات رواتب لفترة ليست في حالة مسودة أو قيد المعالجة'
            )
        return attrs


class PayrollRecordUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payroll record."""

    class Meta:
        model = PayrollRecord
        fields = (
            'basic_salary', 'housing_allowance', 'transport_allowance',
            'food_allowance', 'overtime_hours', 'overtime_amount',
            'bonus', 'commission', 'deductions_gosi', 'deductions_tax',
            'deductions_absence', 'deductions_loan', 'deductions_other',
            'deductions_other_description', 'payment_method',
            'payment_date', 'bank_reference', 'notes',
        )


# =============================================
# Salary Advance Serializers
# =============================================

class SalaryAdvanceListSerializer(serializers.ModelSerializer):
    """Serializer for listing salary advances."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = SalaryAdvance
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'amount', 'purpose', 'status',
            'status_display', 'approved_by', 'approved_by_name',
            'approved_at', 'monthly_deduction', 'months_remaining',
            'advance_date', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SalaryAdvanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a salary advance."""

    class Meta:
        model = SalaryAdvance
        fields = ('employee', 'amount', 'purpose', 'advance_date', 'notes')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('مبلغ السلفة يجب أن يكون أكبر من صفر')
        return value


class SalaryAdvanceApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting salary advances."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    monthly_deduction = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        help_text='الخصم الشهري (مطلوب عند الموافقة)',
    )
    months = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text='عدد الأشهر للخصم (مطلوب عند الموافقة)',
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Employee Loan Serializers
# =============================================

class EmployeeLoanListSerializer(serializers.ModelSerializer):
    """Serializer for listing employee loans."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = EmployeeLoan
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'amount', 'monthly_installment', 'months',
            'months_remaining', 'purpose', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at',
            'start_date', 'end_date', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class EmployeeLoanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employee loan."""

    class Meta:
        model = EmployeeLoan
        fields = (
            'employee', 'amount', 'monthly_installment', 'months',
            'purpose', 'start_date', 'notes',
        )

    def validate(self, attrs):
        if attrs['amount'] <= 0:
            raise serializers.ValidationError('مبلغ القرض يجب أن يكون أكبر من صفر')
        if attrs['monthly_installment'] <= 0:
            raise serializers.ValidationError('القسط الشهري يجب أن يكون أكبر من صفر')
        if attrs['months'] <= 0:
            raise serializers.ValidationError('عدد الأشهر يجب أن يكون أكبر من صفر')
        return attrs


class EmployeeLoanApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting employee loans."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# End of Service Benefit Serializers
# =============================================

class EndOfServiceBenefitListSerializer(serializers.ModelSerializer):
    """Serializer for listing end of service benefits."""

    employee_name = serializers.SerializerMethodField()
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EndOfServiceBenefit
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'years_of_service', 'total_service_days',
            'last_salary', 'total_benefit', 'deduction_amount',
            'net_benefit', 'calculation_date', 'status', 'status_display',
            'paid_date', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_employee_name(self, obj):
        return obj.employee.full_name if obj.employee else ''


class EndOfServiceBenefitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an end of service benefit."""

    class Meta:
        model = EndOfServiceBenefit
        fields = (
            'employee', 'years_of_service', 'total_service_days',
            'last_salary', 'total_benefit', 'deduction_amount',
            'net_benefit', 'calculation_date', 'notes',
        )

    def validate(self, attrs):
        if attrs['years_of_service'] <= 0:
            raise serializers.ValidationError('سنوات الخدمة يجب أن تكون أكبر من صفر')
        if attrs['total_service_days'] <= 0:
            raise serializers.ValidationError('أيام الخدمة يجب أن تكون أكبر من صفر')
        if attrs['total_benefit'] < 0:
            raise serializers.ValidationError('إجمالي المكافأة يجب أن يكون صفر أو أكبر')
        return attrs


# =============================================
# Payroll Stats Serializer
# =============================================

class PayrollStatsSerializer(serializers.Serializer):
    """Serializer for Payroll dashboard statistics."""

    total_periods = serializers.IntegerField()
    active_periods = serializers.IntegerField()
    current_month_records = serializers.IntegerField()
    total_paid_this_month = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pending_records = serializers.IntegerField()
    active_advances = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    advances_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    loans_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    end_of_service_pending = serializers.IntegerField()
    total_employees = serializers.IntegerField()
