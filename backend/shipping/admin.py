"""
Admin configuration for the Shipping module.
"""

from django.contrib import admin
from .models import (
    ShippingMethod,
    Shipment,
    ShipmentItem,
    ShipmentEvent,
    DeliveryAttempt,
)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'carrier', 'cost_type', 'base_cost', 'cost_per_unit', 'estimated_days', 'is_active')
    list_filter = ('cost_type', 'is_active', 'carrier')
    search_fields = ('name', 'carrier')


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'weight')
    readonly_fields = ('product', 'quantity', 'unit_price', 'weight')
    can_delete = False


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0
    fields = ('event_type', 'location', 'description', 'created_at')
    readonly_fields = ('event_type', 'location', 'description', 'created_at')
    can_delete = False


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('shipment_number', 'customer', 'shipping_method', 'status', 'tracking_number', 'shipping_cost', 'created_at')
    list_filter = ('status', 'shipping_method')
    search_fields = ('shipment_number', 'tracking_number', 'customer__name')
    inlines = [ShipmentItemInline, ShipmentEventInline]


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'product', 'quantity', 'unit_price', 'weight')
    list_filter = ('shipment__status',)
    search_fields = ('shipment__shipment_number', 'product__name')


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'event_type', 'location', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('shipment__shipment_number', 'location')


@admin.register(DeliveryAttempt)
class DeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'attempt_number', 'attempt_date', 'status', 'recipient_name')
    list_filter = ('status',)
    search_fields = ('shipment__shipment_number', 'recipient_name')
