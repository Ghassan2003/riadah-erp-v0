"""
Admin configuration for the Assets module.
"""

from django.contrib import admin
from .models import AssetCategory, FixedAsset, AssetTransfer, AssetMaintenance, AssetDisposal


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'useful_life_years', 'depreciation_method', 'salvage_value_rate', 'is_active')
    list_filter = ('is_active', 'depreciation_method')
    search_fields = ('name', 'name_en')


class AssetTransferInline(admin.TabularInline):
    model = AssetTransfer
    extra = 0
    fields = ('from_department', 'to_department', 'from_employee', 'to_employee', 'transfer_date')
    readonly_fields = ('from_department', 'to_department', 'from_employee', 'to_employee', 'transfer_date')


class AssetMaintenanceInline(admin.TabularInline):
    model = AssetMaintenance
    extra = 0
    fields = ('maintenance_type', 'description', 'cost', 'maintenance_date', 'status')
    readonly_fields = ('maintenance_type', 'description', 'cost', 'maintenance_date', 'status')


@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_number', 'name', 'category', 'department', 'assigned_to', 'purchase_price', 'status', 'is_active')
    list_filter = ('status', 'category', 'department', 'is_active')
    search_fields = ('name', 'name_en', 'asset_number', 'serial_number', 'barcode')
    inlines = [AssetTransferInline, AssetMaintenanceInline]


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ('asset', 'from_department', 'to_department', 'from_employee', 'to_employee', 'transfer_date')
    list_filter = ('transfer_date',)
    search_fields = ('asset__name', 'asset__asset_number')


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('asset', 'maintenance_type', 'cost', 'maintenance_date', 'status', 'vendor')
    list_filter = ('maintenance_type', 'status')
    search_fields = ('asset__name', 'description', 'vendor')


@admin.register(AssetDisposal)
class AssetDisposalAdmin(admin.ModelAdmin):
    list_display = ('asset', 'disposal_type', 'disposal_date', 'disposal_value', 'approved_by')
    list_filter = ('disposal_type',)
    search_fields = ('asset__name', 'buyer_name', 'notes')
