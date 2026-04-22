"""
API views for the Internal Audit & Compliance module.
Handles AuditPlans, AuditFindings, AuditEvidence, AuditActions,
ComplianceChecks, stats, and export.
"""

from decimal import Decimal

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse

from .models import (
    AuditPlan,
    AuditFinding,
    AuditEvidence,
    AuditAction,
    ComplianceCheck,
)
from .serializers import (
    AuditPlanListSerializer,
    AuditPlanCreateSerializer,
    AuditPlanDetailSerializer,
    AuditFindingListSerializer,
    AuditFindingCreateSerializer,
    AuditFindingDetailSerializer,
    AuditFindingResolveSerializer,
    AuditEvidenceListSerializer,
    AuditEvidenceCreateSerializer,
    AuditActionListSerializer,
    AuditActionCreateSerializer,
    AuditActionCompleteSerializer,
    ComplianceCheckListSerializer,
    ComplianceCheckCreateSerializer,
    ComplianceCheckPerformSerializer,
    InternalAuditStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Internal Audit Stats View
# =============================================

class InternalAuditStatsView(views.APIView):
    """GET: Internal Audit statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_plans = AuditPlan.objects.count()
        open_findings = AuditFinding.objects.filter(
            status__in=('open', 'in_progress')
        ).count()
        pending_actions = AuditAction.objects.filter(
            status__in=('pending', 'in_progress')
        ).count()

        # Compliance rate: (compliant + partially_compliant) / total * 100
        total_compliance = ComplianceCheck.objects.count()
        compliant_count = ComplianceCheck.objects.filter(
            status__in=('compliant', 'partially_compliant')
        ).count()
        compliance_rate = Decimal('0.00')
        if total_compliance > 0:
            compliance_rate = (Decimal(compliant_count) / Decimal(total_compliance)) * Decimal('100.00')
            compliance_rate = compliance_rate.quantize(Decimal('0.01'))

        total_evidence = AuditEvidence.objects.count()
        completed_actions = AuditAction.objects.filter(status='completed').count()
        overdue_actions = AuditAction.objects.filter(status='overdue').count()
        critical_findings = AuditFinding.objects.filter(severity='critical').count()

        stats = {
            'total_plans': total_plans,
            'open_findings': open_findings,
            'pending_actions': pending_actions,
            'compliance_rate': compliance_rate,
            'total_evidence': total_evidence,
            'completed_actions': completed_actions,
            'overdue_actions': overdue_actions,
            'critical_findings': critical_findings,
        }

        serializer = InternalAuditStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Audit Plan Views
# =============================================

class AuditPlanListView(generics.ListCreateAPIView):
    """GET: List audit plans. POST: Create audit plan (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'fiscal_year', 'audit_type', 'status', 'risk_level', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AuditPlanCreateSerializer
        return AuditPlanListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = AuditPlan.objects.select_related('department', 'lead_auditor', 'created_by')
        # Filter by status
        plan_status = self.request.query_params.get('status')
        if plan_status:
            queryset = queryset.filter(status=plan_status)
        # Filter by audit_type
        audit_type = self.request.query_params.get('audit_type')
        if audit_type:
            queryset = queryset.filter(audit_type=audit_type)
        # Filter by fiscal_year
        fiscal_year = self.request.query_params.get('fiscal_year')
        if fiscal_year:
            queryset = queryset.filter(fiscal_year=fiscal_year)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء خطة التدقيق بنجاح',
            'plan': AuditPlanDetailSerializer(plan).data,
        }, status=status.HTTP_201_CREATED)


class AuditPlanDetailView(generics.RetrieveAPIView):
    """GET: Audit plan details."""

    serializer_class = AuditPlanDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuditPlan.objects.select_related('department', 'lead_auditor', 'created_by')


class AuditPlanCompleteView(views.APIView):
    """POST: Complete an audit plan (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            plan = AuditPlan.objects.select_related('lead_auditor').get(pk=pk)
        except AuditPlan.DoesNotExist:
            return Response(
                {'error': 'خطة التدقيق غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if plan.status not in ('draft', 'in_progress'):
            return Response(
                {'error': 'لا يمكن إكمال خطة تدقيق ليست في حالة مسودة أو قيد التنفيذ'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan.status = 'completed'
        plan.end_date = timezone.now().date()
        plan.save()

        return Response({
            'message': 'تم إكمال خطة التدقيق بنجاح',
            'plan': AuditPlanDetailSerializer(plan).data,
        })


# =============================================
# Audit Finding Views
# =============================================

class AuditFindingListView(generics.ListAPIView):
    """GET: List audit findings with filtering."""

    serializer_class = AuditFindingListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['finding_number', 'title', 'description']
    ordering_fields = ['finding_number', 'severity', 'status', 'category', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = AuditFinding.objects.select_related(
            'audit_plan', 'responsible_person', 'resolved_by'
        )
        # Filter by audit plan
        plan = self.request.query_params.get('plan')
        if plan:
            queryset = queryset.filter(audit_plan_id=plan)
        # Filter by status
        finding_status = self.request.query_params.get('status')
        if finding_status:
            queryset = queryset.filter(status=finding_status)
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class AuditFindingDetailView(generics.RetrieveAPIView):
    """GET: Audit finding details."""

    serializer_class = AuditFindingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuditFinding.objects.select_related(
            'audit_plan', 'responsible_person', 'resolved_by'
        )


class AuditFindingCreateView(generics.CreateAPIView):
    """POST: Create an audit finding (admin only)."""

    serializer_class = AuditFindingCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        finding = serializer.save()
        return Response({
            'message': 'تم إنشاء ملاحظة التدقيق بنجاح',
            'finding': AuditFindingDetailSerializer(finding).data,
        }, status=status.HTTP_201_CREATED)


class AuditFindingResolveView(views.APIView):
    """POST: Resolve/close an audit finding (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            finding = AuditFinding.objects.select_related('audit_plan', 'responsible_person').get(pk=pk)
        except AuditFinding.DoesNotExist:
            return Response(
                {'error': 'ملاحظة التدقيق غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AuditFindingResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        if finding.status in ('resolved', 'closed', 'accepted'):
            return Response(
                {'error': 'ملاحظة التدقيق محسولة أو مغلقة مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        finding.status = new_status
        finding.resolved_at = timezone.now()
        finding.resolved_by = request.user
        finding.save()

        return Response({
            'message': 'تم تحديث حالة ملاحظة التدقيق بنجاح',
            'finding': AuditFindingDetailSerializer(finding).data,
        })


# =============================================
# Audit Evidence Views
# =============================================

class AuditEvidenceListView(generics.ListAPIView):
    """GET: List audit evidence with filtering."""

    serializer_class = AuditEvidenceListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['evidence_type', 'collected_at', 'created_at']
    ordering = ['-collected_at']

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = AuditEvidence.objects.select_related('finding', 'collected_by')
        # Filter by finding
        finding = self.request.query_params.get('finding')
        if finding:
            queryset = queryset.filter(finding_id=finding)
        # Filter by evidence_type
        evidence_type = self.request.query_params.get('evidence_type')
        if evidence_type:
            queryset = queryset.filter(evidence_type=evidence_type)
        return queryset


class AuditEvidenceCreateView(generics.CreateAPIView):
    """POST: Create audit evidence (admin only)."""

    serializer_class = AuditEvidenceCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence = serializer.save(collected_by=request.user)
        return Response({
            'message': 'تم إضافة دليل التدقيق بنجاح',
            'evidence': AuditEvidenceListSerializer(evidence).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Audit Action Views
# =============================================

class AuditActionListView(generics.ListAPIView):
    """GET: List audit actions with filtering."""

    serializer_class = AuditActionListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action_number', 'description']
    ordering_fields = ['action_number', 'priority', 'status', 'due_date', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = AuditAction.objects.select_related(
            'finding__audit_plan', 'assigned_to', 'verified_by'
        )
        # Filter by finding
        finding = self.request.query_params.get('finding')
        if finding:
            queryset = queryset.filter(finding_id=finding)
        # Filter by status
        action_status = self.request.query_params.get('status')
        if action_status:
            queryset = queryset.filter(status=action_status)
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset


class AuditActionDetailView(generics.RetrieveAPIView):
    """GET: Audit action details."""

    serializer_class = AuditActionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuditAction.objects.select_related(
            'finding__audit_plan', 'assigned_to', 'verified_by'
        )


class AuditActionCreateView(generics.CreateAPIView):
    """POST: Create an audit action (admin only)."""

    serializer_class = AuditActionCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.save()
        return Response({
            'message': 'تم إنشاء الإجراء التصحيحي بنجاح',
            'action': AuditActionListSerializer(action).data,
        }, status=status.HTTP_201_CREATED)


class AuditActionCompleteView(views.APIView):
    """POST: Complete/verify an audit action (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            action = AuditAction.objects.select_related('finding', 'assigned_to').get(pk=pk)
        except AuditAction.DoesNotExist:
            return Response(
                {'error': 'الإجراء التصحيحي غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AuditActionCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        evidence = serializer.validated_data.get('evidence_of_completion', '')
        notes = serializer.validated_data.get('notes', '')

        if action.status in ('completed', 'cancelled'):
            return Response(
                {'error': 'الإجراء التصحيحي مكتمل أو ملغي مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action.status = new_status
        if new_status == 'completed':
            action.completion_date = timezone.now().date()
            action.evidence_of_completion = evidence or action.evidence_of_completion
            action.verified_by = request.user
            action.verified_at = timezone.now()

        if notes:
            action.notes = (action.notes + '\n' + notes).strip() if action.notes else notes

        action.save()

        return Response({
            'message': 'تم تحديث حالة الإجراء التصحيحي بنجاح',
            'action': AuditActionListSerializer(action).data,
        })


# =============================================
# Compliance Check Views
# =============================================

class ComplianceCheckListView(generics.ListCreateAPIView):
    """GET: List compliance checks. POST: Create compliance check (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'regulation', 'description']
    ordering_fields = ['name', 'frequency', 'status', 'next_check', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComplianceCheckCreateSerializer
        return ComplianceCheckListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ComplianceCheck.objects.select_related('department', 'responsible')
        # Filter by status
        check_status = self.request.query_params.get('status')
        if check_status:
            queryset = queryset.filter(status=check_status)
        # Filter by frequency
        frequency = self.request.query_params.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check = serializer.save()
        return Response({
            'message': 'تم إنشاء فحص التوافق بنجاح',
            'check': ComplianceCheckListSerializer(check).data,
        }, status=status.HTTP_201_CREATED)


class ComplianceCheckDetailView(generics.RetrieveAPIView):
    """GET: Compliance check details."""

    serializer_class = ComplianceCheckListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ComplianceCheck.objects.select_related('department', 'responsible')


class ComplianceCheckPerformView(views.APIView):
    """POST: Record a compliance check result (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            check = ComplianceCheck.objects.select_related('department', 'responsible').get(pk=pk)
        except ComplianceCheck.DoesNotExist:
            return Response(
                {'error': 'فحص التوافق غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ComplianceCheckPerformSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        check_status = serializer.validated_data['status']
        findings = serializer.validated_data.get('findings', '')

        check.status = check_status
        check.last_check = timezone.now().date()
        if findings:
            check.findings = findings
        check.save()

        return Response({
            'message': 'تم تسجيل نتيجة فحص التوافق بنجاح',
            'check': ComplianceCheckListSerializer(check).data,
        })


# =============================================
# Internal Audit Export View
# =============================================

class InternalAuditExportView(views.APIView):
    """GET: Export audit findings and actions to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        queryset = AuditFinding.objects.select_related(
            'audit_plan', 'responsible_person'
        ).order_by('audit_plan__name', 'finding_number')

        # Filter by audit plan
        plan = self.request.query_params.get('plan')
        if plan:
            queryset = queryset.filter(audit_plan_id=plan)

        # Filter by status
        finding_status = self.request.query_params.get('status')
        if finding_status:
            queryset = queryset.filter(status=finding_status)

        columns = [
            ('plan_name', 'خطة التدقيق', 25),
            ('finding_number', 'رقم الملاحظة', 15),
            ('title', 'العنوان', 30),
            ('severity', 'الخطورة', 12),
            ('category', 'التصنيف', 15),
            ('status', 'الحالة', 15),
            ('responsible', 'المسؤول', 20),
            ('due_date', 'تاريخ الاستحقاق', 15),
            ('recommendation', 'التوصية', 40),
            ('actions_count', 'عدد الإجراءات', 12),
            ('resolved_at', 'تاريخ الحل', 15),
        ]
        data = []
        for f in queryset:
            data.append({
                'plan_name': f.audit_plan.name if f.audit_plan else '',
                'finding_number': f.finding_number,
                'title': f.title,
                'severity': f.get_severity_display(),
                'category': f.get_category_display(),
                'status': f.get_status_display(),
                'responsible': f.responsible_person.username if f.responsible_person else '',
                'due_date': str(f.due_date) if f.due_date else '',
                'recommendation': f.recommendation[:200] if f.recommendation else '',
                'actions_count': f.actions.count(),
                'resolved_at': str(f.resolved_at.date()) if f.resolved_at else '',
            })
        return export_to_excel(data, columns, 'تقرير التدقيق الداخلي', 'internal_audit.xlsx')
