"""
Serializers for the Internal Audit & Compliance module.
Handles AuditPlan, AuditFinding, AuditEvidence, AuditAction, and ComplianceCheck
data transformation.
"""

from rest_framework import serializers
from .models import (
    AuditPlan,
    AuditFinding,
    AuditEvidence,
    AuditAction,
    ComplianceCheck,
)


# =============================================
# Audit Plan Serializers
# =============================================

class AuditPlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing audit plans."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    audit_type_display = serializers.CharField(source='get_audit_type_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    lead_auditor_name = serializers.CharField(source='lead_auditor.username', read_only=True, default=None)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    findings_count = serializers.SerializerMethodField()

    class Meta:
        model = AuditPlan
        fields = (
            'id', 'name', 'description', 'fiscal_year', 'department',
            'department_name', 'audit_type', 'audit_type_display', 'status',
            'status_display', 'start_date', 'end_date', 'lead_auditor',
            'lead_auditor_name', 'risk_level', 'risk_level_display',
            'budget_hours', 'actual_hours', 'findings_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_findings_count(self, obj):
        return obj.findings.count()


class AuditPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an audit plan."""

    class Meta:
        model = AuditPlan
        fields = (
            'name', 'description', 'fiscal_year', 'department', 'audit_type',
            'status', 'start_date', 'end_date', 'lead_auditor', 'team_members',
            'scope', 'objectives', 'risk_level', 'budget_hours',
        )

    def validate(self, attrs):
        if 'end_date' in attrs and attrs['end_date']:
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class AuditPlanDetailSerializer(AuditPlanListSerializer):
    """Detailed audit plan serializer with full information."""

    open_findings_count = serializers.SerializerMethodField()
    resolved_findings_count = serializers.SerializerMethodField()

    class Meta(AuditPlanListSerializer.Meta):
        fields = AuditPlanListSerializer.Meta.fields + (
            'team_members', 'scope', 'objectives',
            'open_findings_count', 'resolved_findings_count',
        )

    def get_open_findings_count(self, obj):
        return obj.findings.filter(status__in=('open', 'in_progress')).count()

    def get_resolved_findings_count(self, obj):
        return obj.findings.filter(status__in=('resolved', 'closed', 'accepted')).count()


# =============================================
# Audit Finding Serializers
# =============================================

class AuditFindingListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit findings."""

    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    audit_plan_name = serializers.CharField(source='audit_plan.name', read_only=True)
    responsible_person_name = serializers.CharField(source='responsible_person.username', read_only=True, default=None)
    actions_count = serializers.SerializerMethodField()

    class Meta:
        model = AuditFinding
        fields = (
            'id', 'audit_plan', 'audit_plan_name', 'finding_number', 'title',
            'description', 'severity', 'severity_display', 'category',
            'category_display', 'status', 'status_display',
            'responsible_person', 'responsible_person_name', 'due_date',
            'resolved_at', 'resolved_by', 'actions_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_actions_count(self, obj):
        return obj.actions.count()


class AuditFindingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an audit finding."""

    class Meta:
        model = AuditFinding
        fields = (
            'audit_plan', 'finding_number', 'title', 'description', 'severity',
            'category', 'condition', 'criteria', 'cause', 'effect',
            'recommendation', 'status', 'responsible_person', 'due_date',
        )

    def validate(self, attrs):
        if AuditFinding.objects.filter(
            audit_plan=attrs['audit_plan'],
            finding_number=attrs['finding_number'],
        ).exists():
            raise serializers.ValidationError('رقم الملاحظة موجود مسبقاً في نفس خطة التدقيق')
        return attrs


class AuditFindingDetailSerializer(AuditFindingListSerializer):
    """Detailed audit finding serializer with condition/criteria/cause/effect."""

    class Meta(AuditFindingListSerializer.Meta):
        fields = AuditFindingListSerializer.Meta.fields + (
            'condition', 'criteria', 'cause', 'effect', 'recommendation',
        )


class AuditFindingResolveSerializer(serializers.Serializer):
    """Serializer for resolving/closing an audit finding."""

    status = serializers.ChoiceField(
        choices=('resolved', 'closed', 'accepted'),
        error_messages={'invalid_choice': 'حالة غير صالحة (resolved أو closed أو accepted)'},
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Audit Evidence Serializers
# =============================================

class AuditEvidenceListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit evidence."""

    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)
    collected_by_name = serializers.CharField(source='collected_by.username', read_only=True, default=None)
    finding_number = serializers.CharField(source='finding.finding_number', read_only=True)
    finding_title = serializers.CharField(source='finding.title', read_only=True)

    class Meta:
        model = AuditEvidence
        fields = (
            'id', 'finding', 'finding_number', 'finding_title',
            'evidence_type', 'evidence_type_display', 'description',
            'file', 'collected_by', 'collected_by_name', 'collected_at', 'created_at',
        )
        read_only_fields = ('id', 'collected_at', 'created_at')


class AuditEvidenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating audit evidence."""

    class Meta:
        model = AuditEvidence
        fields = ('finding', 'evidence_type', 'description', 'file', 'collected_by')


# =============================================
# Audit Action Serializers
# =============================================

class AuditActionListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit actions."""

    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    finding_number = serializers.CharField(source='finding.finding_number', read_only=True)
    finding_title = serializers.CharField(source='finding.title', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True, default=None)

    class Meta:
        model = AuditAction
        fields = (
            'id', 'finding', 'finding_number', 'finding_title', 'action_number',
            'description', 'assigned_to', 'assigned_to_name', 'priority',
            'priority_display', 'due_date', 'status', 'status_display',
            'completion_date', 'evidence_of_completion', 'verified_by',
            'verified_by_name', 'verified_at', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class AuditActionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an audit action."""

    class Meta:
        model = AuditAction
        fields = (
            'finding', 'action_number', 'description', 'assigned_to',
            'priority', 'due_date', 'status', 'notes',
        )

    def validate(self, attrs):
        if AuditAction.objects.filter(
            finding=attrs['finding'],
            action_number=attrs['action_number'],
        ).exists():
            raise serializers.ValidationError('رقم الإجراء موجود مسبقاً لنفس الملاحظة')
        return attrs


class AuditActionCompleteSerializer(serializers.Serializer):
    """Serializer for completing/verifying an audit action."""

    status = serializers.ChoiceField(
        choices=('completed', 'cancelled'),
        error_messages={'invalid_choice': 'حالة غير صالحة (completed أو cancelled)'},
    )
    evidence_of_completion = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Compliance Check Serializers
# =============================================

class ComplianceCheckListSerializer(serializers.ModelSerializer):
    """Serializer for listing compliance checks."""

    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    responsible_name = serializers.CharField(source='responsible.username', read_only=True, default=None)

    class Meta:
        model = ComplianceCheck
        fields = (
            'id', 'name', 'regulation', 'description', 'department',
            'department_name', 'frequency', 'frequency_display',
            'last_check', 'next_check', 'responsible', 'responsible_name',
            'status', 'status_display', 'findings', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ComplianceCheckCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a compliance check."""

    class Meta:
        model = ComplianceCheck
        fields = (
            'name', 'regulation', 'description', 'department', 'frequency',
            'last_check', 'next_check', 'responsible', 'status', 'findings',
        )


class ComplianceCheckPerformSerializer(serializers.Serializer):
    """Serializer for recording a compliance check result."""

    status = serializers.ChoiceField(
        choices=('compliant', 'partially_compliant', 'non_compliant'),
        error_messages={'invalid_choice': 'حالة غير صالحة (compliant أو partially_compliant أو non_compliant)'},
    )
    findings = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Internal Audit Stats Serializer
# =============================================

class InternalAuditStatsSerializer(serializers.Serializer):
    """Serializer for Internal Audit dashboard statistics."""

    total_plans = serializers.IntegerField()
    open_findings = serializers.IntegerField()
    pending_actions = serializers.IntegerField()
    compliance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_evidence = serializers.IntegerField()
    completed_actions = serializers.IntegerField()
    overdue_actions = serializers.IntegerField()
    critical_findings = serializers.IntegerField()
