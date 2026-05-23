"""
Serializers for the Assets module.
Handles AssetCategory, FixedAsset, AssetTransfer, AssetMaintenance, and AssetDisposal.
"""

from rest_framework import serializers
from .models import (
    AssetCategory, FixedAsset, AssetTransfer, AssetMaintenance, AssetDisposal,
)


# =============================================
# AssetCategory Serializers
# =============================================

class AssetCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing asset categories."""

    assets_count = serializers.SerializerMethodField()
    depreciation_method_display = serializers.SerializerMethodField()

    class Meta:
        model = AssetCategory
        fields = (
            'id', 'name', 'name_en', 'useful_life_years',
            'depreciation_method', 'depreciation_method_display',
            'salvage_value_rate', 'assets_count', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_depreciation_method_display(self, obj):
        return obj.get_depreciation_method_display()

    def get_assets_count(self, obj):
        return obj.assets.filter(is_active=True).count()


class AssetCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an asset category."""

    class Meta:
        model = AssetCategory
        fields = ('name', 'name_en', 'useful_life_years', 'depreciation_method', 'salvage_value_rate')


class AssetCategoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an asset category."""

    class Meta:
        model = AssetCategory
        fields = ('name', 'name_en', 'useful_life_years', 'depreciation_method', 'salvage_value_rate', 'is_active')


# =============================================
# FixedAsset Serializers
# =============================================

class FixedAssetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing fixed assets."""

    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    monthly_depreciation = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = FixedAsset
        fields = (
            'id', 'asset_number', 'name', 'name_en', 'category', 'category_name',
            'serial_number', 'barcode', 'purchase_date', 'purchase_price',
            'current_value', 'monthly_depreciation', 'accumulated_depreciation',
            'location', 'department', 'department_name', 'assigned_to', 'assigned_to_name',
            'status', 'status_display', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'asset_number', 'current_value', 'monthly_depreciation', 'created_at')


class FixedAssetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a fixed asset."""

    class Meta:
        model = FixedAsset
        fields = (
            'name', 'name_en', 'category', 'serial_number', 'barcode',
            'purchase_date', 'purchase_price', 'salvage_value', 'useful_life_months',
            'location', 'department', 'assigned_to', 'supplier',
            'warranty_end_date', 'status', 'notes',
        )


class FixedAssetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a fixed asset."""

    class Meta:
        model = FixedAsset
        fields = (
            'name', 'name_en', 'category', 'serial_number', 'barcode',
            'purchase_date', 'purchase_price', 'salvage_value', 'useful_life_months',
            'accumulated_depreciation', 'location', 'department', 'assigned_to',
            'supplier', 'warranty_end_date', 'status', 'is_active', 'notes',
        )


class FixedAssetDetailSerializer(FixedAssetListSerializer):
    """Detailed serializer with category info."""

    category_info = AssetCategoryListSerializer(source='category', read_only=True)

    class Meta(FixedAssetListSerializer.Meta):
        fields = FixedAssetListSerializer.Meta.fields + (
            'supplier', 'warranty_end_date', 'notes', 'updated_at', 'category_info',
        )


# =============================================
# AssetTransfer Serializers
# =============================================

class AssetTransferListSerializer(serializers.ModelSerializer):
    """Serializer for listing asset transfers."""

    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_number = serializers.CharField(source='asset.asset_number', read_only=True)
    from_department_name = serializers.CharField(source='from_department.name', read_only=True, default=None)
    to_department_name = serializers.CharField(source='to_department.name', read_only=True, default=None)
    from_employee_name = serializers.CharField(source='from_employee.full_name', read_only=True, default=None)
    to_employee_name = serializers.CharField(source='to_employee.full_name', read_only=True, default=None)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = AssetTransfer
        fields = (
            'id', 'asset', 'asset_name', 'asset_number',
            'from_department', 'from_department_name', 'to_department', 'to_department_name',
            'from_employee', 'from_employee_name', 'to_employee', 'to_employee_name',
            'from_location', 'to_location', 'transfer_date',
            'notes', 'approved_by', 'approved_by_name', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class AssetTransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an asset transfer."""

    class Meta:
        model = AssetTransfer
        fields = (
            'asset', 'from_department', 'to_department',
            'from_employee', 'to_employee',
            'from_location', 'to_location', 'transfer_date', 'notes',
        )


# =============================================
# AssetMaintenance Serializers
# =============================================

class AssetMaintenanceListSerializer(serializers.ModelSerializer):
    """Serializer for listing asset maintenance records."""

    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_number = serializers.CharField(source='asset.asset_number', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AssetMaintenance
        fields = (
            'id', 'asset', 'asset_name', 'asset_number',
            'maintenance_type', 'maintenance_type_display',
            'description', 'cost', 'maintenance_date', 'next_maintenance_date',
            'vendor', 'status', 'status_display', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class AssetMaintenanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a maintenance record."""

    class Meta:
        model = AssetMaintenance
        fields = (
            'asset', 'maintenance_type', 'description', 'cost',
            'maintenance_date', 'next_maintenance_date', 'vendor', 'status',
        )


class AssetMaintenanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a maintenance record."""

    class Meta:
        model = AssetMaintenance
        fields = (
            'maintenance_type', 'description', 'cost',
            'maintenance_date', 'next_maintenance_date', 'vendor', 'status',
        )


# =============================================
# AssetDisposal Serializers
# =============================================

class AssetDisposalListSerializer(serializers.ModelSerializer):
    """Serializer for listing asset disposals."""

    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_number = serializers.CharField(source='asset.asset_number', read_only=True)
    disposal_type_display = serializers.CharField(source='get_disposal_type_display', read_only=True)
    loss_gain = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = AssetDisposal
        fields = (
            'id', 'asset', 'asset_name', 'asset_number',
            'disposal_type', 'disposal_type_display', 'disposal_date',
            'disposal_value', 'loss_gain', 'buyer_name',
            'notes', 'approved_by', 'approved_by_name', 'created_at',
        )
        read_only_fields = ('id', 'loss_gain', 'created_at')


class AssetDisposalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an asset disposal."""

    class Meta:
        model = AssetDisposal
        fields = (
            'asset', 'disposal_type', 'disposal_date',
            'disposal_value', 'buyer_name', 'notes',
        )


# =============================================
# Asset Depreciation Serializer
# =============================================

class AssetDepreciationSerializer(serializers.Serializer):
    """Serializer for running depreciation on assets."""

    asset_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='List of specific asset IDs to depreciate. If empty, all eligible assets.',
    )


# =============================================
# Asset Stats Serializer
# =============================================

class AssetStatsSerializer(serializers.Serializer):
    """Serializer for assets dashboard statistics."""

    total_assets = serializers.IntegerField()
    active_assets = serializers.IntegerField()
    total_purchase_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_current_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_accumulated_depreciation = serializers.DecimalField(max_digits=14, decimal_places=2)
    assets_in_maintenance = serializers.IntegerField()
    disposed_assets = serializers.IntegerField()
    expiring_warranties = serializers.IntegerField()
    total_maintenance_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
