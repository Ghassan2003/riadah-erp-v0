"""
المسلسلات لوحدة التصنيع.
تتعامل مع تحويل بيانات قوائم المواد، أوامر الإنتاج، سجلات الإنتاج، مراكز العمل، وخطوات المسارات.
"""

from rest_framework import serializers
from .models import (
    BillOfMaterials,
    BOMItem,
    ProductionOrder,
    ProductionLog,
    WorkCenter,
    RoutingStep,
)


# =============================================
# BillOfMaterials Serializers
# =============================================

class BOMListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قوائم المواد."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = BillOfMaterials
        fields = (
            'id', 'product', 'product_name', 'name', 'description',
            'version', 'status', 'status_display', 'effective_date',
            'created_by', 'created_by_name', 'items_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_items_count(self, obj):
        return obj.items.count()


class BOMCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء قائمة مواد جديدة."""

    class Meta:
        model = BillOfMaterials
        fields = (
            'product', 'name', 'description', 'version',
            'status', 'effective_date',
        )


class BOMUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث قائمة مواد."""

    class Meta:
        model = BillOfMaterials
        fields = (
            'name', 'description', 'version', 'status', 'effective_date',
        )


class BOMDetailSerializer(BOMListSerializer):
    """مسلسل مفصل لعرض قائمة مواد مع بنودها."""

    items = serializers.SerializerMethodField()
    routing_steps = serializers.SerializerMethodField()

    class Meta(BOMListSerializer.Meta):
        fields = BOMListSerializer.Meta.fields + ('items', 'routing_steps')

    def get_items(self, obj):
        items = obj.items.select_related('material').all()
        return BOMItemSerializer(items, many=True).data

    def get_routing_steps(self, obj):
        steps = obj.routing_steps.select_related('work_center').all()
        return RoutingStepSerializer(steps, many=True).data


# =============================================
# BOMItem Serializers
# =============================================

class BOMItemSerializer(serializers.ModelSerializer):
    """مسلسل لبنود قائمة المواد."""

    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True, default=None)

    class Meta:
        model = BOMItem
        fields = (
            'id', 'bom', 'material', 'material_name', 'material_sku',
            'quantity', 'unit_cost', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class BOMItemCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء بند في قائمة المواد."""

    class Meta:
        model = BOMItem
        fields = ('bom', 'material', 'quantity', 'unit_cost', 'notes')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


class BOMItemUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث بند في قائمة المواد."""

    class Meta:
        model = BOMItem
        fields = ('material', 'quantity', 'unit_cost', 'notes')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


# =============================================
# ProductionOrder Serializers
# =============================================

class ProductionOrderListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض أوامر الإنتاج."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True, default=None)
    bom_name = serializers.CharField(source='bom.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = ProductionOrder
        fields = (
            'id', 'order_number', 'product', 'product_name', 'product_sku',
            'bom', 'bom_name', 'quantity', 'quantity_produced',
            'quantity_defective', 'status', 'status_display',
            'priority', 'priority_display', 'planned_start_date',
            'planned_end_date', 'actual_start_date', 'actual_end_date',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductionOrderCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء أمر إنتاج جديد."""

    class Meta:
        model = ProductionOrder
        fields = (
            'order_number', 'product', 'bom', 'quantity',
            'planned_start_date', 'planned_end_date', 'priority', 'notes',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


class ProductionOrderUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث أمر إنتاج."""

    class Meta:
        model = ProductionOrder
        fields = (
            'bom', 'quantity', 'priority',
            'planned_start_date', 'planned_end_date', 'notes',
        )


# =============================================
# ProductionLog Serializers
# =============================================

class ProductionLogSerializer(serializers.ModelSerializer):
    """مسلسل لعرض سجلات الإنتاج."""

    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    order_number = serializers.CharField(source='production_order.order_number', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, default=None)

    class Meta:
        model = ProductionLog
        fields = (
            'id', 'production_order', 'order_number', 'operation_type',
            'operation_type_display', 'quantity', 'defect_quantity',
            'notes', 'operator', 'operator_name', 'log_date', 'created_at',
        )
        read_only_fields = ('id', 'log_date', 'created_at')


class ProductionLogCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء سجل إنتاج جديد."""

    class Meta:
        model = ProductionLog
        fields = (
            'production_order', 'operation_type', 'quantity',
            'defect_quantity', 'notes', 'operator',
        )


# =============================================
# WorkCenter Serializers
# =============================================

class WorkCenterSerializer(serializers.ModelSerializer):
    """مسلسل لعرض مراكز العمل."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkCenter
        fields = (
            'id', 'name', 'description', 'location', 'capacity',
            'status', 'status_display', 'cost_per_hour',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkCenterCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء مركز عمل جديد."""

    class Meta:
        model = WorkCenter
        fields = ('name', 'description', 'location', 'capacity', 'status', 'cost_per_hour')


class WorkCenterUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث مركز عمل."""

    class Meta:
        model = WorkCenter
        fields = ('name', 'description', 'location', 'capacity', 'status', 'cost_per_hour')


# =============================================
# RoutingStep Serializers
# =============================================

class RoutingStepSerializer(serializers.ModelSerializer):
    """مسلسل لعرض خطوات مسار الإنتاج."""

    work_center_name = serializers.CharField(source='work_center.name', read_only=True)

    class Meta:
        model = RoutingStep
        fields = (
            'id', 'bom', 'step_number', 'work_center', 'work_center_name',
            'operation_name', 'estimated_minutes', 'cost_per_unit',
            'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class RoutingStepCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء خطوة مسار إنتاج جديدة."""

    class Meta:
        model = RoutingStep
        fields = (
            'bom', 'step_number', 'work_center', 'operation_name',
            'estimated_minutes', 'cost_per_unit', 'notes',
        )


class RoutingStepUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث خطوة مسار إنتاج."""

    class Meta:
        model = RoutingStep
        fields = (
            'step_number', 'work_center', 'operation_name',
            'estimated_minutes', 'cost_per_unit', 'notes',
        )


# =============================================
# Manufacturing Stats Serializer
# =============================================

class ManufacturingStatsSerializer(serializers.Serializer):
    """مسلسل لإحصائيات لوحة معلومات التصنيع."""

    total_boms = serializers.IntegerField()
    active_boms = serializers.IntegerField()
    total_production_orders = serializers.IntegerField()
    orders_in_progress = serializers.IntegerField()
    orders_completed = serializers.IntegerField()
    orders_draft = serializers.IntegerField()
    total_work_centers = serializers.IntegerField()
    active_work_centers = serializers.IntegerField()
    work_centers_maintenance = serializers.IntegerField()
    total_routing_steps = serializers.IntegerField()
    total_production_logs = serializers.IntegerField()
