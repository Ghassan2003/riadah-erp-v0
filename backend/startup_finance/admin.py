"""Django admin configuration for Startup Finance models."""

from django.contrib import admin
from .models import (
    StartupProfile, FundingRound, BurnRateEntry,
    SubscriptionPlan, SubscriptionCycle, CustomerMetric,
    FinancialKPI, FinancialEntry,
)


@admin.register(StartupProfile)
class StartupProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'stage', 'industry', 'team_size', 'currency',
                    'monthly_recurring_revenue', 'monthly_operating_expenses', 'cash_balance')
    list_filter = ('stage', 'industry')
    search_fields = ('company_name', 'industry')
    ordering = ('-id',)


@admin.register(FundingRound)
class FundingRoundAdmin(admin.ModelAdmin):
    list_display = ('startup', 'round_type', 'round_name', 'amount_raised',
                    'valuation_post_money', 'equity_diluted', 'round_date')
    list_filter = ('round_type', 'round_date')
    search_fields = ('round_name', 'investor_names', 'startup__company_name')
    ordering = ('-round_date',)
    date_hierarchy = 'round_date'


@admin.register(BurnRateEntry)
class BurnRateEntryAdmin(admin.ModelAdmin):
    list_display = ('startup', 'month', 'category', 'entry_type', 'amount', 'is_recurring')
    list_filter = ('category', 'entry_type', 'is_recurring', 'month')
    search_fields = ('description',)
    ordering = ('-month', 'category')


class SubscriptionCycleInline(admin.TabularInline):
    model = SubscriptionCycle
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fk_name = 'plan'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly', 'price_yearly', 'trial_days', 'max_users', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('price_monthly',)
    inlines = [SubscriptionCycleInline]


@admin.register(SubscriptionCycle)
class SubscriptionCycleAdmin(admin.ModelAdmin):
    list_display = ('startup', 'customer_name', 'plan', 'status', 'billing_cycle',
                    'amount', 'start_date', 'end_date')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('customer_name',)
    ordering = ('-created_at',)
    date_hierarchy = 'start_date'


@admin.register(CustomerMetric)
class CustomerMetricAdmin(admin.ModelAdmin):
    list_display = ('startup', 'customer_name', 'acquisition_channel',
                    'acquisition_cost', 'monthly_revenue', 'total_revenue', 'projected_ltv')
    list_filter = ('acquisition_channel', 'cohort')
    search_fields = ('customer_name', 'acquisition_channel')
    ordering = ('-created_at',)


@admin.register(FinancialKPI)
class FinancialKPIAdmin(admin.ModelAdmin):
    list_display = ('startup', 'month', 'mrr', 'burn_rate', 'runway_months',
                    'total_subscribers', 'churn_rate_pct', 'calculated_at')
    list_filter = ('month',)
    ordering = ('-month',)
    date_hierarchy = 'month'


@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = ('startup', 'entry_type', 'category', 'amount',
                    'entry_date', 'external_source', 'idempotency_key')
    list_filter = ('entry_type', 'category', 'external_source', 'entry_date')
    search_fields = ('description', 'external_reference', 'idempotency_key')
    ordering = ('-entry_date',)
    date_hierarchy = 'entry_date'
