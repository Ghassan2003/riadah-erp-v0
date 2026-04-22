"""
URL patterns for the Contracts module.
"""

from django.urls import path
from .views import (
    ContractListView, ContractDetailView, ContractDeleteView, ContractRestoreView,
    ContractChangeStatusView, ContractRenewView,
    ContractMilestoneListView, ContractMilestoneCreateView, ContractMilestoneUpdateView,
    ContractMilestoneDetailView, ContractMilestoneDeleteView,
    ContractPaymentListView, ContractPaymentCreateView, ContractPaymentUpdateView,
    ContractPaymentDetailView, ContractPaymentDeleteView,
    ContractStatsView, ContractExportView,
)

urlpatterns = [
    # Contract statistics
    path('stats/', ContractStatsView.as_view(), name='contract-stats'),

    # Contracts - CRUD
    path('', ContractListView.as_view(), name='contract-list'),
    path('create/', ContractListView.as_view(), name='contract-create'),
    path('<int:pk>/', ContractDetailView.as_view(), name='contract-detail'),
    path('<int:pk>/delete/', ContractDeleteView.as_view(), name='contract-delete'),
    path('<int:pk>/restore/', ContractRestoreView.as_view(), name='contract-restore'),
    path('<int:pk>/change-status/', ContractChangeStatusView.as_view(), name='contract-change-status'),
    path('<int:pk>/renew/', ContractRenewView.as_view(), name='contract-renew'),

    # Contract Milestones
    path('milestones/', ContractMilestoneListView.as_view(), name='contract-milestone-list'),
    path('milestones/create/', ContractMilestoneCreateView.as_view(), name='contract-milestone-create'),
    path('milestones/<int:pk>/', ContractMilestoneDetailView.as_view(), name='contract-milestone-detail'),
    path('milestones/<int:pk>/update/', ContractMilestoneUpdateView.as_view(), name='contract-milestone-update'),
    path('milestones/<int:pk>/delete/', ContractMilestoneDeleteView.as_view(), name='contract-milestone-delete'),

    # Contract Payments
    path('contract-payments/', ContractPaymentListView.as_view(), name='contract-payment-list'),
    path('contract-payments/create/', ContractPaymentCreateView.as_view(), name='contract-payment-create'),
    path('contract-payments/<int:pk>/', ContractPaymentDetailView.as_view(), name='contract-payment-detail'),
    path('contract-payments/<int:pk>/update/', ContractPaymentUpdateView.as_view(), name='contract-payment-update'),
    path('contract-payments/<int:pk>/delete/', ContractPaymentDeleteView.as_view(), name='contract-payment-delete'),

    # Excel Export
    path('export/', ContractExportView.as_view(), name='contract-export'),
]
