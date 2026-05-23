"""
تكوين لوحة الإدارة لوحدة إدارة علاقات العملاء (CRM).
"""

from django.contrib import admin
from .models import (
    Company,
    Contact,
    Lead,
    LeadActivity,
    CustomerSegment,
    Campaign,
    CampaignActivity,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'name_en', 'industry', 'city', 'country',
        'company_type', 'annual_revenue', 'employee_count',
        'is_active', 'assigned_to',
    )
    list_filter = ('company_type', 'is_active', 'country', 'city')
    search_fields = ('name', 'name_en', 'industry', 'city', 'country', 'email', 'phone', 'website')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'name_en', 'industry', 'company_type', 'is_active'),
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'email', 'website'),
        }),
        ('العنوان', {
            'fields': ('address', 'city', 'country'),
            'classes': ('collapse',),
        }),
        ('معلومات مالية', {
            'fields': ('annual_revenue', 'employee_count'),
            'classes': ('collapse',),
        }),
        ('إدارة', {
            'fields': ('assigned_to', 'notes'),
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email', 'company', 'company_account',
        'source', 'status', 'assigned_to',
    )
    list_filter = ('status', 'source', 'company_account')
    search_fields = (
        'first_name', 'last_name', 'email', 'company',
        'company_account__name', 'phone', 'mobile',
    )
    list_select_related = ('company_account', 'assigned_to')
    autocomplete_fields = ('company_account',)
    readonly_fields = ('created_at', 'updated_at')


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 0
    fields = ('activity_type', 'subject', 'scheduled_at', 'completed', 'completed_by')
    readonly_fields = ('activity_type', 'subject', 'scheduled_at', 'completed', 'completed_by')
    can_delete = False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact', 'value', 'probability', 'status', 'pipeline_stage', 'assigned_to', 'expected_close_date')
    list_filter = ('status', 'pipeline_stage', 'source')
    search_fields = ('title', 'contact__first_name', 'contact__last_name', 'contact__company', 'contact__company_account__name')
    inlines = [LeadActivityInline]


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'activity_type', 'subject', 'scheduled_at', 'completed', 'completed_by', 'created_at')
    list_filter = ('activity_type', 'completed')
    search_fields = ('subject', 'description', 'lead__title')


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_count', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


class CampaignActivityInline(admin.TabularInline):
    model = CampaignActivity
    extra = 0
    fields = ('activity_type', 'contact', 'activity_date', 'description')
    readonly_fields = ('activity_type', 'contact', 'activity_date', 'description')
    can_delete = False


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'status', 'start_date', 'end_date', 'budget', 'actual_cost', 'assigned_to')
    list_filter = ('status', 'campaign_type')
    search_fields = ('name', 'description', 'target_audience')
    inlines = [CampaignActivityInline]


@admin.register(CampaignActivity)
class CampaignActivityAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'activity_type', 'contact', 'activity_date', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('description', 'campaign__name', 'contact__first_name', 'contact__last_name')
