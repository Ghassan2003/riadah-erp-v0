"""
URL patterns for the Assets module.
"""

from django.urls import path
from .views import (
    AssetCategoryListView, AssetCategoryDetailView, AssetCategoryDeleteView,
    FixedAssetListView, FixedAssetDetailView, FixedAssetDeleteView, FixedAssetRestoreView,
    AssetTransferListView, AssetTransferCreateView,
    AssetTransferDetailView, AssetTransferUpdateView, AssetTransferDeleteView,
    AssetMaintenanceListView, AssetMaintenanceCreateView, AssetMaintenanceUpdateView,
    AssetMaintenanceDetailView, AssetMaintenanceDeleteView,
    AssetDisposalListView, AssetDisposalCreateView,
    AssetDisposalDetailView, AssetDisposalUpdateView, AssetDisposalDeleteView,
    AssetDepreciationView, AssetStatsView, AssetExportView,
)

urlpatterns = [
    # Asset statistics
    path('stats/', AssetStatsView.as_view(), name='asset-stats'),

    # Asset Categories
    path('categories/', AssetCategoryListView.as_view(), name='asset-category-list'),
    path('categories/<int:pk>/', AssetCategoryDetailView.as_view(), name='asset-category-detail'),
    path('categories/<int:pk>/delete/', AssetCategoryDeleteView.as_view(), name='asset-category-delete'),

    # Fixed Assets
    path('assets/', FixedAssetListView.as_view(), name='fixed-asset-list'),
    path('assets/<int:pk>/', FixedAssetDetailView.as_view(), name='fixed-asset-detail'),
    path('assets/<int:pk>/delete/', FixedAssetDeleteView.as_view(), name='fixed-asset-delete'),
    path('assets/<int:pk>/restore/', FixedAssetRestoreView.as_view(), name='fixed-asset-restore'),

    # Asset Transfers
    path('transfers/', AssetTransferListView.as_view(), name='asset-transfer-list'),
    path('transfers/create/', AssetTransferCreateView.as_view(), name='asset-transfer-create'),
    path('transfers/<int:pk>/', AssetTransferDetailView.as_view(), name='asset-transfer-detail'),
    path('transfers/<int:pk>/update/', AssetTransferUpdateView.as_view(), name='asset-transfer-update'),
    path('transfers/<int:pk>/delete/', AssetTransferDeleteView.as_view(), name='asset-transfer-delete'),

    # Asset Maintenance
    path('maintenances/', AssetMaintenanceListView.as_view(), name='asset-maintenance-list'),
    path('maintenances/create/', AssetMaintenanceCreateView.as_view(), name='asset-maintenance-create'),
    path('maintenances/<int:pk>/', AssetMaintenanceDetailView.as_view(), name='asset-maintenance-detail'),
    path('maintenances/<int:pk>/update/', AssetMaintenanceUpdateView.as_view(), name='asset-maintenance-update'),
    path('maintenances/<int:pk>/delete/', AssetMaintenanceDeleteView.as_view(), name='asset-maintenance-delete'),

    # Asset Disposals
    path('disposals/', AssetDisposalListView.as_view(), name='asset-disposal-list'),
    path('disposals/create/', AssetDisposalCreateView.as_view(), name='asset-disposal-create'),
    path('disposals/<int:pk>/', AssetDisposalDetailView.as_view(), name='asset-disposal-detail'),
    path('disposals/<int:pk>/update/', AssetDisposalUpdateView.as_view(), name='asset-disposal-update'),
    path('disposals/<int:pk>/delete/', AssetDisposalDeleteView.as_view(), name='asset-disposal-delete'),

    # Depreciation
    path('depreciation/', AssetDepreciationView.as_view(), name='asset-depreciation'),

    # Excel Export
    path('export/', AssetExportView.as_view(), name='asset-export'),
    path('assets/export/', AssetExportView.as_view(), name='asset-export-detailed'),
]
