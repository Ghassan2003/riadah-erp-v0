"""
Admin configuration for the Budget Management module.
"""

from django.contrib import admin
from .models import (
    Budget,
    BudgetCategory,
    BudgetItem,
    BudgetTransfer,
    BudgetExpense,
)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_year', 'department', 'total_budget', 'utilized_amount', 'remaining_amount', 'status')
    list_filter = ('status', 'fiscal_year', 'department')
    search_fields = ('name', 'description')


class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    extra = 0
    fields = ('name', 'allocated_amount', 'utilized_amount', 'remaining_amount')
    readonly_fields = ('name', 'allocated_amount', 'utilized_amount', 'remaining_amount')
    can_delete = False


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'allocated_amount', 'utilized_amount', 'remaining_amount', 'account')
    list_filter = ('budget',)
    search_fields = ('name', 'description')


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'planned_amount', 'actual_amount', 'status')
    list_filter = ('status', 'category')
    search_fields = ('description', 'notes')


@admin.register(BudgetTransfer)
class BudgetTransferAdmin(admin.ModelAdmin):
    list_display = ('from_budget', 'to_budget', 'amount', 'status', 'approved_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('reason',)


@admin.register(BudgetExpense)
class BudgetExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'budget', 'category', 'amount', 'expense_date', 'status', 'approved_by')
    list_filter = ('status', 'budget')
    search_fields = ('description', 'reference_number')
