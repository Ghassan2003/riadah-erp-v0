"""
URL patterns for the Import/Export module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Import/Export statistics
    path('stats/', views.ImportExportStatsView.as_view(), name='import-export-stats'),

    # Import Orders
    path('import-orders/', views.ImportOrderListView.as_view(), name='import-orders'),
    path('import-orders/create/', views.ImportOrderCreateView.as_view(), name='import-order-create'),
    path('import-orders/<int:pk>/', views.ImportOrderDetailView.as_view(), name='import-order-detail'),
    path('import-orders/<int:pk>/change-status/', views.ImportOrderChangeStatusView.as_view(), name='import-order-change-status'),

    # Import Items
    path('import-items/', views.ImportItemListView.as_view(), name='import-items'),
    path('import-items/<int:pk>/', views.ImportItemDetailView.as_view(), name='import-item-detail'),

    # Export Orders
    path('export-orders/', views.ExportOrderListView.as_view(), name='export-orders'),
    path('export-orders/create/', views.ExportOrderCreateView.as_view(), name='export-order-create'),
    path('export-orders/<int:pk>/', views.ExportOrderDetailView.as_view(), name='export-order-detail'),
    path('export-orders/<int:pk>/change-status/', views.ExportOrderChangeStatusView.as_view(), name='export-order-change-status'),

    # Export Items
    path('export-items/', views.ExportItemListView.as_view(), name='export-items'),
    path('export-items/<int:pk>/', views.ExportItemDetailView.as_view(), name='export-item-detail'),

    # Customs Declarations
    path('customs-declarations/', views.CustomsDeclarationListView.as_view(), name='customs-declarations'),
    path('customs-declarations/create/', views.CustomsDeclarationCreateView.as_view(), name='customs-declaration-create'),
    path('customs-declarations/<int:pk>/', views.CustomsDeclarationDetailView.as_view(), name='customs-declaration-detail'),
    path('customs-declarations/<int:pk>/change-status/', views.CustomsDeclarationChangeStatusView.as_view(), name='customs-declaration-change-status'),

    # Export to Excel
    path('export/', views.ImportExportExportView.as_view(), name='import-export-export'),
]
