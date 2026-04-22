"""
URL patterns for the inventory app.
"""

from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    ProductSoftDeleteView,
    ProductRestoreView,
    InventoryStatsView,
    ProductExportView,
)

urlpatterns = [
    # Inventory statistics (for dashboard)
    path('stats/', InventoryStatsView.as_view(), name='inventory-stats'),

    # Product CRUD
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # Soft delete and restore
    path('products/<int:pk>/soft-delete/', ProductSoftDeleteView.as_view(), name='product-soft-delete'),
    path('products/<int:pk>/restore/', ProductRestoreView.as_view(), name='product-restore'),

    # Export
    path('products/export/', ProductExportView.as_view(), name='product-export'),
]
