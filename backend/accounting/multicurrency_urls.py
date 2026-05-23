"""
URL patterns for Multi-Branch and Multi-Currency support.
"""

from django.urls import path
from .multicurrency_views import (
    CurrencyListView,
    CurrencyCreateView,
    CurrencyDetailView,
    CurrencyUpdateView,
    CurrencyRateUpdateView,
    ExchangeRateListView,
    CurrencyConvertView,
    BranchListView,
    BranchCreateView,
    BranchDetailView,
    BranchUpdateView,
)

urlpatterns = [
    # Currencies
    path('currencies/', CurrencyListView.as_view(), name='currency-list'),
    path('currencies/create/', CurrencyCreateView.as_view(), name='currency-create'),
    path('currencies/<int:pk>/', CurrencyDetailView.as_view(), name='currency-detail'),
    path('currencies/<int:pk>/update/', CurrencyUpdateView.as_view(), name='currency-update'),
    path('currencies/<int:pk>/update-rate/', CurrencyRateUpdateView.as_view(), name='currency-rate-update'),
    path('currencies/<int:pk>/exchange-rates/', ExchangeRateListView.as_view(), name='exchange-rate-list'),
    path('currencies/convert/', CurrencyConvertView.as_view(), name='currency-convert'),
    # Branches
    path('branches/', BranchListView.as_view(), name='branch-list'),
    path('branches/create/', BranchCreateView.as_view(), name='branch-create'),
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch-detail'),
    path('branches/<int:pk>/update/', BranchUpdateView.as_view(), name='branch-update'),
]
