"""
ERP System URL Configuration - Phase 5.
Routes API endpoints to their respective apps.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    # Dashboard API
    path('api/dashboard/stats/', core_views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/dashboard/live-stats/', core_views.DashboardLiveStatsView.as_view(), name='dashboard-live-stats'),

    # PDF Reports - All Modules
    path('api/reports/pdf/<str:module>/', core_views.PDFReportView.as_view(), name='module-pdf-report'),

    # Financial Reports - Enhanced
    path('api/reports/cash-flow/pdf/', core_views.CashFlowPDFView.as_view(), name='cash-flow-pdf'),
    path('api/reports/cash-flow/', core_views.CashFlowAPIView.as_view(), name='cash-flow-api'),
    path('api/reports/income-statement/enhanced/pdf/', core_views.EnhancedIncomeStatementPDFView.as_view(), name='enhanced-income-pdf'),
    path('api/reports/balance-sheet/enhanced/pdf/', core_views.EnhancedBalanceSheetPDFView.as_view(), name='enhanced-balance-pdf'),

    # Advanced Analytics Reports
    path('api/reports/sales-analytics/', core_views.SalesAnalyticsView.as_view(), name='sales-analytics'),
    path('api/reports/inventory-analytics/', core_views.InventoryAnalyticsView.as_view(), name='inventory-analytics'),
    path('api/reports/financial-analytics/', core_views.FinancialAnalyticsView.as_view(), name='financial-analytics'),
    path('api/reports/hr-analytics/', core_views.HRAnalyticsView.as_view(), name='hr-analytics'),

    # Django admin panel
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('users.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/purchases/', include('purchases.urls')),
    path('api/accounting/', include('accounting.urls')),
    path('api/hr/', include('hr.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/audit-log/', include('auditlog.urls')),
    path('api/maintenance/', include('maintenance.urls')),
    path('api/videos/', include('videos.urls')),
    path('api/payroll/', include('payroll.urls')),
    path('api/invoicing/', include('invoicing.urls')),
    path('api/pos/', include('pos.urls')),
    path('api/warehouse/', include('warehouse.urls')),
    path('api/assets/', include('assets.urls')),
    path('api/contracts/', include('contracts.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/attachments/', include('attachments.urls')),
    path('api/budget/', include('budget.urls')),
    path('api/tenders/', include('tenders.urls')),
    path('api/manufacturing/', include('manufacturing.urls')),
    path('api/shipping/', include('shipping.urls')),
    path('api/insurance/', include('insurance.urls')),
    path('api/import-export/', include('importexport.urls')),
    path('api/equip-maint/', include('equipmaint.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/internal-audit/', include('internalaudit.urls')),

    # System endpoints
    path('api/system/info/', core_views.SystemInfoView.as_view(), name='system-info'),
    path('api/system/backup/', core_views.SystemBackupView.as_view(), name='system-backup'),

    # DRF login/logout (optional, for browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
