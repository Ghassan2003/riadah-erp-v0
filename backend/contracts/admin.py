"""
Admin configuration for the Contracts module.
"""

from django.contrib import admin
from .models import Contract, ContractMilestone, ContractPayment


class ContractMilestoneInline(admin.TabularInline):
    model = ContractMilestone
    extra = 0
    fields = ('title', 'due_date', 'amount', 'status', 'completed_date')
    readonly_fields = ('title', 'due_date', 'amount', 'status', 'completed_date')


class ContractPaymentInline(admin.TabularInline):
    model = ContractPayment
    extra = 0
    fields = ('amount', 'due_date', 'paid_date', 'payment_status', 'paid_amount')
    readonly_fields = ('amount', 'due_date', 'paid_date', 'payment_status', 'paid_amount')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'contract_type', 'customer', 'supplier', 'status', 'value', 'start_date', 'end_date')
    list_filter = ('status', 'contract_type', 'currency')
    search_fields = ('title', 'title_en', 'contract_number', 'customer__name', 'supplier__name')
    inlines = [ContractMilestoneInline, ContractPaymentInline]


@admin.register(ContractMilestone)
class ContractMilestoneAdmin(admin.ModelAdmin):
    list_display = ('contract', 'title', 'due_date', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('title', 'contract__title')


@admin.register(ContractPayment)
class ContractPaymentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'milestone', 'amount', 'due_date', 'payment_status', 'paid_amount', 'payment_method')
    list_filter = ('payment_status',)
    search_fields = ('contract__title', 'reference')
