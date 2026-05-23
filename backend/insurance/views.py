"""
API views for the Insurance & Pension module.
Handles InsurancePolicy, InsuranceClaim, PensionRecord, PensionPayment,
stats, and export.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    InsurancePolicy,
    InsuranceClaim,
    PensionRecord,
    PensionPayment,
)
from .serializers import (
    InsurancePolicyListSerializer,
    InsurancePolicyCreateSerializer,
    InsurancePolicyDetailSerializer,
    InsuranceClaimListSerializer,
    InsuranceClaimSubmitSerializer,
    InsuranceClaimReviewSerializer,
    PensionRecordListSerializer,
    PensionRecordCreateSerializer,
    PensionRecordDetailSerializer,
    PensionPaymentListSerializer,
    PensionPaymentCreateSerializer,
    InsuranceStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Insurance Stats View
# =============================================

class InsuranceStatsView(views.APIView):
    """GET: Insurance & Pension statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_policies': InsurancePolicy.objects.count(),
            'active_policies': InsurancePolicy.objects.filter(status='active').count(),
            'total_premiums': InsurancePolicy.objects.filter(status='active').aggregate(
                total=Coalesce(
                    Sum('premium_amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'pending_claims': InsuranceClaim.objects.filter(
                status__in=('submitted', 'under_review')
            ).count(),
            'total_claims_amount': InsuranceClaim.objects.filter(
                status__in=('submitted', 'under_review')
            ).aggregate(
                total=Coalesce(
                    Sum('claimed_amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_pension_contributions': PensionRecord.objects.filter(status='active').aggregate(
                total=Coalesce(
                    Sum('total_contributions'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'active_pension_records': PensionRecord.objects.filter(status='active').count(),
            'pending_pension_payments': PensionPayment.objects.filter(status='pending').count(),
        }

        serializer = InsuranceStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Insurance Policy Views
# =============================================

class InsurancePolicyListView(generics.ListAPIView):
    """GET: List insurance policies."""

    serializer_class = InsurancePolicyListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['policy_number', 'policy_name', 'insurance_provider']
    ordering_fields = [
        'policy_number', 'policy_name', 'insurance_type', 'status',
        'premium_amount', 'start_date', 'created_at',
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = InsurancePolicy.objects.select_related('created_by')
        # Filter by status
        policy_status = self.request.query_params.get('status')
        if policy_status:
            queryset = queryset.filter(status=policy_status)
        # Filter by insurance type
        insurance_type = self.request.query_params.get('insurance_type')
        if insurance_type:
            queryset = queryset.filter(insurance_type=insurance_type)
        # Filter by insured entity
        insured_entity = self.request.query_params.get('insured_entity')
        if insured_entity:
            queryset = queryset.filter(insured_entity=insured_entity)
        return queryset


class InsurancePolicyDetailView(generics.RetrieveAPIView):
    """GET: Insurance policy details."""

    serializer_class = InsurancePolicyDetailSerializer

    def get_queryset(self):
        return InsurancePolicy.objects.select_related('created_by')


class InsurancePolicyCreateView(generics.CreateAPIView):
    """POST: Create insurance policy (admin only)."""

    serializer_class = InsurancePolicyCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء بوليصة التأمين بنجاح',
            'policy': InsurancePolicyDetailSerializer(policy).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Insurance Claim Views
# =============================================

class InsuranceClaimListView(generics.ListAPIView):
    """GET: List insurance claims with filtering."""

    serializer_class = InsuranceClaimListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['claim_number', 'description', 'policy__policy_number', 'policy__policy_name']
    ordering_fields = ['claim_number', 'claimed_amount', 'status', 'incident_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = InsuranceClaim.objects.select_related(
            'policy', 'submitted_by', 'reviewed_by'
        )
        # Filter by policy
        policy = self.request.query_params.get('policy')
        if policy:
            queryset = queryset.filter(policy_id=policy)
        # Filter by status
        claim_status = self.request.query_params.get('status')
        if claim_status:
            queryset = queryset.filter(status=claim_status)
        return queryset


class InsuranceClaimDetailView(generics.RetrieveAPIView):
    """GET: Insurance claim details."""

    serializer_class = InsuranceClaimListSerializer

    def get_queryset(self):
        return InsuranceClaim.objects.select_related(
            'policy', 'submitted_by', 'reviewed_by'
        )


class InsuranceClaimSubmitView(generics.CreateAPIView):
    """POST: Submit an insurance claim (admin only)."""

    serializer_class = InsuranceClaimSubmitSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claim = serializer.save(submitted_by=request.user)
        return Response({
            'message': 'تم تقديم طلب التعويض بنجاح',
            'claim': InsuranceClaimListSerializer(claim).data,
        }, status=status.HTTP_201_CREATED)


class InsuranceClaimReviewView(views.APIView):
    """POST: Approve or reject an insurance claim (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            claim = InsuranceClaim.objects.select_related('policy').get(pk=pk)
        except InsuranceClaim.DoesNotExist:
            return Response(
                {'error': 'طلب التعويض غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InsuranceClaimReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if claim.status not in ('submitted', 'under_review'):
            return Response(
                {'error': 'يمكن المراجعة فقط على الطلبات المقدمة أو قيد المراجعة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            approved_amount = serializer.validated_data.get('approved_amount')

            if not approved_amount or approved_amount <= 0:
                return Response(
                    {'error': 'يجب تحديد المبلغ المعتمد عند الموافقة'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if approved_amount > claim.claimed_amount:
                return Response(
                    {'error': 'المبلغ المعتمد لا يمكن أن يتجاوز المبلغ المطلوب'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            claim.status = 'approved'
            claim.approved_amount = approved_amount
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.save()

            return Response({
                'message': 'تمت الموافقة على طلب التعويض',
                'claim': InsuranceClaimListSerializer(claim).data,
            })
        else:
            claim.status = 'rejected'
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.save()

            return Response({
                'message': 'تم رفض طلب التعويض',
                'claim': InsuranceClaimListSerializer(claim).data,
            })


# =============================================
# Pension Record Views
# =============================================

class PensionRecordListView(generics.ListAPIView):
    """GET: List pension records."""

    serializer_class = PensionRecordListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'employee__first_name', 'employee__last_name',
        'employee__employee_number', 'pension_scheme',
    ]
    ordering_fields = ['pension_scheme', 'status', 'start_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = PensionRecord.objects.select_related('employee__department')
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        # Filter by status
        record_status = self.request.query_params.get('status')
        if record_status:
            queryset = queryset.filter(status=record_status)
        return queryset


class PensionRecordDetailView(generics.RetrieveAPIView):
    """GET: Pension record details."""

    serializer_class = PensionRecordDetailSerializer

    def get_queryset(self):
        return PensionRecord.objects.select_related('employee__department')


class PensionRecordCreateView(generics.CreateAPIView):
    """POST: Create pension record (admin only)."""

    serializer_class = PensionRecordCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({
            'message': 'تم إنشاء سجل المعاش بنجاح',
            'record': PensionRecordDetailSerializer(record).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Pension Payment Views
# =============================================

class PensionPaymentListView(generics.ListAPIView):
    """GET: List pension payments with filtering."""

    serializer_class = PensionPaymentListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'pension_record__employee__first_name',
        'pension_record__employee__last_name',
        'reference_number',
    ]
    ordering_fields = ['amount', 'payment_date', 'month', 'year', 'status']
    ordering = ['-payment_date']

    def get_queryset(self):
        queryset = PensionPayment.objects.select_related(
            'pension_record__employee'
        )
        # Filter by pension record
        record = self.request.query_params.get('record')
        if record:
            queryset = queryset.filter(pension_record_id=record)
        # Filter by status
        payment_status = self.request.query_params.get('status')
        if payment_status:
            queryset = queryset.filter(status=payment_status)
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        # Filter by month
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        return queryset


class PensionPaymentCreateView(generics.CreateAPIView):
    """POST: Create pension payment (admin only)."""

    serializer_class = PensionPaymentCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response({
            'message': 'تم إنشاء دفعة المعاش بنجاح',
            'payment': PensionPaymentListSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Insurance Export View
# =============================================

class InsuranceExportView(views.APIView):
    """GET: Export insurance data to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = request.query_params.get('type', 'policies')

        if export_type == 'policies':
            queryset = InsurancePolicy.objects.select_related('created_by').order_by('-created_at')
            columns = [
                ('policy_number', 'رقم البوليصة', 20),
                ('policy_name', 'اسم البوليصة', 30),
                ('insurance_provider', 'شركة التأمين', 25),
                ('insurance_type', 'نوع التأمين', 15),
                ('coverage_amount', 'مبلغ التغطية', 15),
                ('premium_amount', 'مبلغ القسط', 15),
                ('premium_frequency', 'تكرار القسط', 12),
                ('start_date', 'تاريخ البداية', 15),
                ('end_date', 'تاريخ النهاية', 15),
                ('status', 'الحالة', 12),
                ('insured_entity', 'الجهة المؤمنة', 15),
                ('notes', 'ملاحظات', 30),
            ]
            data = []
            for p in queryset:
                data.append({
                    'policy_number': p.policy_number,
                    'policy_name': p.policy_name,
                    'insurance_provider': p.insurance_provider,
                    'insurance_type': p.get_insurance_type_display(),
                    'coverage_amount': str(p.coverage_amount),
                    'premium_amount': str(p.premium_amount),
                    'premium_frequency': p.get_premium_frequency_display(),
                    'start_date': str(p.start_date),
                    'end_date': str(p.end_date),
                    'status': p.get_status_display(),
                    'insured_entity': p.get_insured_entity_display(),
                    'notes': p.notes,
                })
            return export_to_excel(data, columns, 'بوالص التأمين', 'insurance_policies.xlsx')

        elif export_type == 'claims':
            queryset = InsuranceClaim.objects.select_related(
                'policy', 'submitted_by', 'reviewed_by'
            ).order_by('-created_at')
            columns = [
                ('claim_number', 'رقم الطلب', 20),
                ('policy_number', 'رقم البوليصة', 20),
                ('policy_name', 'اسم البوليصة', 30),
                ('claim_type', 'نوع التعويض', 15),
                ('incident_date', 'تاريخ الحادث', 15),
                ('claimed_amount', 'المبلغ المطلوب', 15),
                ('approved_amount', 'المبلغ المعتمد', 15),
                ('status', 'الحالة', 12),
                ('submitted_by', 'قدم بواسطة', 15),
                ('reviewed_by', 'راجع بواسطة', 15),
                ('reviewed_at', 'تاريخ المراجعة', 20),
                ('payment_date', 'تاريخ الدفع', 15),
            ]
            data = []
            for c in queryset:
                data.append({
                    'claim_number': c.claim_number,
                    'policy_number': c.policy.policy_number if c.policy else '',
                    'policy_name': c.policy.policy_name if c.policy else '',
                    'claim_type': c.get_claim_type_display(),
                    'incident_date': str(c.incident_date),
                    'claimed_amount': str(c.claimed_amount),
                    'approved_amount': str(c.approved_amount),
                    'status': c.get_status_display(),
                    'submitted_by': c.submitted_by.username if c.submitted_by else '',
                    'reviewed_by': c.reviewed_by.username if c.reviewed_by else '',
                    'reviewed_at': str(c.reviewed_at) if c.reviewed_at else '',
                    'payment_date': str(c.payment_date) if c.payment_date else '',
                })
            return export_to_excel(data, columns, 'طلبات التعويض', 'insurance_claims.xlsx')

        elif export_type == 'pensions':
            queryset = PensionRecord.objects.select_related('employee__department').order_by('-created_at')
            columns = [
                ('employee_number', 'رقم الموظف', 15),
                ('employee_name', 'اسم الموظف', 30),
                ('department', 'القسم', 20),
                ('pension_scheme', 'نظام المعاش', 25),
                ('contribution_type', 'نوع المساهمة', 15),
                ('monthly_contribution', 'المساهمة الشهرية', 15),
                ('employer_contribution', 'مساهمة صاحب العمل', 18),
                ('employee_contribution', 'مساهمة الموظف', 15),
                ('total_contributions', 'إجمالي المساهمات', 18),
                ('status', 'الحالة', 12),
                ('start_date', 'تاريخ البداية', 15),
                ('end_date', 'تاريخ النهاية', 15),
            ]
            data = []
            for r in queryset:
                data.append({
                    'employee_number': r.employee.employee_number if r.employee else '',
                    'employee_name': r.employee.full_name if r.employee else '',
                    'department': r.employee.department.name if r.employee and r.employee.department else '',
                    'pension_scheme': r.pension_scheme,
                    'contribution_type': r.get_contribution_type_display(),
                    'monthly_contribution': str(r.monthly_contribution),
                    'employer_contribution': str(r.employer_contribution),
                    'employee_contribution': str(r.employee_contribution),
                    'total_contributions': str(r.total_contributions),
                    'status': r.get_status_display(),
                    'start_date': str(r.start_date),
                    'end_date': str(r.end_date) if r.end_date else '',
                })
            return export_to_excel(data, columns, 'سجلات المعاشات', 'pension_records.xlsx')

        else:
            return Response(
                {'error': 'نوع التصدير غير صالح (policies, claims, or pensions)'},
                status=status.HTTP_400_BAD_REQUEST,
            )
