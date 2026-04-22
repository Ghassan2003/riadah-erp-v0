"""
URL patterns for the Payments module.
"""

from django.urls import path
from .views import (
    PaymentAccountListView,
    PaymentAccountCreateView,
    PaymentAccountDetailView,
    PaymentAccountUpdateView,
    PaymentAccountDeleteView,
    FinancialTransactionListView,
    FinancialTransactionCreateView,
    FinancialTransactionDetailView,
    FinancialTransactionDeleteView,
    ChequeListView,
    ChequeCreateView,
    ChequeDetailView,
    ChequeDeleteView,
    ChequeStatusUpdateView,
    ReconciliationListView,
    ReconciliationCreateView,
    ReconciliationDetailView,
    ReconciliationUpdateView,
    ReconciliationDeleteView,
    PaymentStatsView,
    PaymentExportView,
)

urlpatterns = [
    # Payment statistics
    path('stats/', PaymentStatsView.as_view(), name='payment-stats'),

    # Payment Accounts
    path('accounts/', PaymentAccountListView.as_view(), name='account-list'),
    path('accounts/create/', PaymentAccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/', PaymentAccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/update/', PaymentAccountUpdateView.as_view(), name='account-update'),
    path('accounts/<int:pk>/delete/', PaymentAccountDeleteView.as_view(), name='account-delete'),

    # Financial Transactions
    path('transactions/', FinancialTransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', FinancialTransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<int:pk>/', FinancialTransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/<int:pk>/delete/', FinancialTransactionDeleteView.as_view(), name='transaction-delete'),

    # Cheques
    path('cheques/', ChequeListView.as_view(), name='cheque-list'),
    path('cheques/create/', ChequeCreateView.as_view(), name='cheque-create'),
    path('cheques/<int:pk>/status/', ChequeStatusUpdateView.as_view(), name='cheque-status'),
    path('cheques/<int:pk>/', ChequeDetailView.as_view(), name='cheque-detail'),
    path('cheques/<int:pk>/delete/', ChequeDeleteView.as_view(), name='cheque-delete'),

    # Reconciliations
    path('reconciliations/', ReconciliationListView.as_view(), name='reconciliation-list'),
    path('reconciliations/create/', ReconciliationCreateView.as_view(), name='reconciliation-create'),
    path('reconciliations/<int:pk>/', ReconciliationDetailView.as_view(), name='reconciliation-detail'),
    path('reconciliations/<int:pk>/update/', ReconciliationUpdateView.as_view(), name='reconciliation-update'),
    path('reconciliations/<int:pk>/delete/', ReconciliationDeleteView.as_view(), name='reconciliation-delete'),

    # Excel Export
    path('export/', PaymentExportView.as_view(), name='payment-export'),
]
