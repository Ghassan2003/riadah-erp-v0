"""
Serializers for the Sales module.
Handles Customer, SalesOrder, and SalesOrderItem data transformation.
"""

from rest_framework import serializers
from django.db import transaction
from .models import Customer, SalesOrder, SalesOrderItem


# =============================================
# Customer Serializers
# =============================================

class CustomerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing customers."""

    orders_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'email', 'phone', 'is_active',
            'orders_count', 'created_at',
        )
        read_only_fields = ('id', 'orders_count', 'created_at')


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

    orders_count = serializers.IntegerField(read_only=True, default=0)
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'email', 'phone', 'address', 'is_active',
            'orders_count', 'total_spent', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


# =============================================
# SalesOrderItem Serializers
# =============================================

class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order line items."""

    product_name = serializers.CharField(read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = (
            'id', 'product_name',
            'quantity', 'unit_price', 'subtotal',
        )
        read_only_fields = ('id', 'subtotal')


class SalesOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding items to an order."""

    class Meta:
        model = SalesOrderItem
        fields = ('product_name', 'quantity', 'unit_price')

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
    items_count = serializers.IntegerField(read_only=True, default=0)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = SalesOrder
        fields = (
            'id', 'order_number', 'customer', 'customer_name',
            'status', 'status_display', 'order_date', 'total_amount',
            'items_count', 'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_at')


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

    def validate_items(self, value):
        """Ensure each item has a product name."""
        for item_data in value:
            if not item_data.get('product_name'):
                raise serializers.ValidationError('يجب تحديد اسم المنتج لكل بند')
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = SalesOrder.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
        )

        for item_data in items_data:
            SalesOrderItem.objects.create(
                order=order,
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price', 0),
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
