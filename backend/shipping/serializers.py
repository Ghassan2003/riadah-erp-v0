"""
Serializers for the Shipping module.
Handles ShippingMethod, Shipment, ShipmentItem, ShipmentEvent, and DeliveryAttempt
data transformation.
"""

from rest_framework import serializers
from .models import (
    ShippingMethod,
    Shipment,
    ShipmentItem,
    ShipmentEvent,
    DeliveryAttempt,
)


# =============================================
# Shipping Method Serializers
# =============================================

class ShippingMethodListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing shipping methods."""

    cost_type_display = serializers.CharField(source='get_cost_type_display', read_only=True)

    class Meta:
        model = ShippingMethod
        fields = (
            'id', 'name', 'description', 'carrier', 'tracking_url',
            'cost_type', 'cost_type_display', 'base_cost', 'cost_per_unit',
            'estimated_days', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ShippingMethodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a shipping method."""

    class Meta:
        model = ShippingMethod
        fields = (
            'name', 'description', 'carrier', 'tracking_url', 'cost_type',
            'base_cost', 'cost_per_unit', 'estimated_days', 'is_active',
        )

    def validate_base_cost(self, value):
        if value < 0:
            raise serializers.ValidationError('التكلفة الأساسية يجب أن تكون صفر أو أكبر')
        return value

    def validate_cost_per_unit(self, value):
        if value < 0:
            raise serializers.ValidationError('التكلفة لكل وحدة يجب أن تكون صفر أو أكبر')
        return value


class ShippingMethodUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a shipping method."""

    class Meta:
        model = ShippingMethod
        fields = (
            'name', 'description', 'carrier', 'tracking_url', 'cost_type',
            'base_cost', 'cost_per_unit', 'estimated_days', 'is_active',
        )


class ShippingMethodDetailSerializer(ShippingMethodListSerializer):
    """Detailed shipping method serializer."""

    shipments_count = serializers.SerializerMethodField()

    class Meta(ShippingMethodListSerializer.Meta):
        fields = ShippingMethodListSerializer.Meta.fields + ('shipments_count',)

    def get_shipments_count(self, obj):
        return obj.shipments.count()


# =============================================
# Shipment Serializers
# =============================================

class ShipmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing shipments."""

    customer_name = serializers.CharField(source='customer.name', read_only=True)
    shipping_method_name = serializers.CharField(source='shipping_method.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = (
            'id', 'shipment_number', 'sales_order', 'customer', 'customer_name',
            'shipping_method', 'shipping_method_name', 'status', 'status_display',
            'weight', 'tracking_number', 'estimated_delivery', 'actual_delivery',
            'shipping_cost', 'insurance_amount', 'created_by', 'created_by_name',
            'items_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_items_count(self, obj):
        return obj.items.count()


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a shipment."""

    class Meta:
        model = Shipment
        fields = (
            'shipment_number', 'sales_order', 'customer', 'shipping_method',
            'weight', 'dimensions', 'origin_address', 'destination_address',
            'tracking_number', 'estimated_delivery', 'shipping_cost',
            'insurance_amount', 'notes',
        )

    def validate_shipment_number(self, value):
        if Shipment.objects.filter(shipment_number=value).exists():
            raise serializers.ValidationError('رقم الشحنة موجود مسبقاً')
        return value


class ShipmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a shipment."""

    class Meta:
        model = Shipment
        fields = (
            'weight', 'dimensions', 'tracking_number', 'estimated_delivery',
            'shipping_cost', 'insurance_amount', 'notes',
        )


class ShipmentChangeStatusSerializer(serializers.Serializer):
    """Serializer for changing shipment status."""

    status = serializers.ChoiceField(
        choices=Shipment.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة الشحنة غير صالحة'},
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


class ShipmentDetailSerializer(ShipmentListSerializer):
    """Detailed shipment serializer with items and events."""

    items = serializers.SerializerMethodField()
    recent_events = serializers.SerializerMethodField()

    class Meta(ShipmentListSerializer.Meta):
        fields = ShipmentListSerializer.Meta.fields + (
            'origin_address', 'destination_address', 'dimensions', 'notes',
            'items', 'recent_events',
        )

    def get_items(self, obj):
        items = obj.items.select_related('product').all()
        return ShipmentItemSerializer(items, many=True).data

    def get_recent_events(self, obj):
        events = obj.events.all()[:10]
        return ShipmentEventSerializer(events, many=True).data


# =============================================
# Shipment Item Serializers
# =============================================

class ShipmentItemSerializer(serializers.ModelSerializer):
    """Serializer for shipment items."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True, default=None)

    class Meta:
        model = ShipmentItem
        fields = (
            'id', 'shipment', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'weight', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ShipmentItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a shipment item."""

    class Meta:
        model = ShipmentItem
        fields = ('shipment', 'product', 'quantity', 'unit_price', 'weight')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


# =============================================
# Shipment Event Serializers
# =============================================

class ShipmentEventSerializer(serializers.ModelSerializer):
    """Serializer for shipment events."""

    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    shipment_number = serializers.CharField(source='shipment.shipment_number', read_only=True)

    class Meta:
        model = ShipmentEvent
        fields = (
            'id', 'shipment', 'shipment_number', 'event_type', 'event_type_display',
            'location', 'description', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ShipmentEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a shipment event."""

    class Meta:
        model = ShipmentEvent
        fields = ('shipment', 'event_type', 'location', 'description')


# =============================================
# Delivery Attempt Serializers
# =============================================

class DeliveryAttemptSerializer(serializers.ModelSerializer):
    """Serializer for delivery attempts."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipment_number = serializers.CharField(source='shipment.shipment_number', read_only=True)

    class Meta:
        model = DeliveryAttempt
        fields = (
            'id', 'shipment', 'shipment_number', 'attempt_number',
            'attempt_date', 'status', 'status_display', 'recipient_name',
            'notes', 'signature', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


# =============================================
# Shipping Stats Serializer
# =============================================

class ShippingStatsSerializer(serializers.Serializer):
    """Serializer for Shipping dashboard statistics."""

    total_shipments = serializers.IntegerField()
    pending_shipments = serializers.IntegerField()
    in_transit_shipments = serializers.IntegerField()
    delivered_shipments = serializers.IntegerField()
    returned_shipments = serializers.IntegerField()
    total_shipping_methods = serializers.IntegerField()
    active_shipping_methods = serializers.IntegerField()
    total_shipping_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_events = serializers.IntegerField()
    total_delivery_attempts = serializers.IntegerField()
    failed_delivery_attempts = serializers.IntegerField()
