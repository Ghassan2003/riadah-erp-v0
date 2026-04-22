"""
API views for the Payroll module.
Handles PayrollPeriods, PayrollRecords, SalaryAdvances, EmployeeLoans,
EndOfServiceBenefits, stats, and export.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse

from .models import (
    PayrollPeriod,
    PayrollRecord,
    SalaryAdvance,
    EmployeeLoan,
    EndOfServiceBenefit,
)
from .serializers import (
    PayrollPeriodListSerializer,
    PayrollPeriodCreateSerializer,
    PayrollPeriodUpdateSerializer,
    PayrollPeriodDetailSerializer,
    PayrollRecordListSerializer,
    PayrollRecordCreateSerializer,
    PayrollRecordUpdateSerializer,
    SalaryAdvanceListSerializer,
    SalaryAdvanceCreateSerializer,
    SalaryAdvanceApproveSerializer,
    EmployeeLoanListSerializer,
    EmployeeLoanCreateSerializer,
    EmployeeLoanApproveSerializer,
    EndOfServiceBenefitListSerializer,
    EndOfServiceBenefitCreateSerializer,
    PayrollStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Payroll Period Views
# =============================================

class PayrollPeriodListView(generics.ListCreateAPIView):
    """GET: List payroll periods. POST: Create payroll period (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'year', 'month', 'status', 'created_at']
    ordering = ['-year', '-month']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PayrollPeriodCreateSerializer
        return PayrollPeriodListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = PayrollPeriod.objects.select_related('created_by')
        # Filter by status
        period_status = self.request.query_params.get('status')
        if period_status:
            queryset = queryset.filter(status=period_status)
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        period = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء فترة الرواتب بنجاح',
            'period': PayrollPeriodDetailSerializer(period).data,
        }, status=status.HTTP_201_CREATED)


class PayrollPeriodDetailView(generics.RetrieveUpdateAPIView):
    """GET: Payroll period details. PATCH: Update payroll period (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PayrollPeriodUpdateSerializer
        return PayrollPeriodDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return PayrollPeriod.objects.select_related('created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        period = serializer.save()
        return Response({
            'message': 'تم تحديث فترة الرواتب بنجاح',
            'period': PayrollPeriodDetailSerializer(period).data,
        })


class PayrollPeriodDeleteView(views.APIView):
    """DELETE: Delete a payroll period (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            period = PayrollPeriod.objects.get(pk=pk)
        except PayrollPeriod.DoesNotExist:
            return Response(
                {'error': 'فترة الرواتب غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if period.status not in ('draft',):
            return Response(
                {'error': 'لا يمكن حذف فترة ليست في حالة مسودة'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period.delete()
        return Response({'message': 'تم حذف فترة الرواتب بنجاح'})


class PayrollGenerateView(views.APIView):
    """
    POST: Generate payroll records for a period.
    Auto-creates PayrollRecords for all active employees using their salary data.
    """

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            period = PayrollPeriod.objects.get(pk=pk)
        except PayrollPeriod.DoesNotExist:
            return Response(
                {'error': 'فترة الرواتب غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if period.status != 'draft':
            return Response(
                {'error': 'لا يمكن توليد رواتب لفترة ليست في حالة مسودة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from hr.models import Employee

        # Get all active employees
        active_employees = Employee.objects.filter(
            is_active=True,
            status='active',
        ).select_related('department')

        if not active_employees.exists():
            return Response(
                {'error': 'لا يوجد موظفين نشطين لتوليد الرواتب'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records_created = 0
        total_salaries = Decimal('0')
        total_deductions = Decimal('0')
        total_net = Decimal('0')

        for emp in active_employees:
            # Check if record already exists
            if PayrollRecord.objects.filter(period=period, employee=emp).exists():
                continue

            # Get active loans for this employee and sum monthly installments
            loan_deduction = EmployeeLoan.objects.filter(
                employee=emp,
                status='active',
            ).aggregate(
                total=Coalesce(
                    Sum('monthly_installment'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'] or Decimal('0')

            # Get approved advances with monthly deductions
            advance_deduction = SalaryAdvance.objects.filter(
                employee=emp,
                status__in=('approved', 'paid'),
                months_remaining__gt=0,
            ).aggregate(
                total=Coalesce(
                    Sum('monthly_deduction'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'] or Decimal('0')

            # Calculate GOSI deduction (9.75% of basic salary for Saudi)
            gosi_rate = Decimal('0.0975')
            deductions_gosi = (emp.salary * gosi_rate).quantize(Decimal('0.01'))

            # Total deductions
            total_ded = deductions_gosi + loan_deduction + advance_deduction

            # Calculate earnings
            total_earn = emp.salary + emp.housing_allowance + emp.transport_allowance

            # Net salary
            net_sal = total_earn - total_ded

            # Create the payroll record
            record = PayrollRecord.objects.create(
                period=period,
                employee=emp,
                basic_salary=emp.salary,
                housing_allowance=emp.housing_allowance,
                transport_allowance=emp.transport_allowance,
                deductions_gosi=deductions_gosi,
                deductions_loan=loan_deduction,
                deductions_other=advance_deduction,
                deductions_other_description='خصم السلف الشهرية' if advance_deduction > 0 else '',
                total_earnings=total_earn,
                total_deductions_amount=total_ded,
                net_salary=net_sal,
                payment_method='bank_transfer',
                payment_status='pending',
                created_by=request.user,
            )
            records_created += 1
            total_salaries += total_earn
            total_deductions += total_ded
            total_net += net_sal

        # Update period totals and status
        period.total_employees = records_created
        period.total_salaries = total_salaries
        period.total_deductions = total_deductions
        period.total_net = total_net
        period.status = 'processing'
        period.save()

        return Response({
            'message': f'تم توليد {records_created} سجل راتب بنجاح',
            'period': PayrollPeriodDetailSerializer(period).data,
            'records_created': records_created,
            'total_salaries': str(total_salaries),
            'total_deductions': str(total_deductions),
            'total_net': str(total_net),
        })


class PayrollCloseView(views.APIView):
    """POST: Close a payroll period (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            period = PayrollPeriod.objects.get(pk=pk)
        except PayrollPeriod.DoesNotExist:
            return Response(
                {'error': 'فترة الرواتب غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if period.status != 'paid':
            return Response(
                {'error': 'لا يمكن إغلاق فترة رواتب ليست في حالة مدفوع'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if all records are paid
        unpaid_count = period.records.filter(payment_status='pending').count()
        if unpaid_count > 0:
            return Response(
                {'error': f'يوجد {unpaid_count} سجل راتب لم يتم دفعها بعد'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Close the period
        period.status = 'closed'
        period.save()

        return Response({
            'message': 'تم إغلاق فترة الرواتب بنجاح',
            'period': PayrollPeriodDetailSerializer(period).data,
        })


# =============================================
# Payroll Record Views
# =============================================

class PayrollRecordListView(generics.ListAPIView):
    """GET: List payroll records with filtering."""

    serializer_class = PayrollRecordListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_number']
    ordering_fields = ['employee__first_name', 'net_salary', 'payment_status', 'created_at']
    ordering = ['employee__first_name']

    def get_queryset(self):
        queryset = PayrollRecord.objects.select_related(
            'period', 'employee__department', 'created_by'
        )
        # Filter by period
        period = self.request.query_params.get('period')
        if period:
            queryset = queryset.filter(period_id=period)
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        return queryset


class PayrollRecordDetailView(generics.RetrieveAPIView):
    """GET: Payroll record details."""

    serializer_class = PayrollRecordListSerializer

    def get_queryset(self):
        return PayrollRecord.objects.select_related(
            'period', 'employee__department', 'created_by'
        )


class PayrollRecordUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a payroll record (admin only)."""

    serializer_class = PayrollRecordUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return PayrollRecord.objects.select_related('period', 'employee__department')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Ensure period is in processing status
        if instance.period.status not in ('draft', 'processing'):
            return Response(
                {'error': 'لا يمكن تعديل سجل راتب لفترة ليست في حالة مسودة أو قيد المعالجة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()

        # Recalculate totals
        record.recalculate()

        return Response({
            'message': 'تم تحديث سجل الراتب بنجاح',
            'record': PayrollRecordListSerializer(record).data,
        })


class PayrollPayRecordView(views.APIView):
    """POST: Mark a payroll record as paid (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            record = PayrollRecord.objects.select_related('period', 'employee').get(pk=pk)
        except PayrollRecord.DoesNotExist:
            return Response(
                {'error': 'سجل الراتب غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.payment_status == 'paid':
            return Response(
                {'error': 'هذا السجل مدفوع مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.payment_status = 'paid'
        record.payment_date = timezone.now().date()

        # Optionally update bank reference
        bank_ref = request.data.get('bank_reference')
        if bank_ref:
            record.bank_reference = bank_ref

        record.save()

        # Update period status to paid if all records are paid
        period = record.period
        unpaid_count = period.records.filter(payment_status='pending').count()
        if unpaid_count == 0:
            period.status = 'paid'
            period.save()

        return Response({
            'message': 'تم دفع الراتب بنجاح',
            'record': PayrollRecordListSerializer(record).data,
        })


# =============================================
# Salary Advance Views
# =============================================

class SalaryAdvanceListView(generics.ListCreateAPIView):
    """GET: List salary advances. POST: Create salary advance."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'purpose']
    ordering_fields = ['employee__first_name', 'amount', 'status', 'advance_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SalaryAdvanceCreateSerializer
        return SalaryAdvanceListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = SalaryAdvance.objects.select_related('employee__department', 'approved_by')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by status
        adv_status = self.request.query_params.get('status')
        if adv_status:
            queryset = queryset.filter(status=adv_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        advance = serializer.save()
        return Response({
            'message': 'تم إنشاء طلب السلفة بنجاح',
            'advance': SalaryAdvanceListSerializer(advance).data,
        }, status=status.HTTP_201_CREATED)


class SalaryAdvanceApproveView(views.APIView):
    """POST: Approve or reject a salary advance (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            advance = SalaryAdvance.objects.select_related('employee').get(pk=pk)
        except SalaryAdvance.DoesNotExist:
            return Response(
                {'error': 'طلب السلفة غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SalaryAdvanceApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if advance.status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على الطلبات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            monthly_deduction = serializer.validated_data.get('monthly_deduction')
            months = serializer.validated_data.get('months')

            if not monthly_deduction or not months:
                return Response(
                    {'error': 'يجب تحديد الخصم الشهري وعدد الأشهر عند الموافقة'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            advance.status = 'approved'
            advance.approved_by = request.user
            advance.approved_at = timezone.now()
            advance.monthly_deduction = monthly_deduction
            advance.months_remaining = months
            advance.save()

            return Response({
                'message': 'تمت الموافقة على طلب السلفة',
                'advance': SalaryAdvanceListSerializer(advance).data,
            })
        else:
            advance.status = 'rejected'
            advance.approved_by = request.user
            advance.approved_at = timezone.now()
            advance.save()

            return Response({
                'message': 'تم رفض طلب السلفة',
                'advance': SalaryAdvanceListSerializer(advance).data,
            })


class SalaryAdvanceDetailView(generics.RetrieveAPIView):
    """GET: Salary advance detail."""

    serializer_class = SalaryAdvanceListSerializer

    def get_queryset(self):
        return SalaryAdvance.objects.select_related('employee__department', 'approved_by')


class SalaryAdvanceDeleteView(views.APIView):
    """DELETE: Delete a salary advance (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            advance = SalaryAdvance.objects.get(pk=pk)
        except SalaryAdvance.DoesNotExist:
            return Response({'error': 'طلب السلفة غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if advance.status in ('approved', 'paid'):
            return Response({'error': 'لا يمكن حذف سلفة معتمدة أو مدفوعة'}, status=status.HTTP_400_BAD_REQUEST)
        advance.delete()
        return Response({'message': 'تم حذف طلب السلفة بنجاح'})


# =============================================
# Employee Loan Views
# =============================================

class EmployeeLoanListView(generics.ListCreateAPIView):
    """GET: List employee loans. POST: Create employee loan."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'purpose']
    ordering_fields = ['employee__first_name', 'amount', 'status', 'start_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeLoanCreateSerializer
        return EmployeeLoanListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = EmployeeLoan.objects.select_related('employee__department', 'approved_by')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by status
        loan_status = self.request.query_params.get('status')
        if loan_status:
            queryset = queryset.filter(status=loan_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        return Response({
            'message': 'تم إنشاء طلب القرض بنجاح',
            'loan': EmployeeLoanListSerializer(loan).data,
        }, status=status.HTTP_201_CREATED)


class EmployeeLoanApproveView(views.APIView):
    """POST: Approve or reject an employee loan (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            loan = EmployeeLoan.objects.select_related('employee').get(pk=pk)
        except EmployeeLoan.DoesNotExist:
            return Response(
                {'error': 'طلب القرض غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeLoanApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if loan.status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على الطلبات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import date
        from dateutil.relativedelta import relativedelta

        if action == 'approve':
            loan.status = 'active'
            loan.approved_by = request.user
            loan.approved_at = timezone.now()
            loan.months_remaining = loan.months
            # Calculate end date
            if loan.start_date:
                loan.end_date = loan.start_date + relativedelta(months=loan.months)
            loan.save()

            return Response({
                'message': 'تمت الموافقة على طلب القرض',
                'loan': EmployeeLoanListSerializer(loan).data,
            })
        else:
            loan.status = 'rejected'
            loan.approved_by = request.user
            loan.approved_at = timezone.now()
            loan.save()

            return Response({
                'message': 'تم رفض طلب القرض',
                'loan': EmployeeLoanListSerializer(loan).data,
            })


class EmployeeLoanDetailView(generics.RetrieveAPIView):
    """GET: Employee loan detail."""

    serializer_class = EmployeeLoanListSerializer

    def get_queryset(self):
        return EmployeeLoan.objects.select_related('employee__department', 'approved_by')


class EmployeeLoanDeleteView(views.APIView):
    """DELETE: Delete an employee loan (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            loan = EmployeeLoan.objects.get(pk=pk)
        except EmployeeLoan.DoesNotExist:
            return Response({'error': 'طلب القرض غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if loan.status == 'active':
            return Response({'error': 'لا يمكن حذف قرض نشط'}, status=status.HTTP_400_BAD_REQUEST)
        loan.delete()
        return Response({'message': 'تم حذف طلب القرض بنجاح'})


# =============================================
# End of Service Views
# =============================================

class EndOfServiceListView(generics.ListCreateAPIView):
    """GET: List end of service benefits. POST: Create end of service benefit."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['employee__first_name', 'net_benefit', 'status', 'calculation_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EndOfServiceBenefitCreateSerializer
        return EndOfServiceBenefitListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = EndOfServiceBenefit.objects.select_related('employee__department')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by status
        eos_status = self.request.query_params.get('status')
        if eos_status:
            queryset = queryset.filter(status=eos_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        eos = serializer.save()
        return Response({
            'message': 'تم إنشاء مكافأة نهاية الخدمة بنجاح',
            'benefit': EndOfServiceBenefitListSerializer(eos).data,
        }, status=status.HTTP_201_CREATED)


class EndOfServiceDetailView(generics.RetrieveAPIView):
    """GET: End of service benefit detail."""

    serializer_class = EndOfServiceBenefitListSerializer

    def get_queryset(self):
        return EndOfServiceBenefit.objects.select_related('employee__department')


class EndOfServiceDeleteView(views.APIView):
    """DELETE: Delete an end of service benefit (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            eos = EndOfServiceBenefit.objects.get(pk=pk)
        except EndOfServiceBenefit.DoesNotExist:
            return Response({'error': 'مكافأة نهاية الخدمة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        eos.delete()
        return Response({'message': 'تم حذف مكافأة نهاية الخدمة بنجاح'})


# =============================================
# Payroll Stats View
# =============================================

class PayrollStatsView(views.APIView):
    """GET: Payroll statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        current_month = now.month
        current_year = now.year

        from hr.models import Employee

        stats = {
            'total_periods': PayrollPeriod.objects.count(),
            'active_periods': PayrollPeriod.objects.filter(
                status__in=('draft', 'processing', 'paid')
            ).count(),
            'current_month_records': PayrollRecord.objects.filter(
                period__month=current_month,
                period__year=current_year,
            ).count(),
            'total_paid_this_month': PayrollRecord.objects.filter(
                period__month=current_month,
                period__year=current_year,
                payment_status='paid',
            ).aggregate(
                total=Coalesce(
                    Sum('net_salary'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_pending_records': PayrollRecord.objects.filter(
                payment_status='pending',
            ).count(),
            'active_advances': SalaryAdvance.objects.filter(
                status__in=('approved', 'paid'),
                months_remaining__gt=0,
            ).count(),
            'active_loans': EmployeeLoan.objects.filter(
                status='active',
            ).count(),
            'advances_total': SalaryAdvance.objects.filter(
                status__in=('approved', 'paid'),
                months_remaining__gt=0,
            ).aggregate(
                total=Coalesce(
                    Sum('amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'loans_total': EmployeeLoan.objects.filter(
                status='active',
            ).aggregate(
                total=Coalesce(
                    Sum('amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'end_of_service_pending': EndOfServiceBenefit.objects.filter(
                status__in=('calculated', 'partial'),
            ).count(),
            'total_employees': Employee.objects.filter(is_active=True, status='active').count(),
        }

        serializer = PayrollStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Payroll Export View
# =============================================

class PayrollExportView(views.APIView):
    """GET: Export payroll records to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        queryset = PayrollRecord.objects.select_related(
            'period', 'employee__department'
        ).order_by('period__name', 'employee__first_name')

        # Filter by period
        period = self.request.query_params.get('period')
        if period:
            queryset = queryset.filter(period_id=period)

        columns = [
            ('employee_number', 'رقم الموظف', 15),
            ('employee_name', 'اسم الموظف', 30),
            ('department', 'القسم', 20),
            ('period', 'الفترة', 20),
            ('basic_salary', 'الراتب الأساسي', 15),
            ('housing', 'بدل السكن', 12),
            ('transport', 'بدل النقل', 12),
            ('food', 'بدل الطعام', 12),
            ('overtime', 'ساعات/مبلغ الإضافي', 18),
            ('bonus', 'المكافأة', 12),
            ('commission', 'العمولة', 12),
            ('gosi', 'خصم GOSI', 12),
            ('tax', 'خصم الضريبة', 12),
            ('absence', 'خصم الغياب', 12),
            ('loan', 'خصم القروض', 12),
            ('other_deductions', 'خصومات أخرى', 14),
            ('total_earnings', 'إجمالي الاستحقاقات', 16),
            ('total_deductions', 'إجمالي الخصومات', 16),
            ('net_salary', 'صافي الراتب', 15),
            ('payment_status', 'حالة الدفع', 15),
            ('payment_method', 'طريقة الدفع', 15),
        ]
        data = []
        for r in queryset:
            data.append({
                'employee_number': r.employee.employee_number if r.employee else '',
                'employee_name': r.employee.full_name if r.employee else '',
                'department': r.employee.department.name if r.employee and r.employee.department else '',
                'period': r.period.name if r.period else '',
                'basic_salary': str(r.basic_salary),
                'housing': str(r.housing_allowance),
                'transport': str(r.transport_allowance),
                'food': str(r.food_allowance),
                'overtime': f"{r.overtime_hours}h / {r.overtime_amount}",
                'bonus': str(r.bonus),
                'commission': str(r.commission),
                'gosi': str(r.deductions_gosi),
                'tax': str(r.deductions_tax),
                'absence': str(r.deductions_absence),
                'loan': str(r.deductions_loan),
                'other_deductions': str(r.deductions_other),
                'total_earnings': str(r.total_earnings),
                'total_deductions': str(r.total_deductions_amount),
                'net_salary': str(r.net_salary),
                'payment_status': r.get_payment_status_display(),
                'payment_method': r.get_payment_method_display(),
            })
        return export_to_excel(data, columns, 'كشف الرواتب', 'payroll.xlsx')
