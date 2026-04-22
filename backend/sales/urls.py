"""
URL patterns for the Sales module.
"""

from django.urls import path
from .views import (
    CustomerListView,
    CustomerDetailView,
    CustomerSoftDeleteView,
    SalesOrderListView,
    SalesOrderDetailView,
    SalesOrderCreateView,
    SalesOrderStatusView,
    SalesOrderUpdateView,
    SalesOrderDeleteView,
    SalesStatsView,
    CustomerExportView,
    SalesOrderExportView,
)

urlpatterns = [
    # Sales statistics
    path('stats/', SalesStatsView.as_view(), name='sales-stats'),

    # Customer CRUD
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<int:pk>/soft-delete/', CustomerSoftDeleteView.as_view(), name='customer-soft-delete'),

    # Sales Order operations
    path('orders/', SalesOrderListView.as_view(), name='order-list'),
    path('orders/create/', SalesOrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/', SalesOrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/change-status/', SalesOrderStatusView.as_view(), name='order-change-status'),
    path('orders/<int:pk>/update/', SalesOrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/delete/', SalesOrderDeleteView.as_view(), name='order-delete'),

    # Export
    path('customers/export/', CustomerExportView.as_view(), name='customer-export'),
    path('orders/export/', SalesOrderExportView.as_view(), name='order-export'),
]
