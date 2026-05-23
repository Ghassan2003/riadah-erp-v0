"""
Admin configuration for the Accounting module.
"""

from django.contrib import admin
from .models import Account, JournalEntry, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'current_balance', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name', 'name_en')
    ordering = ('code',)
    list_editable = ('is_active',)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 2
    readonly_fields = ('journal_entry',)
    fields = ('account', 'transaction_type', 'amount', 'description')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'description', 'entry_type', 'entry_date', 'is_posted', 'created_by', 'created_at')
    list_filter = ('entry_type', 'is_posted', 'entry_date')
    search_fields = ('entry_number', 'description', 'reference')
    readonly_fields = ('entry_number', 'created_at', 'updated_at')
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('journal_entry', 'account', 'transaction_type', 'amount', 'description')
    list_filter = ('transaction_type',)
    search_fields = ('account__code', 'account__name', 'description')
