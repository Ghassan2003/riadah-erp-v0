"""
Serializers for the Purchases module.
Handles Supplier, PurchaseOrder, and PurchaseOrderItem data transformation.
"""

from rest_framework import serializers
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Value, DecimalField
from .models import Supplier, PurchaseOrder, PurchaseOrderItem


# =============================================
# Supplier Serializers
# =============================================

class SupplierListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing suppliers."""

    orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            'id', 'name', 'name_en', 'email', 'phone', 'is_active',
            'orders_count', 'created_at',
        )
        read_only_fields = ('id', 'orders_count', 'created_at')

    def get_orders_count(self, obj):
        return obj.orders.filter(status__in=('draft', 'confirmed', 'partial', 'received')).count()


class SupplierCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new supplier."""

    class Meta:
        model = Supplier
        fields = ('name', 'name_en', 'contact_person', 'email', 'phone', 'address', 'tax_number')


class SupplierUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating supplier info."""

    class Meta:
        model = Supplier
        fields = ('name', 'name_en', 'contact_person', 'email', 'phone', 'address', 'tax_number')


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Detailed supplier serializer with stats."""

    orders_count = serializers.SerializerMethodField()
    total_purchases = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            'id', 'name', 'name_en', 'contact_person', 'email', 'phone',
            'address', 'tax_number', 'is_active', 'balance',
            'orders_count', 'total_purchases', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_orders_count(self, obj):
        return obj.orders.filter(status__in=('draft', 'confirmed', 'partial', 'received')).count()

    def get_total_purchases(self, obj):
        total = obj.orders.filter(
            status__in=('confirmed', 'partial', 'received')
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        ).get('total')
        return total


# =============================================
# PurchaseOrderItem Serializers
# =============================================

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order line items."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'subtotal', 'received_quantity',
        )
        read_only_fields = ('id', 'subtotal', 'product_name', 'product_sku')


class PurchaseOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding items to an order (price fetched from product)."""

    class Meta:
        model = PurchaseOrderItem
        fields = ('product', 'quantity')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


# =============================================
# PurchaseOrder Serializers
# =============================================

class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing orders."""

    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'order_number', 'supplier', 'supplier_name',
            'status', 'status_display', 'order_date', 'expected_date',
            'total_amount', 'items_count', 'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with items."""

    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'order_number', 'supplier', 'supplier_name',
            'status', 'status_display', 'order_date', 'expected_date',
            'total_amount', 'notes', 'items', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_by', 'created_at', 'updated_at')


class CreatePurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new purchase order with items.
    Captures product prices at order time.
    """

    items = PurchaseOrderItemCreateSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ('supplier', 'expected_date', 'notes', 'items')

    def validate_items(self, value):
        """Ensure order has at least one item."""
        if not value:
            raise serializers.ValidationError('يجب إضافة منتج واحد على الأقل للأمر')
        return value

    def validate(self, attrs):
        """Validate supplier is active for all items."""
        supplier = attrs.get('supplier')
        if supplier and not supplier.is_active:
            raise serializers.ValidationError(
                f'المورد "{supplier.name}" غير نشط حالياً'
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = PurchaseOrder.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
        )

        for item_data in items_data:
            product = item_data['product']
            PurchaseOrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.unit_price,  # Capture current price
            )

        order.calculate_total()
        return order


class ChangePurchaseOrderStatusSerializer(serializers.Serializer):
    """Serializer for changing purchase order status."""

    status = serializers.ChoiceField(
        choices=PurchaseOrder.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )


# =============================================
# Purchase Stats Serializer
# =============================================

class PurchaseStatsSerializer(serializers.Serializer):
    """Serializer for purchases dashboard statistics."""

    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    confirmed_orders = serializers.IntegerField()
    total_purchases = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_purchases = serializers.DecimalField(max_digits=14, decimal_places=2)
    this_month_purchases = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_suppliers = serializers.IntegerField()
