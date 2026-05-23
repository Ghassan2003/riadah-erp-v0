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
    PurchaseRequisitionListView,
    PurchaseRequisitionDetailView,
    PurchaseRequisitionApproveView,
    PurchaseRequisitionConvertView,
    PurchaseRequisitionDeleteView,
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

    # Purchase Requisition operations
    path('requisitions/', PurchaseRequisitionListView.as_view(), name='purchase-requisition-list'),
    path('requisitions/create/', PurchaseRequisitionListView.as_view(), name='purchase-requisition-create'),
    path('requisitions/<int:pk>/', PurchaseRequisitionDetailView.as_view(), name='purchase-requisition-detail'),
    path('requisitions/<int:pk>/approve/', PurchaseRequisitionApproveView.as_view(), name='purchase-requisition-approve'),
    path('requisitions/<int:pk>/convert/', PurchaseRequisitionConvertView.as_view(), name='purchase-requisition-convert'),
    path('requisitions/<int:pk>/delete/', PurchaseRequisitionDeleteView.as_view(), name='purchase-requisition-delete'),
]
