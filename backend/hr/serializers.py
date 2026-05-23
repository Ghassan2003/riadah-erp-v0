"""
Serializers for the HR module - Phase 5.
Handles Department, Employee, Attendance, LeaveRequest, Holiday Calendar,
Employment History, and Payslip data transformation.
"""

from rest_framework import serializers
from .models import (
    Department, Employee, Attendance, LeaveRequest,
    LeaveBalance, PerformanceReview, Shift, EmployeeShift,
    HolidayCalendar, Holiday, EmploymentHistory, Payslip,
)


# =============================================
# Department Serializers
# =============================================

class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing departments."""

    employees_count = serializers.IntegerField(read_only=True, default=0)
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Department
        fields = (
            'id', 'name', 'name_en', 'description',
            'manager', 'manager_name', 'employees_count',
            'is_active', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class DepartmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a department."""

    class Meta:
        model = Department
        fields = ('name', 'name_en', 'description', 'manager')

    def validate_name(self, value):
        if Department.objects.filter(name=value).exists():
            raise serializers.ValidationError('اسم القسم موجود مسبقاً')
        return value


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating department info."""

    class Meta:
        model = Department
        fields = ('name', 'name_en', 'description', 'manager', 'is_active')


class DepartmentDetailSerializer(DepartmentListSerializer):
    """Detailed department serializer with employees list."""

    employees = serializers.SerializerMethodField()
    children_count = serializers.IntegerField(read_only=True, default=0)
    parent_name = serializers.CharField(source='parent.name', read_only=True, default=None)

    class Meta(DepartmentListSerializer.Meta):
        fields = DepartmentListSerializer.Meta.fields + (
            'parent', 'parent_name', 'children_count', 'employees', 'updated_at',
        )

    def get_employees(self, obj):
        emps = obj.employees.filter(is_active=True)[:20]
        return EmployeeListSerializer(emps, many=True).data


# =============================================
# Employee Serializers
# =============================================

class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing employees."""

    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_name = serializers.CharField(read_only=True)
    total_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Employee
        fields = (
            'id', 'employee_number', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'department', 'department_name',
            'position', 'hire_date', 'status', 'status_display',
            'salary', 'total_salary', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'employee_number', 'full_name', 'total_salary', 'created_at')


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new employee."""

    class Meta:
        model = Employee
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'gender',
            'department', 'position', 'hire_date', 'salary',
            'housing_allowance', 'transport_allowance',
            'bank_name', 'bank_account', 'national_id', 'notes',
        )

    def validate_email(self, value):
        if value and Employee.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError('البريد الإلكتروني مستخدم مسبقاً')
        return value


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee info."""

    class Meta:
        model = Employee
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'gender',
            'department', 'position', 'salary', 'housing_allowance',
            'transport_allowance', 'status', 'is_active',
            'bank_name', 'bank_account', 'national_id', 'notes',
        )


class EmployeeDetailSerializer(EmployeeListSerializer):
    """Detailed employee serializer with all info."""

    department_info = DepartmentListSerializer(source='department', read_only=True)
    pending_leaves = serializers.IntegerField(read_only=True, default=0)

    class Meta(EmployeeListSerializer.Meta):
        fields = EmployeeListSerializer.Meta.fields + (
            'gender', 'housing_allowance', 'transport_allowance',
            'bank_name', 'bank_account', 'national_id', 'notes',
            'updated_at', 'department_info', 'pending_leaves',
        )


# =============================================
# Attendance Serializers
# =============================================

class AttendanceListSerializer(serializers.ModelSerializer):
    """Serializer for listing attendance records."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    hours_worked = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'date', 'check_in', 'check_out',
            'status', 'status_display', 'hours_worked', 'notes',
        )
        read_only_fields = ('id', 'employee_name', 'employee_number', 'department_name', 'hours_worked')


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for recording attendance."""

    class Meta:
        model = Attendance
        fields = ('employee', 'date', 'check_in', 'check_out', 'status', 'notes')

    def validate(self, attrs):
        # Check for duplicate record
        if Attendance.objects.filter(
            employee=attrs['employee'],
            date=attrs['date']
        ).exists():
            raise serializers.ValidationError('يوجد سجل حضور لهذا الموظف في هذا التاريخ')
        return attrs


class AttendanceBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk attendance creation."""

    records = AttendanceCreateSerializer(many=True)


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating attendance records."""

    class Meta:
        model = Attendance
        fields = ('check_in', 'check_out', 'status', 'notes')


# =============================================
# Leave Request Serializers
# =============================================

class LeaveRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing leave requests."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = LeaveRequest
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'leave_type', 'leave_type_display',
            'start_date', 'end_date', 'days', 'reason',
            'approval_status', 'approval_status_display',
            'approved_by', 'approved_by_name', 'approved_at',
            'created_at',
        )
        read_only_fields = ('id', 'days', 'created_at')


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a leave request."""

    class Meta:
        model = LeaveRequest
        fields = ('employee', 'leave_type', 'start_date', 'end_date', 'reason')

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
        # Check for overlapping leave
        overlapping = LeaveRequest.objects.filter(
            employee=attrs['employee'],
            start_date__lte=attrs['end_date'],
            end_date__gte=attrs['start_date'],
            approval_status__in=('pending', 'approved'),
        )
        if overlapping.exists():
            raise serializers.ValidationError('يوجد إجازة متداخلة في نفس الفترة')
        return attrs


class LeaveRequestApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting leave requests."""

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
# Department Tree Serializer (Org Chart)
# =============================================

class DepartmentTreeSerializer(serializers.ModelSerializer):
    """Recursive serializer for department hierarchy / org chart."""

    children = serializers.SerializerMethodField()
    employees_count = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Department
        fields = (
            'id', 'name', 'name_en', 'manager', 'manager_name',
            'employees_count', 'is_active', 'children',
        )

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return DepartmentTreeSerializer(children, many=True).data

    def get_employees_count(self, obj):
        return obj.employees.filter(is_active=True).count()


# =============================================
# Leave Balance Serializers
# =============================================

class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for leave balances."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)

    class Meta:
        model = LeaveBalance
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'leave_type', 'leave_type_display', 'year',
            'total_days', 'used_days', 'remaining_days', 'carried_over',
        )
        read_only_fields = ('id', 'employee_name', 'employee_number', 'leave_type_display')


class LeaveBalanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave balances."""

    class Meta:
        model = LeaveBalance
        fields = (
            'employee', 'leave_type', 'year',
            'total_days', 'used_days', 'remaining_days', 'carried_over',
        )

    def validate(self, attrs):
        qs = LeaveBalance.objects.filter(
            employee=attrs['employee'],
            leave_type=attrs['leave_type'],
            year=attrs['year'],
        )
        if qs.exists():
            raise serializers.ValidationError('يوجد رصيد إجازات لهذا الموظف ونوع الإجازة والسنة مسبقاً')
        return attrs


# =============================================
# Performance Review Serializers
# =============================================

class PerformanceReviewSerializer(serializers.ModelSerializer):
    """Serializer for performance reviews."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, default=None)
    review_period_display = serializers.CharField(source='get_review_period_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PerformanceReview
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'reviewer', 'reviewer_name', 'review_period', 'review_period_display',
            'year', 'quarter', 'start_date', 'end_date',
            'goals_rating', 'competencies_rating', 'teamwork_rating',
            'communication_rating', 'initiative_rating', 'overall_rating',
            'strengths', 'areas_for_improvement', 'goals_for_next_period',
            'comments', 'status', 'status_display',
            'completed_at', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'overall_rating', 'employee_name', 'employee_number',
                            'reviewer_name', 'review_period_display', 'status_display',
                            'created_at', 'updated_at')


class PerformanceReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating performance reviews."""

    class Meta:
        model = PerformanceReview
        fields = (
            'employee', 'reviewer', 'review_period', 'year', 'quarter',
            'start_date', 'end_date',
            'goals_rating', 'competencies_rating', 'teamwork_rating',
            'communication_rating', 'initiative_rating',
            'strengths', 'areas_for_improvement', 'goals_for_next_period',
            'comments', 'status',
        )

    def validate(self, attrs):
        # Validate quarter for quarterly reviews
        if attrs.get('review_period') == 'quarterly' and not attrs.get('quarter'):
            raise serializers.ValidationError('التقييم الربعي يتطلب تحديد الربع')
        if attrs.get('quarter') and not (1 <= attrs['quarter'] <= 4):
            raise serializers.ValidationError('الربع يجب أن يكون بين 1 و 4')
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] > attrs['end_date']:
                raise serializers.ValidationError('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
        # Check for duplicate review
        qs = PerformanceReview.objects.filter(
            employee=attrs['employee'],
            review_period=attrs['review_period'],
            year=attrs['year'],
            quarter=attrs.get('quarter'),
        )
        if qs.exists():
            raise serializers.ValidationError('يوجد تقييم أداء لهذا الموظف في نفس الفترة مسبقاً')
        return attrs


class PerformanceReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating performance reviews."""

    class Meta:
        model = PerformanceReview
        fields = (
            'reviewer', 'goals_rating', 'competencies_rating', 'teamwork_rating',
            'communication_rating', 'initiative_rating',
            'strengths', 'areas_for_improvement', 'goals_for_next_period',
            'comments', 'status',
        )

    def validate(self, attrs):
        if attrs.get('quarter') and not (1 <= attrs['quarter'] <= 4):
            raise serializers.ValidationError('الربع يجب أن يكون بين 1 و 4')
        return attrs


# =============================================
# Shift Serializers
# =============================================

class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for shifts."""

    total_hours = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Shift
        fields = (
            'id', 'name', 'name_en', 'start_time', 'end_time',
            'break_duration', 'is_night', 'applicable_days',
            'is_active', 'total_hours', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'total_hours', 'created_at', 'updated_at')


class ShiftCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating shifts."""

    class Meta:
        model = Shift
        fields = (
            'name', 'name_en', 'start_time', 'end_time',
            'break_duration', 'is_night', 'applicable_days', 'is_active',
        )


# =============================================
# Employee Shift Serializers
# =============================================

class EmployeeShiftSerializer(serializers.ModelSerializer):
    """Serializer for employee shift assignments."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)
    shift_details = ShiftSerializer(source='shift', read_only=True)

    class Meta:
        model = EmployeeShift
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'shift', 'shift_name', 'shift_details',
            'effective_date', 'end_date', 'is_active', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'employee_name', 'employee_number',
                            'shift_name', 'shift_details', 'created_at')


class EmployeeShiftCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employee shift assignments."""

    class Meta:
        model = EmployeeShift
        fields = (
            'employee', 'shift', 'effective_date', 'end_date', 'is_active', 'notes',
        )

    def validate(self, attrs):
        if attrs.get('end_date') and attrs.get('effective_date'):
            if attrs['end_date'] < attrs['effective_date']:
                raise serializers.ValidationError('تاريخ الانتهاء يجب أن يكون بعد تاريخ السريان')
        return attrs


# =============================================
# HR Stats Serializer
# =============================================

class HRStatsSerializer(serializers.Serializer):
    """Serializer for HR dashboard statistics."""

    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    on_leave_employees = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    total_salary_expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_leaves = serializers.IntegerField()
    today_attendance = serializers.IntegerField()
    today_absent = serializers.IntegerField()


# =============================================
# Holiday Calendar Serializers
# =============================================

class HolidayCalendarListSerializer(serializers.ModelSerializer):
    """Serializer for listing holiday calendars."""

    holidays_count = serializers.SerializerMethodField()

    class Meta:
        model = HolidayCalendar
        fields = ('id', 'name', 'year', 'is_active', 'holidays_count',)
        read_only_fields = ('id', 'holidays_count')

    def get_holidays_count(self, obj):
        return obj.holidays.count()


class HolidayCalendarCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a holiday calendar."""

    class Meta:
        model = HolidayCalendar
        fields = ('name', 'year', 'is_active')


class HolidayCalendarDetailSerializer(HolidayCalendarListSerializer):
    """Detailed serializer for holiday calendar with holidays list."""

    holidays = serializers.SerializerMethodField()

    class Meta(HolidayCalendarListSerializer.Meta):
        fields = HolidayCalendarListSerializer.Meta.fields + ('holidays',)

    def get_holidays(self, obj):
        return HolidayListSerializer(obj.holidays.all(), many=True).data


class HolidaySerializer(serializers.ModelSerializer):
    """Serializer for holidays."""

    holiday_type_display = serializers.CharField(source='get_holiday_type_display', read_only=True)

    class Meta:
        model = Holiday
        fields = (
            'id', 'calendar', 'name', 'name_en', 'date',
            'holiday_type', 'holiday_type_display', 'is_recurring',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'holiday_type_display', 'created_at')


class HolidayListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing holidays."""

    holiday_type_display = serializers.CharField(source='get_holiday_type_display', read_only=True)

    class Meta:
        model = Holiday
        fields = (
            'id', 'name', 'name_en', 'date',
            'holiday_type', 'holiday_type_display', 'is_recurring',
        )


class HolidayCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a single holiday."""

    class Meta:
        model = Holiday
        fields = (
            'calendar', 'name', 'name_en', 'date',
            'holiday_type', 'is_recurring', 'notes',
        )

    def validate(self, attrs):
        if Holiday.objects.filter(calendar=attrs['calendar'], date=attrs['date']).exists():
            raise serializers.ValidationError('يوجد إجازة في هذا التاريخ داخل هذا التقويم مسبقاً')
        return attrs


class HolidayBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk holiday creation."""

    calendar = serializers.PrimaryKeyRelatedField(queryset=HolidayCalendar.objects.all())
    holidays = HolidayCreateSerializer(many=True)

    def validate(self, attrs):
        calendar = attrs['calendar']
        dates = [h['date'] for h in attrs['holidays']]
        if len(dates) != len(set(dates)):
            raise serializers.ValidationError('يوجد تواريخ مكررة في قائمة الإجازات')
        return attrs


class YearCalendarSerializer(serializers.Serializer):
    """Serializer for year calendar response."""

    calendar = HolidayCalendarDetailSerializer()
    month = serializers.IntegerField(required=False, default=None)
    holidays = HolidayListSerializer(many=True)
    total_holidays = serializers.IntegerField()


# =============================================
# Employment History Serializers
# =============================================

class EmploymentHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing employment history."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = EmploymentHistory
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'action_type', 'action_type_display',
            'department', 'department_name', 'position', 'salary',
            'effective_date', 'previous_department', 'previous_position',
            'previous_salary', 'reason', 'created_by', 'created_by_name',
            'created_at',
        )
        read_only_fields = (
            'id', 'employee_name', 'employee_number', 'action_type_display',
            'department_name', 'created_by_name', 'created_at',
        )


class EmploymentHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating employment history entries."""

    class Meta:
        model = EmploymentHistory
        fields = (
            'employee', 'action_type', 'department', 'position', 'salary',
            'effective_date', 'previous_department', 'previous_position',
            'previous_salary', 'reason',
        )


# =============================================
# Employee Full History Serializers
# =============================================

class EmployeeAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary in employee full history."""

    total_present = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    total_late = serializers.IntegerField()
    total_half_day = serializers.IntegerField()
    total_holidays = serializers.IntegerField()


class EmployeeSalaryHistorySerializer(serializers.Serializer):
    """Serializer for salary change history."""

    date = serializers.DateField()
    previous_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    new_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.CharField()


class EmployeeFullHistorySerializer(serializers.Serializer):
    """Comprehensive employee history serializer."""

    employee = EmployeeDetailSerializer()
    employment_history = EmploymentHistoryListSerializer(many=True)
    leave_requests = LeaveRequestListSerializer(many=True)
    attendance_summary = EmployeeAttendanceSummarySerializer()
    performance_reviews = PerformanceReviewSerializer(many=True)
    salary_changes = serializers.ListField(child=serializers.DictField())


# =============================================
# Payslip Serializers
# =============================================

class PayslipListSerializer(serializers.ModelSerializer):
    """Serializer for listing payslips."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True, default=None)
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    net_pay = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = Payslip
        fields = (
            'id', 'employee', 'employee_name', 'employee_number', 'department_name',
            'month', 'year', 'status', 'status_display',
            'basic_salary', 'housing_allowance', 'transport_allowance',
            'overtime_pay', 'bonuses',
            'deductions', 'insurance_deduction', 'tax_deduction',
            'loan_deduction', 'advance_deduction', 'other_deduction',
            'total_earnings', 'total_deductions', 'net_pay',
            'approved_by', 'approved_by_name', 'approved_at',
            'payment_date', 'payment_method', 'payment_method_display',
            'notes', 'generated_at', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'total_earnings', 'total_deductions', 'net_pay',
            'employee_name', 'employee_number', 'department_name',
            'status_display', 'payment_method_display',
            'approved_by_name', 'generated_at', 'created_at', 'updated_at',
        )


class PayslipDetailSerializer(PayslipListSerializer):
    """Detailed payslip serializer with all fields."""
    pass


class PayslipUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payslip details."""

    class Meta:
        model = Payslip
        fields = (
            'basic_salary', 'housing_allowance', 'transport_allowance',
            'overtime_pay', 'bonuses',
            'deductions', 'insurance_deduction', 'tax_deduction',
            'loan_deduction', 'advance_deduction', 'other_deduction',
            'notes',
        )


class PayslipApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting payslips."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class PayslipGenerateSerializer(serializers.Serializer):
    """Serializer for bulk payslip generation."""

    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2000)
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=None,
        help_text='قائمة معرفات الموظفين (اختياري، إذا لم يتم تحديدها يتم توليد الكل)',
    )


class PayslipStatsSerializer(serializers.Serializer):
    """Serializer for payslip/payroll summary statistics."""

    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_deductions = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_net_pay = serializers.DecimalField(max_digits=14, decimal_places=2)
    approved_count = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()

