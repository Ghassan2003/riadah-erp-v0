"""
Admin configuration for Purchases models.
"""

from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    """Inline editor for purchase order items."""
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product', 'quantity', 'unit_price', 'subtotal', 'received_quantity')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'email', 'phone', 'is_active', 'balance', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'name_en', 'email', 'phone')
    ordering = ('-created_at',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'supplier', 'status', 'order_date', 'expected_date',
        'total_amount', 'created_by', 'created_at',
    )
    list_filter = ('status', 'order_date', 'created_at')
    search_fields = ('order_number', 'supplier__name', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        ('معلومات الأمر', {
            'fields': ('order_number', 'supplier', 'status', 'order_date', 'expected_date')
        }),
        ('التفاصيل', {
            'fields': ('total_amount', 'notes', 'created_by')
        }),
    )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal', 'received_quantity')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product__name')
    ordering = ('-order__created_at',)
