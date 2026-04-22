"""
Serializers for the Import/Export module.
Handles ImportOrder, ImportItem, ExportOrder, ExportItem, and CustomsDeclaration
data transformation.
"""

from rest_framework import serializers
from .models import (
    ImportOrder,
    ImportItem,
    ExportOrder,
    ExportItem,
    CustomsDeclaration,
)


# =============================================
# Import Order Serializers
# =============================================

class ImportOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing import orders."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = ImportOrder
        fields = (
            'id', 'order_number', 'supplier', 'supplier_name', 'order_date',
            'expected_arrival', 'actual_arrival', 'port_of_entry',
            'country_of_origin', 'currency', 'exchange_rate', 'status',
            'status_display', 'total_amount', 'customs_duties', 'shipping_cost',
            'insurance_cost', 'other_costs', 'total_landed_cost',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ImportOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an import order."""

    class Meta:
        model = ImportOrder
        fields = (
            'order_number', 'supplier', 'order_date', 'expected_arrival',
            'port_of_entry', 'country_of_origin', 'currency', 'exchange_rate',
            'customs_duties', 'shipping_cost', 'insurance_cost', 'other_costs',
            'payment_terms', 'notes',
        )

    def validate_order_number(self, value):
        if ImportOrder.objects.filter(order_number=value).exists():
            raise serializers.ValidationError('رقم الأمر موجود مسبقاً')
        return value


class ImportOrderDetailSerializer(ImportOrderListSerializer):
    """Detailed import order serializer with items count."""

    items_count = serializers.SerializerMethodField()

    class Meta(ImportOrderListSerializer.Meta):
        fields = ImportOrderListSerializer.Meta.fields + ('payment_terms', 'notes', 'items_count')

    def get_items_count(self, obj):
        return obj.items.count()


# =============================================
# Import Item Serializers
# =============================================

class ImportItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing import items."""

    order_number = serializers.CharField(source='import_order.order_number', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True, default=None)

    class Meta:
        model = ImportItem
        fields = (
            'id', 'import_order', 'order_number', 'product', 'product_name',
            'description', 'hs_code', 'quantity', 'unit_price', 'total_price',
            'customs_duty_rate', 'customs_amount', 'unit', 'country_of_origin',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ImportItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an import item."""

    class Meta:
        model = ImportItem
        fields = (
            'import_order', 'product', 'description', 'hs_code',
            'quantity', 'unit_price', 'customs_duty_rate', 'unit',
            'country_of_origin', 'notes',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون صفر أو أكبر')
        return value


# =============================================
# Export Order Serializers
# =============================================

class ExportOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing export orders."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = ExportOrder
        fields = (
            'id', 'order_number', 'customer', 'customer_name', 'order_date',
            'ship_date', 'port_of_loading', 'destination_country',
            'destination_port', 'currency', 'exchange_rate', 'status',
            'status_display', 'total_amount', 'shipping_terms',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ExportOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an export order."""

    class Meta:
        model = ExportOrder
        fields = (
            'order_number', 'customer', 'order_date', 'ship_date',
            'port_of_loading', 'destination_country', 'destination_port',
            'currency', 'exchange_rate', 'shipping_terms',
            'payment_terms', 'notes',
        )

    def validate_order_number(self, value):
        if ExportOrder.objects.filter(order_number=value).exists():
            raise serializers.ValidationError('رقم الأمر موجود مسبقاً')
        return value


class ExportOrderDetailSerializer(ExportOrderListSerializer):
    """Detailed export order serializer with items count."""

    items_count = serializers.SerializerMethodField()

    class Meta(ExportOrderListSerializer.Meta):
        fields = ExportOrderListSerializer.Meta.fields + ('payment_terms', 'notes', 'items_count')

    def get_items_count(self, obj):
        return obj.items.count()


# =============================================
# Export Item Serializers
# =============================================

class ExportItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing export items."""

    order_number = serializers.CharField(source='export_order.order_number', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ExportItem
        fields = (
            'id', 'export_order', 'order_number', 'product', 'product_name',
            'description', 'hs_code', 'quantity', 'unit_price', 'total_price',
            'unit', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ExportItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an export item."""

    class Meta:
        model = ExportItem
        fields = (
            'export_order', 'product', 'description', 'hs_code',
            'quantity', 'unit_price', 'unit', 'notes',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون صفر أو أكبر')
        return value


# =============================================
# Customs Declaration Serializers
# =============================================

class CustomsDeclarationListSerializer(serializers.ModelSerializer):
    """Serializer for listing customs declarations."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    declaration_type_display = serializers.CharField(source='get_declaration_type_display', read_only=True)
    import_order_number = serializers.CharField(source='import_order.order_number', read_only=True, default=None)
    export_order_number = serializers.CharField(source='export_order.order_number', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = CustomsDeclaration
        fields = (
            'id', 'declaration_number', 'import_order', 'import_order_number',
            'export_order', 'export_order_number', 'declaration_type',
            'declaration_type_display', 'status', 'status_display',
            'submitted_date', 'cleared_date', 'declared_value',
            'duties_amount', 'taxes_amount', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CustomsDeclarationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a customs declaration."""

    class Meta:
        model = CustomsDeclaration
        fields = (
            'declaration_number', 'import_order', 'export_order',
            'declaration_type', 'declared_value', 'duties_amount',
            'taxes_amount', 'notes',
        )

    def validate_declaration_number(self, value):
        if CustomsDeclaration.objects.filter(declaration_number=value).exists():
            raise serializers.ValidationError('رقم الإقرار موجود مسبقاً')
        return value

    def validate(self, attrs):
        declaration_type = attrs.get('declaration_type')
        import_order = attrs.get('import_order')
        export_order = attrs.get('export_order')

        if declaration_type == 'import' and not import_order:
            raise serializers.ValidationError('يجب تحديد أمر استيراد لإقرار الاستيراد')
        if declaration_type == 'export' and not export_order:
            raise serializers.ValidationError('يجب تحديد أمر تصدير لإقرار التصدير')
        return attrs


class CustomsDeclarationChangeStatusSerializer(serializers.Serializer):
    """Serializer for changing customs declaration status."""

    status = serializers.ChoiceField(
        choices=CustomsDeclaration.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Stats Serializer
# =============================================

class ImportExportStatsSerializer(serializers.Serializer):
    """Serializer for Import/Export dashboard statistics."""

    total_import_orders = serializers.IntegerField()
    active_import_orders = serializers.IntegerField()
    total_export_orders = serializers.IntegerField()
    active_export_orders = serializers.IntegerField()
    total_customs_declarations = serializers.IntegerField()
    pending_customs = serializers.IntegerField()
    total_import_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_export_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_landed_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_customs_duties = serializers.DecimalField(max_digits=14, decimal_places=2)


class ChangeStatusSerializer(serializers.Serializer):
    """Generic serializer for changing order status."""

    status = serializers.CharField(
        max_length=20,
        help_text='الحالة الجديدة',
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )
