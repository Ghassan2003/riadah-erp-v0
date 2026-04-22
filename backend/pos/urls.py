from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.POSStatsView.as_view(), name='pos-stats'),
    # Shifts
    path('shifts/', views.POSShiftListView.as_view(), name='pos-shifts'),
    path('shifts/open/', views.POSShiftOpenView.as_view(), name='pos-shift-open'),
    path('shifts/<int:pk>/close/', views.POSShiftCloseView.as_view(), name='pos-shift-close'),
    path('shifts/<int:pk>/', views.POSShiftDetailView.as_view(), name='pos-shift-detail'),
    # Sales
    path('sales/', views.POSSaleListView.as_view(), name='pos-sales'),
    path('sales/create/', views.POSSaleCreateView.as_view(), name='pos-sale-create'),
    path('sales/<int:pk>/', views.POSSaleDetailView.as_view(), name='pos-sale-detail'),
    path('sales/<int:pk>/void/', views.POSSaleVoidView.as_view(), name='pos-sale-void'),
    # Refunds
    path('refunds/', views.POSRefundListView.as_view(), name='pos-refunds'),
    path('refunds/create/', views.POSRefundCreateView.as_view(), name='pos-refund-create'),
    path('refunds/<int:pk>/', views.POSRefundDetailView.as_view(), name='pos-refund-detail'),
    # Holds
    path('holds/', views.POSHoldListView.as_view(), name='pos-holds'),
    path('holds/create/', views.POSHoldCreateView.as_view(), name='pos-hold-create'),
    path('holds/<int:pk>/', views.POSHoldDetailView.as_view(), name='pos-hold-detail'),
    path('holds/<int:pk>/delete/', views.POSHoldDeleteView.as_view(), name='pos-hold-delete'),
    # Cash drawer
    path('drawer/', views.CashDrawerTransactionListView.as_view(), name='pos-drawer'),
    path('drawer/create/', views.CashDrawerTransactionCreateView.as_view(), name='pos-drawer-create'),
    path('drawer/<int:pk>/', views.CashDrawerTransactionDetailView.as_view(), name='pos-drawer-detail'),
    path('export/', views.POSExportView.as_view(), name='pos-export'),
]
