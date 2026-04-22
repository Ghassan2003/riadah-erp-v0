from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, PaymentReminder


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('subtotal', 'vat_amount', 'total')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'invoice_type', 'customer', 'supplier',
        'issue_date', 'due_date', 'total_amount', 'payment_status',
        'status', 'is_active', 'created_at'
    )
    list_filter = ('invoice_type', 'status', 'payment_status', 'is_active', 'currency')
    search_fields = ('invoice_number', 'customer__name', 'supplier__name', 'tax_number')
    readonly_fields = (
        'discount_amount', 'vat_amount', 'total_after_discount', 'total_amount',
        'created_at', 'updated_at'
    )
    inlines = [InvoiceItemInline]
    date_hierarchy = 'created_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_number', 'invoice', 'amount', 'payment_method',
        'payment_date', 'bank_name', 'created_at'
    )
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('payment_number', 'invoice__invoice_number', 'reference_number', 'bank_name')
    date_hierarchy = 'payment_date'


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = (
        'invoice', 'reminder_type', 'sent_via', 'status', 'sent_date'
    )
    list_filter = ('reminder_type', 'sent_via', 'status')
    search_fields = ('invoice__invoice_number', 'message')
    date_hierarchy = 'sent_date'
