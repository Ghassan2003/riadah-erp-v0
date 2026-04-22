"""
URL patterns for the Warehouse module.
"""

from django.urls import path
from .views import (
    WarehouseListView, WarehouseDetailView, WarehouseDeleteView, WarehouseRestoreView,
    WarehouseStockListView, WarehouseStockCreateView, WarehouseStockUpdateView,
    WarehouseStockDetailView, WarehouseStockDeleteView,
    StockTransferListView, StockTransferCreateView, StockTransferApproveView, StockTransferReceiveView,
    StockTransferDetailView, StockTransferUpdateView, StockTransferCancelView,
    StockAdjustmentListView, StockAdjustmentCreateView,
    StockAdjustmentDetailView, StockAdjustmentUpdateView, StockAdjustmentDeleteView,
    StockCountListView, StockCountDetailView, StockCountCreateView, StockCountCompleteView,
    StockCountUpdateView, StockCountDeleteView,
    WarehouseStatsView,
    WarehouseExportView, StockTransferExportView, StockAdjustmentExportView,
)

urlpatterns = [
    # Warehouse statistics
    path('stats/', WarehouseStatsView.as_view(), name='warehouse-stats'),

    # Warehouses
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse-delete'),
    path('warehouses/<int:pk>/restore/', WarehouseRestoreView.as_view(), name='warehouse-restore'),

    # Warehouse Stock
    path('stocks/', WarehouseStockListView.as_view(), name='stock-list'),
    path('stocks/create/', WarehouseStockCreateView.as_view(), name='stock-create'),
    path('stocks/<int:pk>/', WarehouseStockDetailView.as_view(), name='stock-detail'),
    path('stocks/<int:pk>/update/', WarehouseStockUpdateView.as_view(), name='stock-update'),
    path('stocks/<int:pk>/delete/', WarehouseStockDeleteView.as_view(), name='stock-delete'),

    # Stock Transfers
    path('transfers/', StockTransferListView.as_view(), name='transfer-list'),
    path('transfers/create/', StockTransferCreateView.as_view(), name='transfer-create'),
    path('transfers/<int:pk>/', StockTransferDetailView.as_view(), name='transfer-detail'),
    path('transfers/<int:pk>/update/', StockTransferUpdateView.as_view(), name='transfer-update'),
    path('transfers/<int:pk>/approve/', StockTransferApproveView.as_view(), name='transfer-approve'),
    path('transfers/<int:pk>/receive/', StockTransferReceiveView.as_view(), name='transfer-receive'),
    path('transfers/<int:pk>/cancel/', StockTransferCancelView.as_view(), name='transfer-cancel'),

    # Stock Adjustments
    path('adjustments/', StockAdjustmentListView.as_view(), name='adjustment-list'),
    path('adjustments/create/', StockAdjustmentCreateView.as_view(), name='adjustment-create'),
    path('adjustments/<int:pk>/', StockAdjustmentDetailView.as_view(), name='adjustment-detail'),
    path('adjustments/<int:pk>/update/', StockAdjustmentUpdateView.as_view(), name='adjustment-update'),
    path('adjustments/<int:pk>/delete/', StockAdjustmentDeleteView.as_view(), name='adjustment-delete'),

    # Stock Counts
    path('counts/', StockCountListView.as_view(), name='count-list'),
    path('counts/<int:pk>/', StockCountDetailView.as_view(), name='count-detail'),
    path('counts/create/', StockCountCreateView.as_view(), name='count-create'),
    path('counts/<int:pk>/update/', StockCountUpdateView.as_view(), name='count-update'),
    path('counts/<int:pk>/complete/', StockCountCompleteView.as_view(), name='count-complete'),
    path('counts/<int:pk>/delete/', StockCountDeleteView.as_view(), name='count-delete'),

    # Excel Export
    path('export/', WarehouseExportView.as_view(), name='warehouse-export'),
    path('warehouses/export/', WarehouseExportView.as_view(), name='warehouse-export-detailed'),
    path('transfers/export/', StockTransferExportView.as_view(), name='transfer-export'),
    path('adjustments/export/', StockAdjustmentExportView.as_view(), name='adjustment-export'),
]
