"""
Serializers for the Sales module.
Handles Customer, SalesOrder, and SalesOrderItem data transformation.
"""

from rest_framework import serializers
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Value, DecimalField
from .models import Customer, SalesOrder, SalesOrderItem


# =============================================
# Customer Serializers
# =============================================

class CustomerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing customers."""

    orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'email', 'phone', 'is_active',
            'orders_count', 'created_at',
        )
        read_only_fields = ('id', 'orders_count', 'created_at')

    def get_orders_count(self, obj):
        return obj.orders.filter(status__in=('draft', 'confirmed', 'shipped', 'delivered')).count()


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new customer."""

    class Meta:
        model = Customer
        fields = ('name', 'email', 'phone', 'address')


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customer info."""

    class Meta:
        model = Customer
        fields = ('name', 'email', 'phone', 'address')


class CustomerDetailSerializer(serializers.ModelSerializer):
    """Detailed customer serializer with stats."""

    orders_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'email', 'phone', 'address', 'is_active',
            'orders_count', 'total_spent', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_orders_count(self, obj):
        return obj.orders.filter(status__in=('draft', 'confirmed', 'shipped', 'delivered')).count()

    def get_total_spent(self, obj):
        total = obj.orders.filter(
            status__in=('confirmed', 'shipped', 'delivered')
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        ).get('total')
        return total


# =============================================
# SalesOrderItem Serializers
# =============================================

class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order line items."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'subtotal',
        )
        read_only_fields = ('id', 'subtotal', 'product_name', 'product_sku')


class SalesOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding items to an order (price fetched from product)."""

    class Meta:
        model = SalesOrderItem
        fields = ('product', 'quantity')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


# =============================================
# SalesOrder Serializers
# =============================================

class SalesOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing orders."""

    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = SalesOrder
        fields = (
            'id', 'order_number', 'customer', 'customer_name',
            'status', 'status_display', 'order_date', 'total_amount',
            'items_count', 'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class SalesOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with items."""

    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = SalesOrder
        fields = (
            'id', 'order_number', 'customer', 'customer_name',
            'status', 'status_display', 'order_date', 'total_amount',
            'notes', 'items', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_by', 'created_at', 'updated_at')


class CreateSalesOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new sales order with items.
    Captures product prices at order time.
    """

    items = SalesOrderItemCreateSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = ('customer', 'notes', 'items')

    def validate_items(self, value):
        """Ensure order has at least one item."""
        if not value:
            raise serializers.ValidationError('يجب إضافة منتج واحد على الأقل للأمر')
        return value

    def validate(self, attrs):
        """Validate stock availability for all items."""
        items_data = attrs.get('items', [])
        for item_data in items_data:
            product = item_data['product']
            # Check product is active
            if not product.is_active:
                raise serializers.ValidationError(
                    f'المنتج "{product.name}" غير متاح حالياً'
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = SalesOrder.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
        )

        for item_data in items_data:
            product = item_data['product']
            SalesOrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.unit_price,  # Capture current price
            )

        order.calculate_total()
        return order


class ChangeOrderStatusSerializer(serializers.Serializer):
    """Serializer for changing order status."""

    status = serializers.ChoiceField(
        choices=SalesOrder.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )


# =============================================
# Sales Stats Serializer
# =============================================

class SalesStatsSerializer(serializers.Serializer):
    """Serializer for sales dashboard statistics."""

    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    confirmed_orders = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    this_month_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
