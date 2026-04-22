"""
URL patterns for the Accounting module - Phase 4.
"""

from django.urls import path
from .views import (
    AccountListView,
    AccountDetailView,
    AccountCreateView,
    AccountUpdateView,
    AccountDeleteView,
    JournalEntryListView,
    JournalEntryDetailView,
    JournalEntryCreateView,
    JournalEntryUpdateView,
    JournalEntryPostView,
    JournalEntryReverseView,
    IncomeStatementView,
    BalanceSheetView,
    AccountingStatsView,
    IncomeStatementPDFView,
    BalanceSheetPDFView,
    AccountExportView,
    JournalEntryExportView,
)

urlpatterns = [
    # Accounting statistics
    path('stats/', AccountingStatsView.as_view(), name='accounting-stats'),

    # Chart of Accounts
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('accounts/create/', AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/update/', AccountUpdateView.as_view(), name='account-update'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account-delete'),

    # Journal Entries
    path('entries/', JournalEntryListView.as_view(), name='entry-list'),
    path('entries/create/', JournalEntryCreateView.as_view(), name='entry-create'),
    path('entries/<int:pk>/', JournalEntryDetailView.as_view(), name='entry-detail'),
    path('entries/<int:pk>/update/', JournalEntryUpdateView.as_view(), name='entry-update'),
    path('entries/<int:pk>/post/', JournalEntryPostView.as_view(), name='entry-post'),
    path('entries/<int:pk>/reverse/', JournalEntryReverseView.as_view(), name='entry-reverse'),

    # Financial Reports
    path('reports/income-statement/', IncomeStatementView.as_view(), name='income-statement'),
    path('reports/balance-sheet/', BalanceSheetView.as_view(), name='balance-sheet'),

    # PDF Reports
    path('reports/income-statement/pdf/', IncomeStatementPDFView.as_view(), name='income-statement-pdf'),
    path('reports/balance-sheet/pdf/', BalanceSheetPDFView.as_view(), name='balance-sheet-pdf'),

    # Excel Export
    path('accounts/export/', AccountExportView.as_view(), name='account-export'),
    path('entries/export/', JournalEntryExportView.as_view(), name='entry-export'),
]
