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
    # Price Lists
    path('price-lists/', views.PriceListListView.as_view(), name='pos-price-lists'),
    path('price-lists/<int:pk>/', views.PriceListDetailView.as_view(), name='pos-price-list-detail'),
    path('price-lists/<int:pk>/delete/', views.PriceListDeleteView.as_view(), name='pos-price-list-delete'),
    # Discount Rules
    path('discount-rules/', views.DiscountRuleListView.as_view(), name='pos-discount-rules'),
    path('discount-rules/<int:pk>/', views.DiscountRuleDetailView.as_view(), name='pos-discount-rule-detail'),
    path('discount-rules/<int:pk>/delete/', views.DiscountRuleDeleteView.as_view(), name='pos-discount-rule-delete'),
    path('discount-rules/apply/', views.DiscountRuleApplyView.as_view(), name='pos-discount-rule-apply'),
    # Promo Codes
    path('promo-codes/', views.PromoCodeListView.as_view(), name='pos-promo-codes'),
    path('promo-codes/<int:pk>/', views.PromoCodeDetailView.as_view(), name='pos-promo-code-detail'),
    path('promo-codes/<int:pk>/delete/', views.PromoCodeDeleteView.as_view(), name='pos-promo-code-delete'),
    path('promo-codes/validate/', views.PromoCodeValidateView.as_view(), name='pos-promo-code-validate'),
    # Loyalty Programs
    path('loyalty-programs/', views.LoyaltyProgramListView.as_view(), name='pos-loyalty-programs'),
    path('loyalty-programs/<int:pk>/', views.LoyaltyProgramDetailView.as_view(), name='pos-loyalty-program-detail'),
    path('loyalty-programs/<int:pk>/delete/', views.LoyaltyProgramDeleteView.as_view(), name='pos-loyalty-program-delete'),
    path('loyalty/balance/', views.LoyaltyBalanceView.as_view(), name='pos-loyalty-balance'),
    path('loyalty/redeem/', views.LoyaltyRedeemView.as_view(), name='pos-loyalty-redeem'),
    path('loyalty/transactions/', views.LoyaltyTransactionListView.as_view(), name='pos-loyalty-transactions'),
    # Restaurant Tables
    path('tables/', views.RestaurantTableListView.as_view(), name='pos-tables'),
    path('tables/<int:pk>/', views.RestaurantTableDetailView.as_view(), name='pos-table-detail'),
    path('tables/<int:pk>/status/', views.RestaurantTableStatusView.as_view(), name='pos-table-status'),
    # Installments
    path('installments/', views.InstallmentPlanListView.as_view(), name='pos-installments'),
    path('installments/<int:pk>/', views.InstallmentPlanDetailView.as_view(), name='pos-installment-detail'),
    path('installments/stats/', views.InstallmentStatsView.as_view(), name='pos-installment-stats'),
    path('installment-payments/', views.InstallmentPaymentListView.as_view(), name='pos-installment-payments'),
    path('installment-payments/<int:pk>/', views.InstallmentPaymentDetailView.as_view(), name='pos-installment-payment-detail'),
]
