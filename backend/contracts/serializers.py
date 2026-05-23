"""
Serializers for the Contracts module.
Handles Contract, ContractMilestone, and ContractPayment data.
"""

from rest_framework import serializers
from .models import Contract, ContractMilestone, ContractPayment


# =============================================
# Contract Serializers
# =============================================

class ContractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing contracts."""

    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default=None)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default=None)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    responsible_person_name = serializers.CharField(source='responsible_person.username', read_only=True, default=None)
    remaining_days = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    milestones_count = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            'id', 'contract_number', 'title', 'title_en', 'contract_type', 'contract_type_display',
            'customer', 'customer_name', 'supplier', 'supplier_name',
            'project', 'project_name',
            'start_date', 'end_date', 'value', 'currency', 'vat_inclusive',
            'status', 'status_display', 'remaining_days', 'is_expired',
            'responsible_person', 'responsible_person_name',
            'milestones_count', 'total_paid',
            'is_active', 'created_at',
        )
        read_only_fields = ('id', 'contract_number', 'remaining_days', 'is_expired', 'created_at')

    def get_remaining_days(self, obj):
        return obj.remaining_days

    def get_milestones_count(self, obj):
        return obj.milestones.count()

    def get_total_paid(self, obj):
        from django.db.models import Sum
        total = obj.contract_payments.aggregate(
            total=Sum('paid_amount', default=0)
        )
        return total['total']


class ContractCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a contract."""

    class Meta:
        model = Contract
        fields = (
            'title', 'title_en', 'contract_type', 'customer', 'supplier', 'project',
            'start_date', 'end_date', 'value', 'currency', 'vat_inclusive',
            'payment_terms', 'description', 'terms_conditions',
            'renewal_reminder_days', 'signed_date', 'signed_by',
            'responsible_person', 'notes', 'status',
        )


class ContractUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a contract."""

    class Meta:
        model = Contract
        fields = (
            'title', 'title_en', 'contract_type', 'customer', 'supplier', 'project',
            'start_date', 'end_date', 'value', 'currency', 'vat_inclusive',
            'payment_terms', 'description', 'terms_conditions',
            'renewal_reminder_days', 'signed_date', 'signed_by',
            'responsible_person', 'status', 'is_active', 'notes',
        )


class ContractDetailSerializer(ContractListSerializer):
    """Detailed contract serializer with milestones and payments."""

    class Meta(ContractListSerializer.Meta):
        fields = ContractListSerializer.Meta.fields + (
            'signed_date', 'signed_by', 'payment_terms', 'description',
            'terms_conditions', 'renewal_reminder_days',
            'notes', 'updated_at',
        )


# =============================================
# ContractMilestone Serializers
# =============================================

class ContractMilestoneListSerializer(serializers.ModelSerializer):
    """Serializer for listing contract milestones."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContractMilestone
        fields = (
            'id', 'contract', 'title', 'description', 'due_date',
            'amount', 'status', 'status_display', 'completed_date', 'notes',
        )
        read_only_fields = ('id',)


class ContractMilestoneCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a milestone."""

    class Meta:
        model = ContractMilestone
        fields = ('contract', 'title', 'description', 'due_date', 'amount', 'status', 'notes')


class ContractMilestoneUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a milestone."""

    class Meta:
        model = ContractMilestone
        fields = ('title', 'description', 'due_date', 'amount', 'status', 'completed_date', 'notes')


# =============================================
# ContractPayment Serializers
# =============================================

class ContractPaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing contract payments."""

    contract_title = serializers.CharField(source='contract.title', read_only=True)
    milestone_title = serializers.CharField(source='milestone.title', read_only=True, default=None)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = ContractPayment
        fields = (
            'id', 'contract', 'contract_title', 'milestone', 'milestone_title',
            'amount', 'due_date', 'paid_date', 'payment_status', 'payment_status_display',
            'paid_amount', 'remaining_amount', 'payment_method', 'reference',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_remaining_amount(self, obj):
        return obj.amount - obj.paid_amount


class ContractPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a contract payment."""

    class Meta:
        model = ContractPayment
        fields = ('contract', 'milestone', 'amount', 'due_date', 'payment_method', 'reference', 'notes')


class ContractPaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a contract payment."""

    class Meta:
        model = ContractPayment
        fields = (
            'milestone', 'due_date', 'paid_date', 'payment_status',
            'paid_amount', 'payment_method', 'reference', 'notes',
        )


# =============================================
# Contract Status Change Serializer
# =============================================

class ContractChangeStatusSerializer(serializers.Serializer):
    """Serializer for changing contract status."""

    new_status = serializers.ChoiceField(
        choices=Contract.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


class ContractRenewSerializer(serializers.Serializer):
    """Serializer for renewing a contract."""

    new_end_date = serializers.DateField(help_text='تاريخ الانتهاء الجديد')
    new_value = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        help_text='القيمة الجديدة (اختياري)',
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Contract Stats Serializer
# =============================================

class ContractStatsSerializer(serializers.Serializer):
    """Serializer for contracts dashboard statistics."""

    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    expired_contracts = serializers.IntegerField()
    expiring_soon = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_payments = serializers.IntegerField()
    completed_milestones = serializers.IntegerField()
    pending_milestones = serializers.IntegerField()
