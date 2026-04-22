"""
URL patterns for the Shipping module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Shipping statistics
    path('stats/', views.ShippingStatsView.as_view(), name='shipping-stats'),

    # Shipping Methods
    path('methods/', views.ShippingMethodListView.as_view(), name='shipping-methods'),
    path('methods/<int:pk>/', views.ShippingMethodDetailView.as_view(), name='shipping-method-detail'),

    # Shipments
    path('shipments/', views.ShipmentListView.as_view(), name='shipments'),
    path('shipments/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment-detail'),
    path('shipments/<int:pk>/change-status/', views.ShipmentChangeStatusView.as_view(), name='shipment-change-status'),

    # Shipment Items
    path('items/', views.ShipmentItemListView.as_view(), name='shipment-items'),
    path('items/<int:pk>/', views.ShipmentItemDetailView.as_view(), name='shipment-item-detail'),

    # Shipment Events
    path('events/', views.ShipmentEventListView.as_view(), name='shipment-events'),
    path('events/create/', views.ShipmentEventCreateView.as_view(), name='shipment-event-create'),

    # Delivery Attempts
    path('delivery-attempts/', views.DeliveryAttemptListView.as_view(), name='delivery-attempts'),

    # Export
    path('export/', views.ShippingExportView.as_view(), name='shipping-export'),
]
