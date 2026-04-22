"""
Admin configuration for Sales models.
"""

from django.contrib import admin
from .models import Customer, SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    """Inline editor for order items."""
    model = SalesOrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product', 'quantity', 'unit_price', 'subtotal')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'status', 'order_date',
        'total_amount', 'created_by', 'created_at',
    )
    list_filter = ('status', 'order_date', 'created_at')
    search_fields = ('order_number', 'customer__name', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at')
    inlines = [SalesOrderItemInline]

    fieldsets = (
        ('معلومات الأمر', {
            'fields': ('order_number', 'customer', 'status', 'order_date')
        }),
        ('التفاصيل', {
            'fields': ('total_amount', 'notes', 'created_by')
        }),
    )


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product__name')
    ordering = ('-order__created_at',)
