"""
Admin configuration for the Insurance & Pension module.
"""

from django.contrib import admin
from .models import (
    InsurancePolicy,
    InsuranceClaim,
    PensionRecord,
    PensionPayment,
)


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = (
        'policy_number', 'policy_name', 'insurance_provider',
        'insurance_type', 'status', 'coverage_amount', 'premium_amount',
        'start_date', 'end_date',
    )
    list_filter = ('status', 'insurance_type', 'premium_frequency', 'insured_entity')
    search_fields = ('policy_number', 'policy_name', 'insurance_provider')


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = (
        'claim_number', 'policy', 'claim_type', 'claimed_amount',
        'approved_amount', 'status', 'incident_date', 'submitted_by',
    )
    list_filter = ('status', 'claim_type', 'incident_date')
    search_fields = ('claim_number', 'policy__policy_number', 'description')


@admin.register(PensionRecord)
class PensionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'pension_scheme', 'contribution_type',
        'monthly_contribution', 'total_contributions', 'status', 'start_date',
    )
    list_filter = ('status', 'contribution_type')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'pension_scheme')


@admin.register(PensionPayment)
class PensionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'pension_record', 'amount', 'payment_date',
        'month', 'year', 'payment_method', 'status',
    )
    list_filter = ('status', 'payment_method', 'year', 'month')
    search_fields = ('pension_record__employee__first_name', 'pension_record__employee__last_name', 'reference_number')
