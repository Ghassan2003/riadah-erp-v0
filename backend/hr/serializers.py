"""
Serializers for the HR module - Phase 5.
Handles Department, Employee, Attendance, and LeaveRequest data transformation.
"""

from rest_framework import serializers
from .models import Department, Employee, Attendance, LeaveRequest


# =============================================
# Department Serializers
# =============================================

class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing departments."""

    employees_count = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Department
        fields = (
            'id', 'name', 'name_en', 'description',
            'manager', 'manager_name', 'employees_count',
            'is_active', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_employees_count(self, obj):
        return obj.employees.filter(is_active=True).count()


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

    class Meta(DepartmentListSerializer.Meta):
        fields = DepartmentListSerializer.Meta.fields + ('employees', 'updated_at')

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
    pending_leaves = serializers.SerializerMethodField()

    class Meta(EmployeeListSerializer.Meta):
        fields = EmployeeListSerializer.Meta.fields + (
            'gender', 'housing_allowance', 'transport_allowance',
            'bank_name', 'bank_account', 'national_id', 'notes',
            'updated_at', 'department_info', 'pending_leaves',
        )

    def get_pending_leaves(self, obj):
        return obj.leave_requests.filter(approval_status='pending').count()


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
