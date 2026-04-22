"""
Admin configuration for the Import/Export module.
"""

from django.contrib import admin
from .models import (
    ImportOrder,
    ImportItem,
    ExportOrder,
    ExportItem,
    CustomsDeclaration,
)


class ImportItemInline(admin.TabularInline):
    model = ImportItem
    extra = 0
    fields = ('product', 'description', 'hs_code', 'quantity', 'unit_price', 'total_price', 'customs_duty_rate', 'customs_amount', 'unit')
    readonly_fields = ('total_price', 'customs_amount')
    can_delete = True


class ExportItemInline(admin.TabularInline):
    model = ExportItem
    extra = 0
    fields = ('product', 'description', 'hs_code', 'quantity', 'unit_price', 'total_price', 'unit')
    readonly_fields = ('total_price',)
    can_delete = True


@admin.register(ImportOrder)
class ImportOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'order_date', 'expected_arrival', 'status', 'total_amount', 'total_landed_cost')
    list_filter = ('status', 'country_of_origin', 'currency', 'port_of_entry')
    search_fields = ('order_number', 'supplier__name')
    inlines = [ImportItemInline]


@admin.register(ImportItem)
class ImportItemAdmin(admin.ModelAdmin):
    list_display = ('import_order', 'product', 'description', 'quantity', 'unit_price', 'total_price', 'customs_duty_rate')
    list_filter = ('unit',)
    search_fields = ('description', 'hs_code', 'product__name', 'import_order__order_number')


@admin.register(ExportOrder)
class ExportOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'ship_date', 'status', 'total_amount')
    list_filter = ('status', 'destination_country', 'currency', 'port_of_loading')
    search_fields = ('order_number', 'customer__name')
    inlines = [ExportItemInline]


@admin.register(ExportItem)
class ExportItemAdmin(admin.ModelAdmin):
    list_display = ('export_order', 'product', 'description', 'quantity', 'unit_price', 'total_price')
    list_filter = ('unit',)
    search_fields = ('description', 'hs_code', 'product__name', 'export_order__order_number')


@admin.register(CustomsDeclaration)
class CustomsDeclarationAdmin(admin.ModelAdmin):
    list_display = ('declaration_number', 'declaration_type', 'status', 'declared_value', 'duties_amount', 'taxes_amount', 'submitted_date', 'cleared_date')
    list_filter = ('declaration_type', 'status')
    search_fields = ('declaration_number', 'import_order__order_number', 'export_order__order_number')
