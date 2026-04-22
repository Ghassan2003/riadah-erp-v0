"""
Admin configuration for the Payments module.
"""

from django.contrib import admin
from .models import PaymentAccount, FinancialTransaction, Cheque, Reconciliation


@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_name', 'account_type', 'bank_name', 'currency',
        'current_balance', 'is_default', 'is_active',
    )
    list_filter = ('account_type', 'is_default', 'is_active', 'currency')
    search_fields = ('account_name', 'bank_name', 'account_number', 'iban')


class ChequeInline(admin.TabularInline):
    model = Cheque
    extra = 0
    fields = ('cheque_number', 'bank_name', 'amount', 'due_date', 'status')
    readonly_fields = ('cheque_number', 'bank_name', 'amount', 'due_date', 'status')


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_number', 'transaction_type', 'account', 'amount',
        'currency', 'payment_method', 'status', 'transaction_date',
    )
    list_filter = ('transaction_type', 'payment_method', 'status', 'currency', 'transaction_date')
    search_fields = ('transaction_number', 'description', 'cheque_number', 'customer__name', 'supplier__name')


@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = (
        'cheque_number', 'bank_name', 'amount', 'due_date',
        'payer_name', 'payee_name', 'cheque_type', 'status',
    )
    list_filter = ('cheque_type', 'status', 'bank_name', 'due_date')
    search_fields = ('cheque_number', 'bank_name', 'payer_name', 'payee_name')


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        'reconciliation_number', 'account', 'period_start', 'period_end',
        'system_balance', 'actual_balance', 'status',
    )
    list_filter = ('status', 'account')
    search_fields = ('reconciliation_number', 'account__account_name', 'notes')
