"""
Serializers for the Equipment Maintenance module.
Handles Equipment, MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart, and EquipmentInspection
data transformation.
"""

from rest_framework import serializers
from .models import (
    Equipment,
    MaintenanceSchedule,
    MaintenanceWorkOrder,
    MaintenancePart,
    EquipmentInspection,
)


# =============================================
# Equipment Serializers
# =============================================

class EquipmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing equipment."""

    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_name = serializers.CharField(source='assigned_department.name', read_only=True, default=None)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = (
            'id', 'name', 'equipment_number', 'category', 'category_display',
            'brand', 'model_number', 'serial_number', 'location', 'purchase_date',
            'purchase_cost', 'warranty_end', 'status', 'status_display',
            'assigned_department', 'department_name', 'assigned_to', 'assigned_to_name',
            'current_meter_reading', 'image', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None


class EquipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating equipment."""

    class Meta:
        model = Equipment
        fields = (
            'name', 'equipment_number', 'category', 'brand', 'model_number',
            'serial_number', 'location', 'purchase_date', 'purchase_cost',
            'warranty_end', 'status', 'assigned_department', 'assigned_to',
            'current_meter_reading', 'image', 'notes',
        )

    def validate_equipment_number(self, value):
        if Equipment.objects.filter(equipment_number=value).exists():
            raise serializers.ValidationError('رقم المعدة موجود مسبقاً')
        return value


class EquipmentDetailSerializer(EquipmentListSerializer):
    """Detailed equipment serializer with work orders and inspections count."""

    work_orders_count = serializers.SerializerMethodField()
    schedules_count = serializers.SerializerMethodField()
    inspections_count = serializers.SerializerMethodField()

    class Meta(EquipmentListSerializer.Meta):
        fields = EquipmentListSerializer.Meta.fields + (
            'work_orders_count', 'schedules_count', 'inspections_count',
        )

    def get_work_orders_count(self, obj):
        return obj.work_orders.count()

    def get_schedules_count(self, obj):
        return obj.schedules.filter(is_active=True).count()

    def get_inspections_count(self, obj):
        return obj.inspections.count()


# =============================================
# Maintenance Schedule Serializers
# =============================================

class MaintenanceScheduleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing maintenance schedules."""

    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_number = serializers.CharField(source='equipment.equipment_number', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    frequency_type_display = serializers.CharField(source='get_frequency_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = (
            'id', 'equipment', 'equipment_name', 'equipment_number',
            'maintenance_type', 'maintenance_type_display',
            'frequency_type', 'frequency_type_display', 'frequency_value',
            'last_performed', 'next_due', 'assigned_to', 'assigned_to_name',
            'estimated_cost', 'estimated_hours', 'priority', 'priority_display',
            'is_active', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None


class MaintenanceScheduleDetailSerializer(MaintenanceScheduleListSerializer):
    """Detailed maintenance schedule serializer with work orders count."""

    work_orders_count = serializers.SerializerMethodField()

    class Meta(MaintenanceScheduleListSerializer.Meta):
        fields = MaintenanceScheduleListSerializer.Meta.fields + ('work_orders_count',)

    def get_work_orders_count(self, obj):
        return obj.work_orders.count()


# =============================================
# Maintenance Work Order Serializers
# =============================================

class MaintenanceWorkOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing maintenance work orders."""

    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_number = serializers.CharField(source='equipment.equipment_number', read_only=True)
    work_type_display = serializers.CharField(source='get_work_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceWorkOrder
        fields = (
            'id', 'work_order_number', 'equipment', 'equipment_name',
            'equipment_number', 'schedule', 'work_type', 'work_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'description', 'requested_by', 'requested_by_name',
            'assigned_to', 'assigned_to_name', 'started_at', 'completed_at',
            'actual_cost', 'actual_hours', 'parts_used', 'completion_notes',
            'approved_by', 'approved_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name() if obj.requested_by else None

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None


class MaintenanceWorkOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a maintenance work order."""

    class Meta:
        model = MaintenanceWorkOrder
        fields = (
            'equipment', 'schedule', 'work_type', 'priority',
            'description', 'assigned_to',
        )

    def validate_work_order_number(self, value):
        if MaintenanceWorkOrder.objects.filter(work_order_number=value).exists():
            raise serializers.ValidationError('رقم أمر العمل موجود مسبقاً')
        return value


class MaintenanceWorkOrderApproveSerializer(serializers.Serializer):
    """Serializer for approving work orders."""

    assigned_to = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='تعيين المسؤول عن التنفيذ (معرف المستخدم)',
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


class MaintenanceWorkOrderCompleteSerializer(serializers.Serializer):
    """Serializer for completing work orders."""

    actual_cost = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        default=0,
    )
    actual_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        default=0,
    )
    completion_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Maintenance Part Serializers
# =============================================

class MaintenancePartListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing maintenance parts."""

    work_order_number = serializers.CharField(source='work_order.work_order_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default=None)

    class Meta:
        model = MaintenancePart
        fields = (
            'id', 'work_order', 'work_order_number', 'part_name', 'part_number',
            'quantity', 'unit_cost', 'supplier', 'supplier_name', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class MaintenancePartCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a maintenance part."""

    class Meta:
        model = MaintenancePart
        fields = (
            'work_order', 'part_name', 'part_number', 'quantity',
            'unit_cost', 'supplier', 'notes',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


class MaintenancePartDetailSerializer(MaintenancePartListSerializer):
    """Detailed maintenance part serializer with total cost."""

    total_cost = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta(MaintenancePartListSerializer.Meta):
        fields = MaintenancePartListSerializer.Meta.fields + ('total_cost',)


# =============================================
# Equipment Inspection Serializers
# =============================================

class EquipmentInspectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing equipment inspections."""

    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_number = serializers.CharField(source='equipment.equipment_number', read_only=True)
    inspection_type_display = serializers.CharField(source='get_inspection_type_display', read_only=True)
    condition_rating_display = serializers.CharField(source='get_condition_rating_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    inspector_name = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentInspection
        fields = (
            'id', 'equipment', 'equipment_name', 'equipment_number',
            'inspection_type', 'inspection_type_display', 'inspector',
            'inspector_name', 'inspection_date', 'condition_rating',
            'condition_rating_display', 'findings', 'recommendations',
            'next_inspection', 'status', 'status_display', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_inspector_name(self, obj):
        return obj.inspector.get_full_name() if obj.inspector else None


class EquipmentInspectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an equipment inspection."""

    class Meta:
        model = EquipmentInspection
        fields = (
            'equipment', 'inspection_type', 'inspector', 'condition_rating',
            'findings', 'recommendations', 'next_inspection', 'status',
        )


# =============================================
# Equipment Maintenance Stats Serializer
# =============================================

class EquipmentMaintStatsSerializer(serializers.Serializer):
    """Serializer for Equipment Maintenance dashboard statistics."""

    total_equipment = serializers.IntegerField()
    operational_equipment = serializers.IntegerField()
    maintenance_equipment = serializers.IntegerField()
    broken_equipment = serializers.IntegerField()
    retired_equipment = serializers.IntegerField()
    total_work_orders = serializers.IntegerField()
    pending_work_orders = serializers.IntegerField()
    in_progress_work_orders = serializers.IntegerField()
    completed_work_orders = serializers.IntegerField()
    active_schedules = serializers.IntegerField()
    overdue_schedules = serializers.IntegerField()
    total_inspections = serializers.IntegerField()
    passed_inspections = serializers.IntegerField()
    failed_inspections = serializers.IntegerField()
    total_maintenance_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_work_orders_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
