"""
Serializers for the Warehouse module.
Handles Warehouse, WarehouseStock, StockTransfer, StockAdjustment, and StockCount data.
"""

from rest_framework import serializers
from .models import (
    Warehouse, WarehouseStock, StockTransfer, StockTransferItem,
    StockAdjustment, StockCount, StockCountItem,
)


# =============================================
# Warehouse Serializers
# =============================================

class WarehouseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing warehouses."""

    current_stock_level = serializers.SerializerMethodField()
    utilized_capacity = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Warehouse
        fields = (
            'id', 'name', 'code', 'city', 'manager', 'manager_name',
            'capacity', 'current_stock_level', 'utilized_capacity',
            'products_count', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'code', 'created_at')

    def get_current_stock_level(self, obj):
        return obj.current_stock_level

    def get_utilized_capacity(self, obj):
        return obj.utilized_capacity

    def get_products_count(self, obj):
        return obj.products_count


class WarehouseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a warehouse."""

    class Meta:
        model = Warehouse
        fields = ('name', 'address', 'city', 'manager', 'capacity')


class WarehouseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating warehouse info."""

    class Meta:
        model = Warehouse
        fields = ('name', 'address', 'city', 'manager', 'capacity', 'is_active')


class WarehouseDetailSerializer(WarehouseListSerializer):
    """Detailed warehouse serializer with stocks list."""

    class Meta(WarehouseListSerializer.Meta):
        fields = WarehouseListSerializer.Meta.fields + ('address', 'updated_at')


# =============================================
# WarehouseStock Serializers
# =============================================

class WarehouseStockListSerializer(serializers.ModelSerializer):
    """Serializer for listing warehouse stock levels."""

    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    available_quantity = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = WarehouseStock
        fields = (
            'id', 'warehouse', 'warehouse_name', 'warehouse_code',
            'product', 'product_name', 'product_sku',
            'quantity', 'reserved_quantity', 'available_quantity',
            'min_stock_level', 'max_stock_level', 'last_restock_date',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'available_quantity', 'created_at', 'updated_at')


class WarehouseStockCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating warehouse stock."""

    class Meta:
        model = WarehouseStock
        fields = (
            'warehouse', 'product', 'quantity', 'reserved_quantity',
            'min_stock_level', 'max_stock_level', 'last_restock_date',
        )

    def validate(self, attrs):
        if WarehouseStock.objects.filter(
            warehouse=attrs['warehouse'],
            product=attrs['product'],
        ).exists():
            raise serializers.ValidationError('يوجد رصيد مخزون لهذا المنتج في هذا المستودع مسبقاً')
        return attrs


class WarehouseStockUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating warehouse stock."""

    class Meta:
        model = WarehouseStock
        fields = (
            'quantity', 'reserved_quantity', 'min_stock_level',
            'max_stock_level', 'last_restock_date',
        )


# =============================================
# StockTransfer Serializers
# =============================================

class StockTransferItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing transfer items."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = StockTransferItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'received_quantity', 'notes',
        )
        read_only_fields = ('id',)


class StockTransferItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transfer items."""

    class Meta:
        model = StockTransferItem
        fields = ('product', 'quantity', 'notes')


class StockTransferListSerializer(serializers.ModelSerializer):
    """Serializer for listing stock transfers."""

    from_warehouse_name = serializers.CharField(source='from_warehouse.name', read_only=True)
    from_warehouse_code = serializers.CharField(source='from_warehouse.code', read_only=True)
    to_warehouse_name = serializers.CharField(source='to_warehouse.name', read_only=True)
    to_warehouse_code = serializers.CharField(source='to_warehouse.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True, default=None)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = StockTransfer
        fields = (
            'id', 'transfer_number', 'from_warehouse', 'from_warehouse_name', 'from_warehouse_code',
            'to_warehouse', 'to_warehouse_name', 'to_warehouse_code',
            'status', 'status_display', 'items_count',
            'requested_by', 'requested_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'transfer_number', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class StockTransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock transfers."""

    items = StockTransferItemCreateSerializer(many=True)

    class Meta:
        model = StockTransfer
        fields = ('from_warehouse', 'to_warehouse', 'requested_by', 'notes', 'items')

    def validate(self, attrs):
        if attrs['from_warehouse'] == attrs['to_warehouse']:
            raise serializers.ValidationError('المستودع المصدر والوجهة يجب أن يكونا مختلفين')
        return attrs


class StockTransferApproveSerializer(serializers.Serializer):
    """Serializer for approving a stock transfer."""

    action = serializers.ChoiceField(choices=('approve', 'reject'))


class StockTransferReceiveSerializer(serializers.Serializer):
    """Serializer for receiving a stock transfer."""

    items = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of {item_id, received_quantity} objects',
    )


# =============================================
# StockAdjustment Serializers
# =============================================

class StockAdjustmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing stock adjustments."""

    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    difference = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = StockAdjustment
        fields = (
            'id', 'adjustment_number', 'warehouse', 'warehouse_name', 'warehouse_code',
            'product', 'product_name', 'reason', 'reason_display',
            'previous_quantity', 'new_quantity', 'difference',
            'notes', 'created_by', 'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'adjustment_number', 'difference', 'created_at')


class StockAdjustmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock adjustments."""

    class Meta:
        model = StockAdjustment
        fields = ('warehouse', 'reason', 'product', 'previous_quantity', 'new_quantity', 'notes')

    def validate(self, attrs):
        if attrs['previous_quantity'] < 0 or attrs['new_quantity'] < 0:
            raise serializers.ValidationError('الكميات لا يمكن أن تكون سالبة')
        return attrs


# =============================================
# StockCount Serializers
# =============================================

class StockCountItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing stock count items."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    difference = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = StockCountItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'system_quantity', 'counted_quantity', 'difference', 'notes',
        )
        read_only_fields = ('id', 'difference')


class StockCountItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock count items."""

    class Meta:
        model = StockCountItem
        fields = ('product', 'system_quantity', 'counted_quantity', 'notes')


class StockCountListSerializer(serializers.ModelSerializer):
    """Serializer for listing stock counts."""

    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    counted_by_name = serializers.CharField(source='counted_by.username', read_only=True, default=None)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = StockCount
        fields = (
            'id', 'count_number', 'warehouse', 'warehouse_name', 'warehouse_code',
            'status', 'status_display', 'counted_by', 'counted_by_name',
            'started_at', 'completed_at', 'items_count', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'count_number', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class StockCountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a stock count."""

    items = StockCountItemCreateSerializer(many=True)

    class Meta:
        model = StockCount
        fields = ('warehouse', 'counted_by', 'notes', 'items')


# =============================================
# Warehouse Stats Serializer
# =============================================

class WarehouseStatsSerializer(serializers.Serializer):
    """Serializer for warehouse dashboard statistics."""

    total_warehouses = serializers.IntegerField()
    active_warehouses = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_products_in_stock = serializers.IntegerField()
    pending_transfers = serializers.IntegerField()
    in_transit_transfers = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
    completed_counts = serializers.IntegerField()
    pending_adjustments = serializers.IntegerField()
