"""
API views for the HR module - Phase 5.
Handles Department, Employee, Attendance, Leave management,
Holiday Calendar, Employment History, and Payslips.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import (
    Department, Employee, Attendance, LeaveRequest,
    LeaveBalance, PerformanceReview, Shift, EmployeeShift,
    HolidayCalendar, Holiday, EmploymentHistory, Payslip,
)
from .serializers import (
    DepartmentListSerializer,
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    DepartmentDetailSerializer,
    DepartmentTreeSerializer,
    EmployeeListSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    EmployeeDetailSerializer,
    AttendanceListSerializer,
    AttendanceCreateSerializer,
    AttendanceUpdateSerializer,
    LeaveRequestListSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestApproveSerializer,
    LeaveBalanceSerializer,
    LeaveBalanceCreateSerializer,
    PerformanceReviewSerializer,
    PerformanceReviewCreateSerializer,
    PerformanceReviewUpdateSerializer,
    ShiftSerializer,
    ShiftCreateUpdateSerializer,
    EmployeeShiftSerializer,
    EmployeeShiftCreateUpdateSerializer,
    HRStatsSerializer,
    # Holiday Calendar serializers
    HolidayCalendarListSerializer,
    HolidayCalendarCreateSerializer,
    HolidayCalendarDetailSerializer,
    HolidaySerializer,
    HolidayListSerializer,
    HolidayCreateSerializer,
    HolidayBulkCreateSerializer,
    # Employment History serializers
    EmploymentHistoryListSerializer,
    EmploymentHistoryCreateSerializer,
    EmployeeFullHistorySerializer,
    # Payslip serializers
    PayslipListSerializer,
    PayslipDetailSerializer,
    PayslipUpdateSerializer,
    PayslipApproveSerializer,
    PayslipGenerateSerializer,
    PayslipStatsSerializer,
)
from users.permissions import IsAdmin
from core.decorators import PermissionRequiredMixin


# =============================================
# Department Views
# =============================================

class DepartmentListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List departments. POST: Create department (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DepartmentCreateSerializer
        return DepartmentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Department.objects.prefetch_related('manager').annotate(
            employees_count=Count('employees', filter=Q(employees__is_active=True))
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dept = serializer.save()
        return Response({
            'message': 'تم إنشاء القسم بنجاح',
            'department': DepartmentDetailSerializer(dept).data,
        }, status=status.HTTP_201_CREATED)


class DepartmentDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET: Department details. PATCH: Update department (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DepartmentUpdateSerializer
        return DepartmentDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Department.objects.prefetch_related(
            'manager', 'employees'
        ).annotate(
            children_count=Count('children', filter=Q(children__is_active=True)),
            employees_count=Count('employees', filter=Q(employees__is_active=True))
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        dept = serializer.save()
        return Response({
            'message': 'تم تحديث القسم بنجاح',
            'department': DepartmentDetailSerializer(dept).data,
        })


class DepartmentDeleteView(views.APIView):
    """DELETE: Soft-delete a department (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
        except Department.DoesNotExist:
            return Response(
                {'error': 'القسم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        dept.is_active = False
        dept.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف القسم بنجاح'})


class DepartmentRestoreView(views.APIView):
    """POST: Restore a soft-deleted department (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
        except Department.DoesNotExist:
            return Response(
                {'error': 'القسم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        dept.is_active = True
        dept.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم إعادة تفعيل القسم بنجاح'})


# =============================================
# Employee Views
# =============================================

class EmployeeListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List employees. POST: Create employee (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'employee_number', 'email', 'position']
    ordering_fields = ['first_name', 'employee_number', 'hire_date', 'salary', 'department']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeCreateSerializer
        return EmployeeListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Employee.objects.select_related('department')
        # Filter by department
        dept = self.request.query_params.get('department')
        if dept:
            queryset = queryset.filter(department_id=dept)
        # Filter by status
        emp_status = self.request.query_params.get('status')
        if emp_status:
            queryset = queryset.filter(status=emp_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emp = serializer.save()
        return Response({
            'message': 'تم إضافة الموظف بنجاح',
            'employee': EmployeeDetailSerializer(emp).data,
        }, status=status.HTTP_201_CREATED)


class EmployeeDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET: Employee details. PATCH: Update employee (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return EmployeeUpdateSerializer
        return EmployeeDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Employee.objects.select_related('department').annotate(
            pending_leaves=Count('leave_requests', filter=Q(leave_requests__approval_status='pending'))
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        emp = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات الموظف بنجاح',
            'employee': EmployeeDetailSerializer(emp).data,
        })


class EmployeeDeleteView(views.APIView):
    """DELETE: Soft-delete an employee (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            emp = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'الموظف غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        emp.is_active = False
        emp.status = 'terminated'
        emp.save(update_fields=['is_active', 'status', 'updated_at'])
        return Response({'message': 'تم حذف الموظف بنجاح'})


class EmployeeRestoreView(views.APIView):
    """POST: Restore a soft-deleted employee (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            emp = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'الموظف غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        emp.is_active = True
        emp.status = 'active'
        emp.save(update_fields=['is_active', 'status', 'updated_at'])
        return Response({'message': 'تم إعادة تفعيل الموظف بنجاح'})


# =============================================
# Attendance Views
# =============================================

class AttendanceListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List attendance records with filtering."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = AttendanceListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['date', 'employee__first_name', 'status']
    ordering = ['-date']

    def get_queryset(self):
        queryset = Attendance.objects.select_related('employee__department')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(employee__department_id=department)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        # Filter by status
        att_status = self.request.query_params.get('status')
        if att_status:
            queryset = queryset.filter(status=att_status)
        return queryset


class AttendanceCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Record attendance (admin only)."""

    permission_module = 'hr'
    permission_action = 'create'

    serializer_class = AttendanceCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({
            'message': 'تم تسجيل الحضور بنجاح',
            'attendance': AttendanceListSerializer(record).data,
        }, status=status.HTTP_201_CREATED)


class AttendanceUpdateView(PermissionRequiredMixin, generics.UpdateAPIView):
    """PUT/PATCH: Update an attendance record (admin only)."""

    permission_module = 'hr'
    permission_action = 'edit'

    serializer_class = AttendanceUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Attendance.objects.select_related('employee__department')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({
            'message': 'تم تحديث سجل الحضور بنجاح',
            'attendance': AttendanceListSerializer(record).data,
        })


class AttendanceDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Attendance record detail."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = AttendanceListSerializer

    def get_queryset(self):
        return Attendance.objects.select_related('employee__department')


class AttendanceDeleteView(views.APIView):
    """DELETE: Delete an attendance record (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            record = Attendance.objects.get(pk=pk)
        except Attendance.DoesNotExist:
            return Response({'error': 'سجل الحضور غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        record.delete()
        return Response({'message': 'تم حذف سجل الحضور بنجاح'})


# =============================================
# Leave Request Views
# =============================================

class LeaveRequestListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List leave requests with filtering."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = LeaveRequestListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['start_date', 'approval_status', 'leave_type', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related('employee__department', 'approved_by')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by approval status
        approval_status = self.request.query_params.get('approval_status')
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        # Filter by leave type
        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)
        return queryset


class LeaveRequestCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Create a leave request."""

    permission_module = 'hr'
    permission_action = 'create'

    serializer_class = LeaveRequestCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()
        return Response({
            'message': 'تم إنشاء طلب الإجازة بنجاح',
            'leave': LeaveRequestListSerializer(leave).data,
        }, status=status.HTTP_201_CREATED)


class LeaveRequestApproveView(views.APIView):
    """POST: Approve or reject a leave request (admin only).
    
    CRITICAL: This view handles automatic leave balance deduction on approval
    and restoration on rejection of previously approved requests.
    """

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            leave = LeaveRequest.objects.select_related('employee').get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'طلب الإجازة غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveRequestApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        employee = leave.employee
        year = leave.start_date.year

        # --- APPROVE ---
        if action == 'approve':
            if leave.approval_status not in ('pending',):
                return Response(
                    {'error': 'يمكن الموافقة فقط على الطلبات المعلقة'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For unpaid leave, skip balance check but still approve
            if leave.leave_type == 'unpaid':
                leave.approval_status = 'approved'
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
                leave.save()
                return Response({
                    'message': 'تمت الموافقة على طلب الإجازة بدون راتب',
                    'leave': LeaveRequestListSerializer(leave).data,
                })

            # Get or create leave balance for this employee/type/year
            leave_balance, created = LeaveBalance.objects.get_or_create(
                employee=employee,
                leave_type=leave.leave_type,
                year=year,
                defaults={
                    'total_days': 30,
                    'remaining_days': 30,
                },
            )

            # Validate enough remaining days
            if leave_balance.remaining_days < leave.days:
                return Response(
                    {
                        'error': (
                            f'رصيد الإجازات غير كافٍ. الموظف يمتلك '
                            f'{leave_balance.remaining_days} يوم متبقي فقط، '
                            f'ولكن الطلب يتطلب {leave.days} يوم.'
                        ),
                        'remaining_days': leave_balance.remaining_days,
                        'requested_days': leave.days,
                        'shortage': leave.days - leave_balance.remaining_days,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Deduct from balance within a transaction
            with transaction.atomic():
                # Re-fetch balance with select_for_update to prevent race conditions
                balance = LeaveBalance.objects.select_for_update().get(pk=leave_balance.pk)
                if balance.remaining_days < leave.days:
                    return Response(
                        {
                            'error': (
                                f'رصيد الإجازات غير كافٍ. رصيد آخر تحديث: '
                                f'{balance.remaining_days} يوم متبقي.'
                            ),
                            'remaining_days': balance.remaining_days,
                            'requested_days': leave.days,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                balance.used_days = balance.used_days + leave.days
                balance.remaining_days = balance.remaining_days - leave.days
                balance.save(update_fields=['used_days', 'remaining_days'])

                leave.approval_status = 'approved'
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
                leave.save()

            return Response({
                'message': (
                    f'تمت الموافقة على طلب الإجازة. تم خصم {leave.days} يوم '
                    f'من رصيد {leave.get_leave_type_display()}. '
                    f'المتبقي: {balance.remaining_days} يوم.'
                ),
                'leave': LeaveRequestListSerializer(leave).data,
                'balance': {
                    'used_days': balance.used_days,
                    'remaining_days': balance.remaining_days,
                    'total_days': balance.total_days,
                },
            })

        # --- REJECT ---
        elif action == 'reject':
            if leave.approval_status == 'pending':
                # Simple rejection - no balance changes needed
                leave.approval_status = 'rejected'
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
                leave.save()
                return Response({
                    'message': 'تم رفض طلب الإجازة',
                    'leave': LeaveRequestListSerializer(leave).data,
                })

            elif leave.approval_status == 'approved':
                # CRITICAL: Revert previously approved leave - add days back to balance
                if leave.leave_type == 'unpaid':
                    leave.approval_status = 'rejected'
                    leave.approved_by = request.user
                    leave.approved_at = timezone.now()
                    leave.save()
                    return Response({
                        'message': 'تم إلغاء الموافقة على طلب الإجازة بدون راتب',
                        'leave': LeaveRequestListSerializer(leave).data,
                    })

                year = leave.start_date.year
                try:
                    leave_balance = LeaveBalance.objects.get(
                        employee=employee,
                        leave_type=leave.leave_type,
                        year=year,
                    )
                except LeaveBalance.DoesNotExist:
                    # Balance record not found - reject without restoring
                    leave.approval_status = 'rejected'
                    leave.approved_by = request.user
                    leave.approved_at = timezone.now()
                    leave.save()
                    return Response({
                        'message': 'تم رفض طلب الإجازة (تحذير: لم يتم العثور على سجل الرصيد لإعادة الأيام)',
                        'leave': LeaveRequestListSerializer(leave).data,
                    })

                with transaction.atomic():
                    # Re-fetch balance with select_for_update
                    balance = LeaveBalance.objects.select_for_update().get(pk=leave_balance.pk)

                    # Restore days
                    balance.used_days = max(balance.used_days - leave.days, 0)
                    balance.remaining_days = balance.remaining_days + leave.days
                    # Ensure remaining doesn't exceed total
                    balance.remaining_days = min(balance.remaining_days, balance.total_days)
                    balance.save(update_fields=['used_days', 'remaining_days'])

                    leave.approval_status = 'rejected'
                    leave.approved_by = request.user
                    leave.approved_at = timezone.now()
                    leave.save()

                return Response({
                    'message': (
                        f'تم رفض طلب الإجازة المعتمد. تم إضافة {leave.days} يوم '
                        f'إلى رصيد {leave.get_leave_type_display()}. '
                        f'المتبقي: {balance.remaining_days} يوم.'
                    ),
                    'leave': LeaveRequestListSerializer(leave).data,
                    'balance': {
                        'used_days': balance.used_days,
                        'remaining_days': balance.remaining_days,
                        'total_days': balance.total_days,
                    },
                })

            else:
                return Response(
                    {'error': 'لا يمكن الرفض على طلب سبق رفضه أو إلغاؤه'},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class LeaveRequestDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Leave request detail."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = LeaveRequestListSerializer

    def get_queryset(self):
        return LeaveRequest.objects.select_related('employee__department', 'approved_by')


class LeaveRequestDeleteView(views.APIView):
    """DELETE: Delete a leave request (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            leave = LeaveRequest.objects.select_related('employee').get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'طلب الإجازة غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if leave.approval_status == 'approved':
            return Response({'error': 'لا يمكن حذف إجازة معتمدة'}, status=status.HTTP_400_BAD_REQUEST)
        leave.delete()
        return Response({'message': 'تم حذف طلب الإجازة بنجاح'})


# =============================================
# Department Tree View (Org Chart)
# =============================================

class DepartmentTreeView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: Return hierarchical department tree for org chart."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = DepartmentTreeSerializer

    def get_queryset(self):
        return Department.objects.filter(
            parent__isnull=True, is_active=True
        ).prefetch_related('manager', 'children', 'employees')


# =============================================
# Leave Balance Views
# =============================================

class LeaveBalanceListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List leave balances with optional employee/year filter."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = LeaveBalanceSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['employee__first_name', 'leave_type', 'year', 'remaining_days']
    ordering = ['employee__first_name', 'leave_type']

    def get_queryset(self):
        queryset = LeaveBalance.objects.select_related('employee')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        # Filter by leave type
        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)
        return queryset


class LeaveBalanceInitializeView(views.APIView):
    """POST: Initialize yearly leave balances for all active employees (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        year = request.data.get('year') or timezone.now().year
        total_days = request.data.get('total_days', 30)
        leave_types = [choice[0] for choice in LeaveRequest.LEAVE_TYPE_CHOICES]

        employees = Employee.objects.filter(is_active=True, status='active')
        created_count = 0
        skipped_count = 0

        for emp in employees:
            for lt in leave_types:
                obj, created = LeaveBalance.objects.get_or_create(
                    employee=emp,
                    leave_type=lt,
                    year=year,
                    defaults={
                        'total_days': total_days,
                        'remaining_days': total_days,
                    },
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        return Response({
            'message': f'تم تهيئة أرصدة الإجازات لسنة {year}',
            'year': year,
            'employees_processed': employees.count(),
            'balances_created': created_count,
            'balances_skipped': skipped_count,
        })


# =============================================
# Performance Review Views
# =============================================

class PerformanceReviewListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List performance reviews with filtering."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = PerformanceReviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['year', 'overall_rating', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = PerformanceReview.objects.select_related('employee', 'reviewer')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by status
        review_status = self.request.query_params.get('status')
        if review_status:
            queryset = queryset.filter(status=review_status)
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        # Filter by review period
        review_period = self.request.query_params.get('review_period')
        if review_period:
            queryset = queryset.filter(review_period=review_period)
        return queryset


class PerformanceReviewCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Create a performance review."""

    permission_module = 'hr'
    permission_action = 'create'

    serializer_class = PerformanceReviewCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response({
            'message': 'تم إنشاء تقييم الأداء بنجاح',
            'review': PerformanceReviewSerializer(review).data,
        }, status=status.HTTP_201_CREATED)


class PerformanceReviewDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET: Review detail. PATCH: Update review."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PerformanceReviewUpdateSerializer
        return PerformanceReviewSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return PerformanceReview.objects.select_related('employee', 'reviewer')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        # Auto-set completed_at
        if review.status == 'completed' and not review.completed_at:
            review.completed_at = timezone.now()
            review.save(update_fields=['completed_at'])
        return Response({
            'message': 'تم تحديث تقييم الأداء بنجاح',
            'review': PerformanceReviewSerializer(review).data,
        })


# =============================================
# Shift Views
# =============================================

class ShiftListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List shifts. POST: Create shift (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en']
    ordering_fields = ['name', 'start_time', 'created_at']
    ordering = ['start_time']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShiftCreateUpdateSerializer
        return ShiftSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Shift.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shift = serializer.save()
        return Response({
            'message': 'تم إنشاء الوردية بنجاح',
            'shift': ShiftSerializer(shift).data,
        }, status=status.HTTP_201_CREATED)


class ShiftDetailView(PermissionRequiredMixin, generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE: Shift detail."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit', 'delete': 'delete'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ShiftCreateUpdateSerializer
        return ShiftSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Shift.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        shift = serializer.save()
        return Response({
            'message': 'تم تحديث الوردية بنجاح',
            'shift': ShiftSerializer(shift).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'تم حذف الوردية بنجاح'})


# =============================================
# Employee Shift Views
# =============================================

class EmployeeShiftListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List employee shift assignments. POST: Create assignment (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['employee__first_name', 'effective_date', '-effective_date']
    ordering = ['-effective_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeShiftCreateUpdateSerializer
        return EmployeeShiftSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = EmployeeShift.objects.select_related('employee', 'shift')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by shift
        shift = self.request.query_params.get('shift')
        if shift:
            queryset = queryset.filter(shift_id=shift)
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        return Response({
            'message': 'تم تعيين الوردية بنجاح',
            'assignment': EmployeeShiftSerializer(assignment).data,
        }, status=status.HTTP_201_CREATED)


class EmployeeShiftDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET/PATCH: Employee shift assignment detail."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return EmployeeShiftCreateUpdateSerializer
        return EmployeeShiftSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return EmployeeShift.objects.select_related('employee', 'shift')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        return Response({
            'message': 'تم تحديث تعيين الوردية بنجاح',
            'assignment': EmployeeShiftSerializer(assignment).data,
        })


# =============================================
# HR Stats View
# =============================================

class HRStatsView(views.APIView):
    """GET: HR statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        active_emps = Employee.objects.filter(is_active=True, status='active')
        stats = {
            'total_employees': Employee.objects.filter(is_active=True).count(),
            'active_employees': active_emps.count(),
            'on_leave_employees': Employee.objects.filter(status='on_leave', is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'total_salary_expense': active_emps.aggregate(
                total=Coalesce(
                    Sum(F('salary') + F('housing_allowance') + F('transport_allowance')),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'pending_leaves': LeaveRequest.objects.filter(approval_status='pending').count(),
            'today_attendance': Attendance.objects.filter(date=today, status='present').count(),
            'today_absent': Attendance.objects.filter(date=today, status='absent').count(),
        }

        serializer = HRStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export Views
# =============================================

class EmployeeExportView(views.APIView):
    """GET: Export employees to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Employee.objects.select_related('department')
        columns = [
            ('employee_number', 'رقم الموظف', 15),
            ('full_name', 'الاسم الكامل', 30),
            ('email', 'البريد الإلكتروني', 30),
            ('phone', 'الهاتف', 15),
            ('department', 'القسم', 20),
            ('position', 'المسمى الوظيفي', 25),
            ('hire_date', 'تاريخ التعيين', 15),
            ('salary', 'الراتب الأساسي', 15),
            ('status', 'الحالة', 15),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for e in queryset:
            data.append({
                'employee_number': e.employee_number,
                'full_name': e.full_name,
                'email': e.email or '',
                'phone': e.phone or '',
                'department': e.department.name if e.department else '',
                'position': e.position or '',
                'hire_date': str(e.hire_date) if e.hire_date else '',
                'salary': str(e.salary),
                'status': e.get_status_display(),
                'is_active': e.is_active,
            })
        return export_to_excel(data, columns, 'الموظفون', 'employees.xlsx')


class AttendanceExportView(views.APIView):
    """GET: Export attendance records to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Attendance.objects.select_related('employee__department')
        columns = [
            ('employee', 'الموظف', 30),
            ('department', 'القسم', 20),
            ('date', 'التاريخ', 15),
            ('check_in', 'وقت الحضور', 12),
            ('check_out', 'وقت الانصراف', 12),
            ('status', 'الحالة', 15),
            ('notes', 'ملاحظات', 30),
        ]
        data = []
        for a in queryset:
            data.append({
                'employee': a.employee.full_name if a.employee else '',
                'department': a.employee.department.name if a.employee and a.employee.department else '',
                'date': str(a.date) if a.date else '',
                'check_in': str(a.check_in) if a.check_in else '',
                'check_out': str(a.check_out) if a.check_out else '',
                'status': a.get_status_display(),
                'notes': a.notes or '',
            })
        return export_to_excel(data, columns, 'سجلات الحضور', 'attendance.xlsx')


class LeaveExportView(views.APIView):
    """GET: Export leave requests to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = LeaveRequest.objects.select_related('employee__department', 'approved_by')
        columns = [
            ('employee', 'الموظف', 30),
            ('leave_type', 'نوع الإجازة', 18),
            ('start_date', 'تاريخ البداية', 15),
            ('end_date', 'تاريخ النهاية', 15),
            ('days', 'عدد الأيام', 12),
            ('reason', 'السبب', 30),
            ('approval_status', 'حالة الموافقة', 15),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for l in queryset:
            data.append({
                'employee': l.employee.full_name if l.employee else '',
                'leave_type': l.get_leave_type_display(),
                'start_date': str(l.start_date) if l.start_date else '',
                'end_date': str(l.end_date) if l.end_date else '',
                'days': l.days,
                'reason': l.reason or '',
                'approval_status': l.get_approval_status_display(),
                'created_at': str(l.created_at.strftime('%Y-%m-%d %H:%M')) if l.created_at else '',
            })
        return export_to_excel(data, columns, 'طلبات الإجازات', 'leaves.xlsx')


# =============================================
# Holiday Calendar Views
# =============================================

class HolidayCalendarListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List holiday calendars. POST: Create calendar (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'year']
    ordering = ['-year', 'name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HolidayCalendarCreateSerializer
        return HolidayCalendarListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = HolidayCalendar.objects.annotate(
            holidays_count=Count('holidays')
        )
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calendar = serializer.save()
        return Response({
            'message': 'تم إنشاء تقويم الإجازات بنجاح',
            'calendar': HolidayCalendarListSerializer(calendar).data,
        }, status=status.HTTP_201_CREATED)


class HolidayCalendarDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET: Holiday calendar details. PATCH: Update (admin only)."""

    permission_module = 'hr'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return HolidayCalendarCreateSerializer
        return HolidayCalendarDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return HolidayCalendar.objects.annotate(
            holidays_count=Count('holidays')
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        calendar = serializer.save()
        return Response({
            'message': 'تم تحديث تقويم الإجازات بنجاح',
            'calendar': HolidayCalendarDetailSerializer(calendar).data,
        })


class HolidayListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List holidays for a calendar, filterable by date range and type."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = HolidayListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'name', 'holiday_type']
    ordering = ['date']

    def get_queryset(self):
        queryset = Holiday.objects.select_related('calendar')
        # Filter by calendar
        calendar = self.request.query_params.get('calendar')
        if calendar:
            queryset = queryset.filter(calendar_id=calendar)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        # Filter by holiday type
        holiday_type = self.request.query_params.get('holiday_type')
        if holiday_type:
            queryset = queryset.filter(holiday_type=holiday_type)
        # Filter by recurring
        is_recurring = self.request.query_params.get('is_recurring')
        if is_recurring is not None:
            queryset = queryset.filter(is_recurring=is_recurring.lower() == 'true')
        return queryset


class HolidayDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Retrieve a single holiday."""
    permission_module = 'hr'
    permission_required = 'hr.view_holiday'
    queryset = Holiday.objects.select_related('calendar')
    serializer_class = HolidaySerializer


class HolidayDeleteView(PermissionRequiredMixin, generics.DestroyAPIView):
    """DELETE: Delete a single holiday (admin only)."""
    permission_module = 'hr'
    permission_required = 'hr.delete_holiday'
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer


class HolidayCreateView(views.APIView):
    """POST: Create a single holiday (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = HolidayCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        holiday = serializer.save()
        return Response({
            'message': 'تم إنشاء الإجازة بنجاح',
            'holiday': HolidaySerializer(holiday).data,
        }, status=status.HTTP_201_CREATED)


class HolidayBulkCreateView(views.APIView):
    """POST: Create multiple holidays at once for a calendar (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = HolidayBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        calendar = serializer.validated_data['calendar']
        holidays_data = serializer.validated_data['holidays']
        created = []
        skipped = 0

        with transaction.atomic():
            for h_data in holidays_data:
                h_data['calendar'] = calendar
                h_serializer = HolidayCreateSerializer(data=h_data)
                h_serializer.is_valid(raise_exception=False)
                if h_serializer.errors:
                    skipped += 1
                    continue
                holiday = h_serializer.save()
                created.append(holiday)

        return Response({
            'message': f'تم إنشاء {len(created)} إجازة بنجاح',
            'created_count': len(created),
            'skipped_count': skipped,
            'holidays': HolidayListSerializer(created, many=True).data,
        }, status=status.HTTP_201_CREATED)


class YearCalendarView(views.APIView):
    """GET: Get all holidays for a specific calendar, year, and optional month."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        calendar_id = request.query_params.get('calendar')
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not calendar_id or not year:
            return Response(
                {'error': 'يرجى تحديد calendar و year'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            calendar = HolidayCalendar.objects.get(pk=calendar_id)
        except HolidayCalendar.DoesNotExist:
            return Response(
                {'error': 'تقويم الإجازات غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = Holiday.objects.filter(calendar=calendar).order_by('date')

        # Filter by month if provided
        if month:
            queryset = queryset.filter(date__month=month)

        holidays = list(queryset)
        return Response({
            'calendar': HolidayCalendarDetailSerializer(calendar).data,
            'year': int(year),
            'month': int(month) if month else None,
            'holidays': HolidayListSerializer(holidays, many=True).data,
            'total_holidays': len(holidays),
        })


# =============================================
# Employment History Views
# =============================================

class EmploymentHistoryListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List employment history entries with employee filter."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = EmploymentHistoryListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['effective_date', 'action_type', '-effective_date']
    ordering = ['-effective_date']

    def get_queryset(self):
        queryset = EmploymentHistory.objects.select_related(
            'employee', 'department', 'created_by'
        )
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset


class EmploymentHistoryCreateView(views.APIView):
    """POST: Create an employment history entry (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = EmploymentHistoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        history = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء السجل الوظيفي بنجاح',
            'history': EmploymentHistoryListSerializer(history).data,
        }, status=status.HTTP_201_CREATED)


class EmployeeFullHistoryView(views.APIView):
    """GET: Get comprehensive history for one employee - returns leaves,
    attendance summary, performance reviews, salary changes, and employment history."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            employee = Employee.objects.select_related('department').get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'الموظف غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Employment history
        employment_history = EmploymentHistory.objects.filter(
            employee=employee
        ).select_related('department', 'created_by').order_by('-effective_date')

        # Leave requests
        leave_requests = LeaveRequest.objects.filter(
            employee=employee
        ).select_related('approved_by').order_by('-created_at')

        # Attendance summary
        today = timezone.now().date()
        year_start = today.replace(month=1, day=1)
        attendance_data = Attendance.objects.filter(
            employee=employee,
            date__gte=year_start,
        ).aggregate(
            total_present=Coalesce(
                Count('id', filter=Q(status='present')),
                Value(0)
            ),
            total_absent=Coalesce(
                Count('id', filter=Q(status='absent')),
                Value(0)
            ),
            total_late=Coalesce(
                Count('id', filter=Q(status='late')),
                Value(0)
            ),
            total_half_day=Coalesce(
                Count('id', filter=Q(status='half_day')),
                Value(0)
            ),
            total_holidays=Coalesce(
                Count('id', filter=Q(status='holiday')),
                Value(0)
            ),
        )

        # Performance reviews
        performance_reviews = PerformanceReview.objects.filter(
            employee=employee
        ).select_related('reviewer').order_by('-year')

        # Salary changes (from employment history)
        salary_changes = list(
            EmploymentHistory.objects.filter(
                employee=employee,
                action_type__in=('hire', 'promotion', 'demotion', 'salary_change'),
            ).values(
                'effective_date', 'previous_salary', 'salary', 'reason', 'action_type'
            ).order_by('-effective_date')
        )
        salary_changes_data = [
            {
                'date': sc['effective_date'],
                'action_type': sc['action_type'],
                'previous_salary': str(sc['previous_salary']) if sc['previous_salary'] else '0.00',
                'new_salary': str(sc['salary']) if sc['salary'] else '0.00',
                'reason': sc['reason'] or '',
            }
            for sc in salary_changes
        ]

        return Response({
            'employee': EmployeeDetailSerializer(employee).data,
            'employment_history': EmploymentHistoryListSerializer(
                employment_history, many=True
            ).data,
            'leave_requests': LeaveRequestListSerializer(
                leave_requests, many=True
            ).data,
            'attendance_summary': {
                'total_present': attendance_data['total_present'],
                'total_absent': attendance_data['total_absent'],
                'total_late': attendance_data['total_late'],
                'total_half_day': attendance_data['total_half_day'],
                'total_holidays': attendance_data['total_holidays'],
            },
            'performance_reviews': PerformanceReviewSerializer(
                performance_reviews, many=True
            ).data,
            'salary_changes': salary_changes_data,
        })


# =============================================
# Payslip Views
# =============================================

class PayslipListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List payslips with filters for employee, month, year, status."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = PayslipListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['employee__first_name', 'year', '-year', 'month', 'status']
    ordering = ['-year', '-month']

    def get_queryset(self):
        queryset = Payslip.objects.select_related(
            'employee__department', 'approved_by'
        )
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by month
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        # Filter by status
        payslip_status = self.request.query_params.get('status')
        if payslip_status:
            queryset = queryset.filter(status=payslip_status)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(employee__department_id=department)
        return queryset


class PayslipDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Retrieve single payslip detail."""

    permission_module = 'hr'
    permission_action = 'view'

    serializer_class = PayslipDetailSerializer

    def get_queryset(self):
        return Payslip.objects.select_related(
            'employee__department', 'approved_by'
        )


class PayslipGenerateView(views.APIView):
    """POST: Generate payslips for all active employees (or specific ones) for a month.
    
    Automatically populates basic_salary, housing_allowance, transport_allowance
    from employee records. All deduction and bonus fields default to 0 for manual adjustment.
    """

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = PayslipGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        employee_ids = serializer.validated_data.get('employee_ids')

        # Determine target employees
        if employee_ids:
            employees = Employee.objects.filter(
                id__in=employee_ids, is_active=True
            ).select_related('department')
        else:
            employees = Employee.objects.filter(
                is_active=True, status='active'
            ).select_related('department')

        if not employees.exists():
            return Response(
                {'error': 'لا يوجد موظفون مؤهلون لتوليد قسائم الرواتب'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        skipped = []

        with transaction.atomic():
            for emp in employees:
                # Check if payslip already exists
                if Payslip.objects.filter(
                    employee=emp, month=month, year=year
                ).exists():
                    skipped.append(emp.employee_number)
                    continue

                payslip = Payslip.objects.create(
                    employee=emp,
                    month=month,
                    year=year,
                    basic_salary=emp.salary,
                    housing_allowance=emp.housing_allowance,
                    transport_allowance=emp.transport_allowance,
                    status='draft',
                )
                created.append(payslip)

        return Response({
            'message': f'تم توليد {len(created)} قسيمة راتب بنجاح',
            'month': month,
            'year': year,
            'created_count': len(created),
            'skipped_count': len(skipped),
            'skipped_employees': skipped,
            'payslips': PayslipListSerializer(created, many=True).data,
        }, status=status.HTTP_201_CREATED)


class PayslipApproveView(views.APIView):
    """POST: Approve or reject a payslip (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            payslip = Payslip.objects.select_related('employee').get(pk=pk)
        except Payslip.DoesNotExist:
            return Response(
                {'error': 'قسيمة الراتب غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PayslipApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        if action == 'approve':
            if payslip.status not in ('draft',):
                return Response(
                    {'error': 'يمكن الاعتماد فقط على القسائم المسودة'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payslip.status = 'approved'
            payslip.approved_by = request.user
            payslip.approved_at = timezone.now()
            if notes:
                payslip.notes = (payslip.notes + '\n' + notes).strip()
            payslip.save()
            return Response({
                'message': 'تم اعتماد قسيمة الراتب بنجاح',
                'payslip': PayslipDetailSerializer(payslip).data,
            })

        elif action == 'reject':
            if payslip.status not in ('draft', 'approved'):
                return Response(
                    {'error': 'يمكن الرفض فقط على القسائم المسودة أو المعتمدة'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payslip.status = 'draft'
            payslip.approved_by = None
            payslip.approved_at = None
            if notes:
                payslip.notes = (payslip.notes + '\n' + notes).strip()
            payslip.save()
            return Response({
                'message': 'تم رفض قسيمة الراتب وإعادتها للمسودة',
                'payslip': PayslipDetailSerializer(payslip).data,
            })


class PayslipStatsView(views.APIView):
    """GET: Payroll summary statistics for a specific month/year."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not month or not year:
            return Response(
                {'error': 'يرجى تحديد الشهر والسنة (month و year)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month = int(month)
        year = int(year)

        payslips = Payslip.objects.filter(month=month, year=year)

        stats = payslips.aggregate(
            total_earnings=Coalesce(
                Sum(
                    F('basic_salary') + F('housing_allowance') + F('transport_allowance')
                    + F('overtime_pay') + F('bonuses')
                ),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            total_deductions=Coalesce(
                Sum(
                    F('deductions') + F('insurance_deduction') + F('tax_deduction')
                    + F('loan_deduction') + F('advance_deduction') + F('other_deduction')
                ),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        total_net_pay = stats['total_earnings'] - stats['total_deductions']

        return Response({
            'month': month,
            'year': year,
            'total_employees': payslips.count(),
            'total_earnings': stats['total_earnings'],
            'total_deductions': stats['total_deductions'],
            'total_net_pay': total_net_pay,
            'approved_count': payslips.filter(status='approved').count(),
            'draft_count': payslips.filter(status='draft').count(),
            'paid_count': payslips.filter(status='paid').count(),
        })
