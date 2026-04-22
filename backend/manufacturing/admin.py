"""
تهيئة المشرف لوحدة التصنيع.
"""

from django.contrib import admin
from .models import (
    BillOfMaterials,
    BOMItem,
    ProductionOrder,
    ProductionLog,
    WorkCenter,
    RoutingStep,
)


class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 0
    fields = ('material', 'quantity', 'unit_cost', 'notes')
    readonly_fields = ('material', 'quantity', 'unit_cost')
    can_delete = False


class RoutingStepInline(admin.TabularInline):
    model = RoutingStep
    extra = 0
    fields = ('step_number', 'work_center', 'operation_name', 'estimated_minutes', 'cost_per_unit')
    readonly_fields = ('step_number', 'work_center', 'operation_name', 'estimated_minutes', 'cost_per_unit')
    can_delete = False


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'version', 'status', 'effective_date', 'created_at')
    list_filter = ('status', 'product')
    search_fields = ('name', 'product__name', 'product__sku')
    inlines = [BOMItemInline, RoutingStepInline]


@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ('bom', 'material', 'quantity', 'unit_cost', 'created_at')
    list_filter = ('bom',)
    search_fields = ('bom__name', 'material__name', 'material__sku')


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product', 'quantity', 'quantity_produced', 'status', 'priority', 'planned_start_date', 'created_at')
    list_filter = ('status', 'priority', 'product')
    search_fields = ('order_number', 'product__name', 'product__sku')


@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = ('production_order', 'operation_type', 'quantity', 'defect_quantity', 'operator', 'log_date')
    list_filter = ('operation_type', 'production_order')
    search_fields = ('production_order__order_number', 'notes')


@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'status', 'cost_per_hour', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'location')


@admin.register(RoutingStep)
class RoutingStepAdmin(admin.ModelAdmin):
    list_display = ('bom', 'step_number', 'work_center', 'operation_name', 'estimated_minutes', 'cost_per_unit')
    list_filter = ('bom', 'work_center')
    search_fields = ('bom__name', 'operation_name')
