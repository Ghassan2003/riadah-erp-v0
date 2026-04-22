"""
Serializers for the Product model.
Handles data validation and transformation for inventory API.
"""

from rest_framework import serializers
from .models import Product


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products in tables."""

    is_low_stock = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'sku', 'quantity', 'unit_price',
            'reorder_level', 'is_active', 'is_low_stock', 'total_value',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_low_stock', 'total_value')


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new product."""

    class Meta:
        model = Product
        fields = (
            'name', 'description', 'sku', 'quantity',
            'unit_price', 'reorder_level',
        )

    def validate_sku(self, value):
        """Ensure SKU is unique (including soft-deleted products)."""
        if Product.all_objects.filter(sku=value).exists():
            raise serializers.ValidationError(
                'رمز المنتج (SKU) مستخدم بالفعل. يجب أن يكون فريداً.'
            )
        return value

    def validate_unit_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون أكبر من صفر')
        return value

    def validate_quantity(self, value):
        """Ensure quantity is non-negative."""
        if value < 0:
            raise serializers.ValidationError('الكمية لا يمكن أن تكون سالبة')
        return value


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing product."""

    class Meta:
        model = Product
        fields = (
            'name', 'description', 'sku', 'quantity',
            'unit_price', 'reorder_level',
        )

    def validate_sku(self, value):
        """Ensure SKU uniqueness, excluding the current product."""
        instance = self.instance
        if Product.all_objects.filter(sku=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(
                'رمز المنتج (SKU) مستخدم بالفعل. يجب أن يكون فريداً.'
            )
        return value

    def validate_unit_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون أكبر من صفر')
        return value

    def validate_quantity(self, value):
        """Ensure quantity is non-negative."""
        if value < 0:
            raise serializers.ValidationError('الكمية لا يمكن أن تكون سالبة')
        return value


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for viewing a single product."""

    is_low_stock = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'sku', 'quantity',
            'unit_price', 'reorder_level', 'is_active',
            'is_low_stock', 'total_value',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_low_stock', 'total_value')


class InventoryStatsSerializer(serializers.Serializer):
    """Serializer for inventory dashboard statistics."""

    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    total_inventory_value = serializers.DecimalField(max_digits=14, decimal_places=2)
