"""
URL Configuration for Startup Finance module.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    # 1. Startup Profile
    path('profiles/', views.StartupProfileListCreateView.as_view(), name='startup-profile-list'),
    path('profiles/<int:pk>/', views.StartupProfileDetailView.as_view(), name='startup-profile-detail'),

    # 2. Funding Rounds
    path('funding-rounds/', views.FundingRoundListCreateView.as_view(), name='funding-round-list'),
    path('funding-rounds/<int:pk>/', views.FundingRoundDetailView.as_view(), name='funding-round-detail'),

    # 3. Burn Rate Entries
    path('burn-rate/', views.BurnRateEntryListCreateView.as_view(), name='burn-rate-list'),
    path('burn-rate/<int:pk>/', views.BurnRateEntryDetailView.as_view(), name='burn-rate-detail'),

    # 4. Subscription Plans
    path('subscription-plans/', views.SubscriptionPlanListCreateView.as_view(), name='subscription-plan-list'),
    path('subscription-plans/<int:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),

    # 5. Subscription Cycles
    path('subscriptions/', views.SubscriptionCycleListCreateView.as_view(), name='subscription-cycle-list'),
    path('subscriptions/<int:pk>/', views.SubscriptionCycleDetailView.as_view(), name='subscription-cycle-detail'),

    # 6. Customer Metrics
    path('customer-metrics/', views.CustomerMetricListCreateView.as_view(), name='customer-metric-list'),
    path('customer-metrics/<int:pk>/', views.CustomerMetricDetailView.as_view(), name='customer-metric-detail'),

    # 7. Financial Entries
    path('entries/', views.FinancialEntryListCreateView.as_view(), name='financial-entry-list'),
    path('entries/<int:pk>/', views.FinancialEntryDetailView.as_view(), name='financial-entry-detail'),

    # 8. Financial KPIs
    path('kpis/', views.FinancialKPIListView.as_view(), name='financial-kpi-list'),

    # 9. لوحة تحكم المؤسسين
    path('dashboard/', views.FounderDashboardView.as_view(), name='founder-dashboard'),

    # 10. حساب KPIs
    path('calculate-kpis/', views.CalculateKPIsView.as_view(), name='calculate-kpis'),
]
