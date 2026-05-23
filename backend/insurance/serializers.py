"""
Serializers for the Insurance & Pension module.
Handles InsurancePolicy, InsuranceClaim, PensionRecord, and PensionPayment
data transformation.
"""

from rest_framework import serializers
from .models import (
    InsurancePolicy,
    InsuranceClaim,
    PensionRecord,
    PensionPayment,
)


# =============================================
# Insurance Policy Serializers
# =============================================

class InsurancePolicyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing insurance policies."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    insurance_type_display = serializers.CharField(source='get_insurance_type_display', read_only=True)
    premium_frequency_display = serializers.CharField(source='get_premium_frequency_display', read_only=True)
    insured_entity_display = serializers.CharField(source='get_insured_entity_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = InsurancePolicy
        fields = (
            'id', 'policy_number', 'policy_name', 'insurance_provider',
            'insurance_type', 'insurance_type_display', 'coverage_amount',
            'premium_amount', 'premium_frequency', 'premium_frequency_display',
            'start_date', 'end_date', 'status', 'status_display',
            'insured_entity', 'insured_entity_display', 'related_entity_id',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class InsurancePolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an insurance policy."""

    class Meta:
        model = InsurancePolicy
        fields = (
            'policy_number', 'policy_name', 'insurance_provider',
            'insurance_type', 'coverage_amount', 'premium_amount',
            'premium_frequency', 'start_date', 'end_date', 'status',
            'insured_entity', 'related_entity_id', 'notes',
        )

    def validate(self, attrs):
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class InsurancePolicyDetailSerializer(InsurancePolicyListSerializer):
    """Detailed insurance policy serializer with claims count."""

    claims_count = serializers.SerializerMethodField()

    class Meta(InsurancePolicyListSerializer.Meta):
        fields = InsurancePolicyListSerializer.Meta.fields + ('claims_count',)

    def get_claims_count(self, obj):
        return obj.claims.count()


# =============================================
# Insurance Claim Serializers
# =============================================

class InsuranceClaimListSerializer(serializers.ModelSerializer):
    """Serializer for listing insurance claims."""

    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    policy_name = serializers.CharField(source='policy.policy_name', read_only=True)
    claim_type_display = serializers.CharField(source='get_claim_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True, default=None)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, default=None)

    class Meta:
        model = InsuranceClaim
        fields = (
            'id', 'claim_number', 'policy', 'policy_number', 'policy_name',
            'claim_type', 'claim_type_display', 'incident_date', 'description',
            'claimed_amount', 'approved_amount', 'status', 'status_display',
            'submitted_by', 'submitted_by_name', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'payment_date', 'documents', 'notes',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class InsuranceClaimSubmitSerializer(serializers.ModelSerializer):
    """Serializer for submitting an insurance claim."""

    class Meta:
        model = InsuranceClaim
        fields = (
            'claim_number', 'policy', 'claim_type', 'incident_date',
            'description', 'claimed_amount', 'documents', 'notes',
        )

    def validate_claimed_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ المطلوب يجب أن يكون أكبر من صفر')
        return value


class InsuranceClaimReviewSerializer(serializers.Serializer):
    """Serializer for reviewing (approve/reject) an insurance claim."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    approved_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        help_text='المبلغ المعتمد (مطلوب عند الموافقة)',
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Pension Record Serializers
# =============================================

class PensionRecordListSerializer(serializers.ModelSerializer):
    """Serializer for listing pension records."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True, default=None)
    contribution_type_display = serializers.CharField(source='get_contribution_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PensionRecord
        fields = (
            'id', 'employee', 'employee_name', 'employee_number',
            'department_name', 'pension_scheme', 'contribution_type',
            'contribution_type_display', 'monthly_contribution',
            'employer_contribution', 'employee_contribution',
            'start_date', 'end_date', 'status', 'status_display',
            'total_contributions', 'last_contribution_date',
            'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class PensionRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a pension record."""

    class Meta:
        model = PensionRecord
        fields = (
            'employee', 'pension_scheme', 'contribution_type',
            'monthly_contribution', 'employer_contribution',
            'employee_contribution', 'start_date', 'end_date',
            'status', 'total_contributions', 'last_contribution_date', 'notes',
        )

    def validate(self, attrs):
        if attrs.get('monthly_contribution', 0) < 0:
            raise serializers.ValidationError('المساهمة الشهرية يجب أن تكون صفر أو أكبر')
        return attrs


class PensionRecordDetailSerializer(PensionRecordListSerializer):
    """Detailed pension record serializer with payments count."""

    payments_count = serializers.SerializerMethodField()

    class Meta(PensionRecordListSerializer.Meta):
        fields = PensionRecordListSerializer.Meta.fields + ('payments_count',)

    def get_payments_count(self, obj):
        return obj.payments.count()


# =============================================
# Pension Payment Serializers
# =============================================

class PensionPaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing pension payments."""

    pension_scheme = serializers.CharField(source='pension_record.pension_scheme', read_only=True)
    employee_name = serializers.CharField(source='pension_record.employee.full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PensionPayment
        fields = (
            'id', 'pension_record', 'pension_scheme', 'employee_name',
            'amount', 'payment_date', 'month', 'year', 'payment_method',
            'payment_method_display', 'reference_number', 'status',
            'status_display', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class PensionPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a pension payment."""

    class Meta:
        model = PensionPayment
        fields = (
            'pension_record', 'amount', 'payment_date',
            'month', 'year', 'payment_method', 'reference_number',
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value

    def validate(self, attrs):
        if attrs['month'] < 1 or attrs['month'] > 12:
            raise serializers.ValidationError('الشهر يجب أن يكون بين 1 و 12')
        return attrs


# =============================================
# Insurance Stats Serializer
# =============================================

class InsuranceStatsSerializer(serializers.Serializer):
    """Serializer for Insurance & Pension dashboard statistics."""

    total_policies = serializers.IntegerField()
    active_policies = serializers.IntegerField()
    total_premiums = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_claims = serializers.IntegerField()
    total_claims_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pension_contributions = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_pension_records = serializers.IntegerField()
    pending_pension_payments = serializers.IntegerField()
