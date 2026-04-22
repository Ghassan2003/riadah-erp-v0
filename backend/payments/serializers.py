"""
Serializers for the Payments module.
Handles PaymentAccount, FinancialTransaction, Cheque, and Reconciliation data transformation.
"""

from rest_framework import serializers
from .models import (
    PaymentAccount,
    FinancialTransaction,
    Cheque,
    Reconciliation,
)


# =============================================
# PaymentAccount Serializers
# =============================================

class PaymentAccountListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payment accounts."""

    account_type_display = serializers.CharField(
        source='get_account_type_display', read_only=True
    )
    transaction_count = serializers.SerializerMethodField()

    class Meta:
        model = PaymentAccount
        fields = (
            'id', 'account_name', 'account_type', 'account_type_display',
            'bank_name', 'account_number', 'currency', 'current_balance',
            'is_default', 'is_active', 'created_at', 'transaction_count',
        )
        read_only_fields = ('id', 'current_balance', 'created_at', 'transaction_count')

    def get_transaction_count(self, obj):
        return obj.transactions.count()


class PaymentAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payment account."""

    class Meta:
        model = PaymentAccount
        fields = (
            'account_name', 'account_type', 'bank_name', 'account_number',
            'iban', 'currency', 'is_default',
        )

    def validate(self, attrs):
        if attrs.get('account_type') == 'bank_account' and not attrs.get('bank_name'):
            raise serializers.ValidationError('اسم البنك مطلوب للحسابات البنكية')
        if attrs.get('account_type') == 'bank_account' and not attrs.get('account_number'):
            raise serializers.ValidationError('رقم الحساب مطلوب للحسابات البنكية')
        return attrs


class PaymentAccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payment account info."""

    class Meta:
        model = PaymentAccount
        fields = (
            'account_name', 'account_type', 'bank_name', 'account_number',
            'iban', 'currency', 'is_default', 'is_active',
        )


class PaymentAccountDetailSerializer(PaymentAccountListSerializer):
    """Detailed payment account serializer."""

    recent_transactions = serializers.SerializerMethodField()

    class Meta(PaymentAccountListSerializer.Meta):
        fields = PaymentAccountListSerializer.Meta.fields + (
            'iban', 'updated_at', 'recent_transactions',
        )

    def get_recent_transactions(self, obj):
        transactions = obj.transactions.order_by('-created_at')[:10]
        return FinancialTransactionListSerializer(transactions, many=True).data


# =============================================
# FinancialTransaction Serializers
# =============================================

class FinancialTransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing financial transactions."""

    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    reference_type_display = serializers.CharField(
        source='get_reference_type_display', read_only=True, default=None
    )
    account_name = serializers.CharField(
        source='account.account_name', read_only=True, default=None
    )
    to_account_name = serializers.CharField(
        source='to_account.account_name', read_only=True, default=None
    )
    customer_name = serializers.CharField(
        source='customer.name', read_only=True, default=None
    )
    supplier_name = serializers.CharField(
        source='supplier.name', read_only=True, default=None
    )
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True, default=None
    )

    class Meta:
        model = FinancialTransaction
        fields = (
            'id', 'transaction_number', 'transaction_type', 'transaction_type_display',
            'account', 'account_name', 'to_account', 'to_account_name',
            'amount', 'currency', 'reference_type', 'reference_type_display',
            'reference_id', 'customer', 'customer_name', 'supplier', 'supplier_name',
            'description', 'transaction_date', 'payment_method', 'payment_method_display',
            'cheque_number', 'status', 'status_display', 'created_by', 'created_by_name',
            'created_at',
        )
        read_only_fields = ('id', 'transaction_number', 'created_at')


class FinancialTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a financial transaction."""

    class Meta:
        model = FinancialTransaction
        fields = (
            'transaction_type', 'account', 'to_account', 'amount', 'currency',
            'reference_type', 'reference_id', 'customer', 'supplier',
            'description', 'transaction_date', 'payment_method', 'cheque_number',
            'status', 'created_by',
        )

    def validate(self, attrs):
        trx_type = attrs.get('transaction_type')
        account = attrs.get('account')
        to_account = attrs.get('to_account')

        if trx_type in ('receipt', 'payment', 'adjustment') and not account:
            raise serializers.ValidationError('الحساب مطلوب لهذا النوع من العمليات')
        if trx_type == 'transfer':
            if not account:
                raise serializers.ValidationError('الحساب المصدر مطلوب للتحويل')
            if not to_account:
                raise serializers.ValidationError('حساب المستلم مطلوب للتحويل')
            if account == to_account:
                raise serializers.ValidationError('لا يمكن التحويل إلى نفس الحساب')
        if attrs.get('payment_method') == 'cheque' and not attrs.get('cheque_number'):
            raise serializers.ValidationError('رقم الشيك مطلوب عند الدفع بالشيك')
        return attrs


class FinancialTransactionDetailSerializer(FinancialTransactionListSerializer):
    """Detailed financial transaction serializer."""

    account_info = PaymentAccountListSerializer(
        source='account', read_only=True
    )
    to_account_info = PaymentAccountListSerializer(
        source='to_account', read_only=True
    )

    class Meta(FinancialTransactionListSerializer.Meta):
        fields = FinancialTransactionListSerializer.Meta.fields + (
            'updated_at', 'account_info', 'to_account_info',
        )


# =============================================
# Cheque Serializers
# =============================================

class ChequeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing cheques."""

    cheque_type_display = serializers.CharField(
        source='get_cheque_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    customer_name = serializers.CharField(
        source='customer.name', read_only=True, default=None
    )
    supplier_name = serializers.CharField(
        source='supplier.name', read_only=True, default=None
    )

    class Meta:
        model = Cheque
        fields = (
            'id', 'cheque_number', 'bank_name', 'branch_name', 'amount',
            'due_date', 'payer_name', 'payee_name', 'cheque_type',
            'cheque_type_display', 'status', 'status_display',
            'transaction', 'customer', 'customer_name', 'supplier', 'supplier_name',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ChequeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a cheque."""

    class Meta:
        model = Cheque
        fields = (
            'cheque_number', 'bank_name', 'branch_name', 'amount',
            'due_date', 'payer_name', 'payee_name', 'cheque_type',
            'status', 'transaction', 'customer', 'supplier', 'notes',
        )

    def validate_cheque_number(self, value):
        if Cheque.objects.filter(cheque_number=value).exists():
            raise serializers.ValidationError('رقم الشيك موجود مسبقاً')
        return value


class ChequeDetailSerializer(ChequeListSerializer):
    """Detailed cheque serializer."""

    class Meta(ChequeListSerializer.Meta):
        fields = ChequeListSerializer.Meta.fields + ('updated_at',)


class ChequeStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating cheque status."""

    action = serializers.ChoiceField(
        choices=('deposit', 'clear', 'bounce', 'cancel'),
        error_messages={'invalid_choice': 'إجراء غير صالح (deposit/clear/bounce/cancel)'},
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Reconciliation Serializers
# =============================================

class ReconciliationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reconciliations."""

    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    account_name = serializers.CharField(
        source='account.account_name', read_only=True
    )
    reconciled_by_name = serializers.CharField(
        source='reconciled_by.username', read_only=True, default=None
    )

    class Meta:
        model = Reconciliation
        fields = (
            'id', 'reconciliation_number', 'account', 'account_name',
            'period_start', 'period_end', 'system_balance', 'actual_balance',
            'status', 'status_display', 'reconciled_by', 'reconciled_by_name',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'reconciliation_number', 'created_at')


class ReconciliationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a reconciliation."""

    class Meta:
        model = Reconciliation
        fields = (
            'account', 'period_start', 'period_end',
            'system_balance', 'actual_balance', 'notes',
        )

    def validate(self, attrs):
        if attrs['period_start'] > attrs['period_end']:
            raise serializers.ValidationError('تاريخ بداية الفترة يجب أن يكون قبل تاريخ النهاية')
        return attrs


class ReconciliationDetailSerializer(ReconciliationListSerializer):
    """Detailed reconciliation serializer with difference property."""

    difference = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta(ReconciliationListSerializer.Meta):
        fields = ReconciliationListSerializer.Meta.fields + (
            'updated_at', 'difference',
        )


# =============================================
# Payment Stats Serializer
# =============================================

class PaymentStatsSerializer(serializers.Serializer):
    """Serializer for payments dashboard statistics."""

    total_accounts = serializers.IntegerField()
    active_accounts = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_receipts = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_payments = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_transactions = serializers.IntegerField()
    pending_cheques = serializers.IntegerField()
    bounced_cheques = serializers.IntegerField()
    total_transactions_count = serializers.IntegerField()
    month_receipts = serializers.DecimalField(max_digits=14, decimal_places=2)
    month_payments = serializers.DecimalField(max_digits=14, decimal_places=2)
