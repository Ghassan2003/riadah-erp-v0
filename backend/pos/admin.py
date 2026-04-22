from django.contrib import admin
from .models import (
    POSShift,
    POSSale,
    POSRefund,
    POSHoldOrder,
    CashDrawerTransaction,
)


@admin.register(POSShift)
class POSShiftAdmin(admin.ModelAdmin):
    list_display = [
        'shift_number', 'cashier', 'start_time', 'end_time',
        'status', 'opening_cash', 'closing_cash', 'expected_cash',
        'difference', 'total_sales', 'total_transactions',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['shift_number', 'cashier__username', 'cashier__first_name']
    readonly_fields = [
        'shift_number', 'expected_cash', 'difference',
        'total_sales', 'total_transactions', 'total_refunds',
    ]
    date_hierarchy = 'created_at'


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'shift', 'customer', 'total_amount',
        'payment_method', 'status', 'created_at',
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['receipt_number', 'notes']
    readonly_fields = ['receipt_number', 'vat_amount']
    date_hierarchy = 'created_at'


@admin.register(POSRefund)
class POSRefundAdmin(admin.ModelAdmin):
    list_display = [
        'refund_number', 'sale', 'shift', 'refund_amount',
        'refund_method', 'processed_by', 'created_at',
    ]
    list_filter = ['refund_method', 'created_at']
    search_fields = ['refund_number', 'reason', 'sale__receipt_number']
    readonly_fields = ['refund_number']
    date_hierarchy = 'created_at'


@admin.register(POSHoldOrder)
class POSHoldOrderAdmin(admin.ModelAdmin):
    list_display = [
        'hold_number', 'shift', 'customer_name', 'total_amount',
        'is_recovered', 'created_at',
    ]
    list_filter = ['is_recovered', 'created_at']
    search_fields = ['hold_number', 'customer_name']
    readonly_fields = ['hold_number']


@admin.register(CashDrawerTransaction)
class CashDrawerTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'shift', 'transaction_type', 'amount', 'description',
        'created_by', 'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['description', 'shift__shift_number']
    date_hierarchy = 'created_at'
