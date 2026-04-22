"""
Admin configuration for the Warehouse module.
"""

from django.contrib import admin
from .models import (
    Warehouse, WarehouseStock, StockTransfer, StockTransferItem,
    StockAdjustment, StockCount, StockCountItem,
)


class WarehouseStockInline(admin.TabularInline):
    model = WarehouseStock
    extra = 0
    fields = ('product', 'quantity', 'reserved_quantity', 'min_stock_level', 'max_stock_level')
    readonly_fields = ('product', 'quantity', 'reserved_quantity')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'manager', 'capacity', 'is_active')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'code', 'city')
    inlines = [WarehouseStockInline]


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 0
    fields = ('product', 'quantity', 'received_quantity', 'notes')
    readonly_fields = ('product', 'quantity', 'received_quantity')


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('transfer_number', 'from_warehouse', 'to_warehouse', 'status', 'requested_by', 'approved_at')
    list_filter = ('status',)
    search_fields = ('transfer_number', 'from_warehouse__name', 'to_warehouse__name')
    inlines = [StockTransferItemInline]


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ('warehouse', 'product', 'quantity', 'reserved_quantity', 'min_stock_level', 'max_stock_level')
    list_filter = ('warehouse',)
    search_fields = ('warehouse__name', 'product__name', 'product__sku')


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'warehouse', 'product', 'reason', 'previous_quantity', 'new_quantity', 'created_at')
    list_filter = ('reason', 'warehouse')
    search_fields = ('adjustment_number', 'product__name', 'warehouse__name')


class StockCountItemInline(admin.TabularInline):
    model = StockCountItem
    extra = 0
    fields = ('product', 'system_quantity', 'counted_quantity', 'notes')
    readonly_fields = ('product', 'system_quantity', 'counted_quantity')


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ('count_number', 'warehouse', 'status', 'counted_by', 'started_at', 'completed_at')
    list_filter = ('status', 'warehouse')
    search_fields = ('count_number', 'warehouse__name')
    inlines = [StockCountItemInline]


@admin.register(StockCountItem)
class StockCountItemAdmin(admin.ModelAdmin):
    list_display = ('count', 'product', 'system_quantity', 'counted_quantity')
    list_filter = ('count__warehouse',)
    search_fields = ('product__name',)
