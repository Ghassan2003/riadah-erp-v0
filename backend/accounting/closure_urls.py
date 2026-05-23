"""
أنماط عناوين URL لوحدة الإغلاق المحاسبي الدوري.
"""

from django.urls import path
from .closure_views import (
    FiscalYearListView,
    FiscalYearCreateView,
    FiscalYearDetailView,
    FiscalYearCloseView,
    FiscalPeriodDetailView,
    FiscalPeriodCloseView,
    FiscalPeriodReopenView,
    FiscalPeriodBalancesView,
)

urlpatterns = [
    # السنوات المالية
    path('fiscal-years/', FiscalYearListView.as_view(), name='fiscal-year-list'),
    path('fiscal-years/create/', FiscalYearCreateView.as_view(), name='fiscal-year-create'),
    path('fiscal-years/<int:pk>/', FiscalYearDetailView.as_view(), name='fiscal-year-detail'),
    path('fiscal-years/<int:pk>/close/', FiscalYearCloseView.as_view(), name='fiscal-year-close'),

    # الفترات المحاسبية
    path('fiscal-periods/<int:pk>/', FiscalPeriodDetailView.as_view(), name='fiscal-period-detail'),
    path('fiscal-periods/<int:pk>/close/', FiscalPeriodCloseView.as_view(), name='fiscal-period-close'),
    path('fiscal-periods/<int:pk>/reopen/', FiscalPeriodReopenView.as_view(), name='fiscal-period-reopen'),
    path('fiscal-periods/<int:pk>/balances/', FiscalPeriodBalancesView.as_view(), name='fiscal-period-balances'),
]
