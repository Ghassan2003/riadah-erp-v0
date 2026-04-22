"""
Serializers for the Accounting module - Phase 4.
Handles Account, JournalEntry, and Transaction data transformation.
"""

from rest_framework import serializers
from django.db import transaction as db_transaction
from .models import Account, JournalEntry, Transaction, AccountType


# =============================================
# Account Serializers
# =============================================

class AccountListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing accounts."""

    account_type_display = serializers.CharField(
        source='get_account_type_display', read_only=True
    )
    has_children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(
        source='parent.name', read_only=True, default=None
    )

    class Meta:
        model = Account
        fields = (
            'id', 'code', 'name', 'name_en', 'account_type',
            'account_type_display', 'parent', 'parent_name',
            'current_balance', 'is_active', 'has_children',
        )
        read_only_fields = ('id', 'current_balance')

    def get_has_children(self, obj):
        return obj.children.filter(is_active=True).exists()


class AccountDetailSerializer(AccountListSerializer):
    """Detailed account serializer with full info."""

    children = serializers.SerializerMethodField()

    class Meta(AccountListSerializer.Meta):
        fields = AccountListSerializer.Meta.fields + (
            'description', 'children', 'created_at', 'updated_at',
        )

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return AccountListSerializer(children, many=True).data


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new account."""

    class Meta:
        model = Account
        fields = ('code', 'name', 'name_en', 'account_type', 'parent', 'description')

    def validate_code(self, value):
        if Account.objects.filter(code=value).exists():
            raise serializers.ValidationError('رمز الحساب موجود مسبقاً')
        return value


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating account info."""

    class Meta:
        model = Account
        fields = ('name', 'name_en', 'parent', 'description', 'is_active')

    def validate_code(self, value):
        """Prevent duplicate code on update."""
        instance = self.instance
        if Account.objects.filter(code=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError('رمز الحساب موجود مسبقاً')
        return value


# =============================================
# Transaction Serializers
# =============================================

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for individual transactions."""

    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            'id', 'account', 'account_code', 'account_name',
            'transaction_type', 'transaction_type_display',
            'amount', 'description',
        )
        read_only_fields = ('id', 'account_code', 'account_name', 'transaction_type_display')


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions within a journal entry."""

    class Meta:
        model = Transaction
        fields = ('account', 'transaction_type', 'amount', 'description')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value


# =============================================
# Journal Entry Serializers
# =============================================

class JournalEntryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing journal entries."""

    entry_type_display = serializers.CharField(
        source='get_entry_type_display', read_only=True
    )
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True, default=''
    )

    class Meta:
        model = JournalEntry
        fields = (
            'id', 'entry_number', 'description', 'entry_type',
            'entry_type_display', 'entry_date', 'is_posted',
            'total_debit', 'total_credit', 'reference',
            'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'entry_number', 'created_at')

    def get_total_debit(self, obj):
        return sum(t.amount for t in obj.transactions.all() if t.transaction_type == 'debit')

    def get_total_credit(self, obj):
        return sum(t.amount for t in obj.transactions.all() if t.transaction_type == 'credit')


class JournalEntryDetailSerializer(JournalEntryListSerializer):
    """Detailed serializer with transactions."""

    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta(JournalEntryListSerializer.Meta):
        fields = JournalEntryListSerializer.Meta.fields + (
            'transactions', 'updated_at', 'sales_order',
        )


class CreateJournalEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for creating a journal entry with transactions.
    Validates that total debits equal total credits.
    """

    transactions = TransactionCreateSerializer(many=True)

    class Meta:
        model = JournalEntry
        fields = ('description', 'reference', 'entry_date', 'entry_type', 'transactions')

    def validate_transactions(self, value):
        if not value or len(value) < 2:
            raise serializers.ValidationError(
                'يجب أن يحتوي القيد على حركتين ماليتين على الأقل (قيد مزدوج)'
            )
        return value

    def validate(self, attrs):
        transactions = attrs.get('transactions', [])
        total_debit = sum(
            t['amount'] for t in transactions if t['transaction_type'] == 'debit'
        )
        total_credit = sum(
            t['amount'] for t in transactions if t['transaction_type'] == 'credit'
        )

        if total_debit == 0:
            raise serializers.ValidationError('يجب أن يكون هناك حركة مدينة واحدة على الأقل')
        if total_credit == 0:
            raise serializers.ValidationError('يجب أن يكون هناك حركة دائنة واحدة على الأقل')
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f'المجاميع غير متساوية: المدين = {total_debit}، الدائن = {total_credit}'
            )

        return attrs

    @db_transaction.atomic
    def create(self, validated_data):
        transactions_data = validated_data.pop('transactions', [])
        entry = JournalEntry.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
        )

        for txn_data in transactions_data:
            Transaction.objects.create(
                journal_entry=entry,
                **txn_data,
            )

        return entry

    @db_transaction.atomic
    def update(self, instance, validated_data):
        transactions_data = validated_data.pop('transactions', None)

        # Update entry fields
        instance.description = validated_data.get('description', instance.description)
        instance.reference = validated_data.get('reference', instance.reference)
        instance.entry_date = validated_data.get('entry_date', instance.entry_date)
        instance.entry_type = validated_data.get('entry_type', instance.entry_type)
        instance.save()

        # Update transactions if provided
        if transactions_data is not None:
            # Remove existing transactions
            instance.transactions.all().delete()
            # Create new transactions
            for txn_data in transactions_data:
                Transaction.objects.create(
                    journal_entry=instance,
                    **txn_data,
                )

        return instance


# =============================================
# Financial Report Serializers
# =============================================

class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance in reports."""

    account_code = serializers.CharField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    balance = serializers.DecimalField(max_digits=16, decimal_places=2)


class FinancialReportSerializer(serializers.Serializer):
    """Serializer for income statement data."""

    total_income = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=16, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    income_accounts = AccountBalanceSerializer(many=True)
    expense_accounts = AccountBalanceSerializer(many=True)


class BalanceSheetSerializer(serializers.Serializer):
    """Serializer for balance sheet data."""

    total_assets = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_equity = serializers.DecimalField(max_digits=16, decimal_places=2)
    asset_accounts = AccountBalanceSerializer(many=True)
    liability_accounts = AccountBalanceSerializer(many=True)
    equity_accounts = AccountBalanceSerializer(many=True)


class AccountingStatsSerializer(serializers.Serializer):
    """Serializer for accounting dashboard statistics."""

    total_accounts = serializers.IntegerField()
    active_accounts = serializers.IntegerField()
    total_journal_entries = serializers.IntegerField()
    posted_entries = serializers.IntegerField()
    pending_entries = serializers.IntegerField()
    total_income = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=16, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
