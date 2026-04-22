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

    # Contracts
    path('contracts/', ContractListView.as_view(), name='contract-list'),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:pk>/delete/', ContractDeleteView.as_view(), name='contract-delete'),
    path('contracts/<int:pk>/restore/', ContractRestoreView.as_view(), name='contract-restore'),
    path('contracts/<int:pk>/change-status/', ContractChangeStatusView.as_view(), name='contract-change-status'),
    path('contracts/<int:pk>/renew/', ContractRenewView.as_view(), name='contract-renew'),

    # Contract Milestones
    path('milestones/', ContractMilestoneListView.as_view(), name='contract-milestone-list'),
    path('milestones/create/', ContractMilestoneCreateView.as_view(), name='contract-milestone-create'),
    path('milestones/<int:pk>/update/', ContractMilestoneUpdateView.as_view(), name='contract-milestone-update'),
    path('milestones/<int:pk>/', ContractMilestoneDetailView.as_view(), name='contract-milestone-detail'),
    path('milestones/<int:pk>/delete/', ContractMilestoneDeleteView.as_view(), name='contract-milestone-delete'),

    # Contract Payments
    path('payments/', ContractPaymentListView.as_view(), name='contract-payment-list'),
    path('payments/create/', ContractPaymentCreateView.as_view(), name='contract-payment-create'),
    path('payments/<int:pk>/update/', ContractPaymentUpdateView.as_view(), name='contract-payment-update'),
    path('payments/<int:pk>/', ContractPaymentDetailView.as_view(), name='contract-payment-detail'),
    path('payments/<int:pk>/delete/', ContractPaymentDeleteView.as_view(), name='contract-payment-delete'),

    # Excel Export
    path('contracts/export/', ContractExportView.as_view(), name='contract-export'),
]
