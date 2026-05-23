"""
Admin configuration for the Equipment Maintenance module.
"""

from django.contrib import admin
from .models import (
    Equipment,
    MaintenanceSchedule,
    MaintenanceWorkOrder,
    MaintenancePart,
    EquipmentInspection,
)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_number', 'category', 'brand', 'status', 'assigned_department', 'purchase_cost')
    list_filter = ('category', 'status')
    search_fields = ('name', 'equipment_number', 'brand', 'model_number', 'serial_number')


class MaintenancePartInline(admin.TabularInline):
    model = MaintenancePart
    extra = 0
    fields = ('part_name', 'part_number', 'quantity', 'unit_cost', 'supplier')
    readonly_fields = ('part_name', 'part_number', 'quantity', 'unit_cost', 'supplier')
    can_delete = False


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_type', 'frequency_type', 'frequency_value', 'next_due', 'priority', 'is_active')
    list_filter = ('maintenance_type', 'frequency_type', 'priority', 'is_active')
    search_fields = ('equipment__name', 'equipment__equipment_number')


@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'equipment', 'work_type', 'priority', 'status', 'requested_by', 'assigned_to', 'created_at')
    list_filter = ('work_type', 'priority', 'status')
    search_fields = ('work_order_number', 'equipment__name', 'equipment__equipment_number', 'description')
    inlines = [MaintenancePartInline]


@admin.register(MaintenancePart)
class MaintenancePartAdmin(admin.ModelAdmin):
    list_display = ('part_name', 'part_number', 'work_order', 'quantity', 'unit_cost', 'supplier')
    list_filter = ('supplier',)
    search_fields = ('part_name', 'part_number')


@admin.register(EquipmentInspection)
class EquipmentInspectionAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'inspection_type', 'inspector', 'inspection_date', 'condition_rating', 'status')
    list_filter = ('inspection_type', 'condition_rating', 'status')
    search_fields = ('equipment__name', 'equipment__equipment_number', 'findings')
