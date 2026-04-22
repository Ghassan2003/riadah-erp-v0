"""
URL patterns for the Purchases module.
"""

from django.urls import path
from .views import (
    PurchaseStatsView,
    SupplierListView,
    SupplierDetailView,
    SupplierSoftDeleteView,
    SupplierRestoreView,
    PurchaseOrderListView,
    PurchaseOrderDetailView,
    PurchaseOrderCreateView,
    PurchaseOrderUpdateView,
    PurchaseOrderDeleteView,
    PurchaseOrderStatusView,
    SupplierExportView,
    PurchaseOrderExportView,
)

urlpatterns = [
    # Purchases statistics
    path('stats/', PurchaseStatsView.as_view(), name='purchase-stats'),

    # Supplier CRUD
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
    path('suppliers/<int:pk>/soft-delete/', SupplierSoftDeleteView.as_view(), name='supplier-soft-delete'),
    path('suppliers/<int:pk>/restore/', SupplierRestoreView.as_view(), name='supplier-restore'),

    # Purchase Order operations
    path('orders/', PurchaseOrderListView.as_view(), name='purchase-order-list'),
    path('orders/create/', PurchaseOrderCreateView.as_view(), name='purchase-order-create'),
    path('orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),
    path('orders/<int:pk>/update/', PurchaseOrderUpdateView.as_view(), name='purchase-order-update'),
    path('orders/<int:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='purchase-order-delete'),
    path('orders/<int:pk>/change-status/', PurchaseOrderStatusView.as_view(), name='purchase-order-change-status'),

    # Excel Export
    path('suppliers/export/', SupplierExportView.as_view(), name='supplier-export'),
    path('orders/export/', PurchaseOrderExportView.as_view(), name='purchase-order-export'),
]
