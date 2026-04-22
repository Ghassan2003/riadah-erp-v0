"""
API views for the HR module - Phase 5.
Handles Department, Employee, Attendance, and Leave management.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Department, Employee, Attendance, LeaveRequest
from .serializers import (
    DepartmentListSerializer,
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    DepartmentDetailSerializer,
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
    HRStatsSerializer,
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
        queryset = Department.objects.prefetch_related('manager')
        return queryset

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
        return Department.objects.prefetch_related('manager', 'employees')

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
        return Employee.objects.select_related('department')

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
    """POST: Approve or reject a leave request (admin only)."""

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

        if leave.approval_status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على الطلبات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            leave.approval_status = 'approved'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            return Response({
                'message': 'تمت الموافقة على طلب الإجازة',
                'leave': LeaveRequestListSerializer(leave).data,
            })
        else:
            leave.approval_status = 'rejected'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            return Response({
                'message': 'تم رفض طلب الإجازة',
                'leave': LeaveRequestListSerializer(leave).data,
            })


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
