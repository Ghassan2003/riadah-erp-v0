"""
Admin configuration for the Tender Management module.
"""

from django.contrib import admin
from .models import (
    Tender,
    TenderDocument,
    TenderBid,
    TenderEvaluation,
    TenderAward,
)


class TenderDocumentInline(admin.TabularInline):
    model = TenderDocument
    extra = 0
    fields = ('title', 'file', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class TenderBidInline(admin.TabularInline):
    model = TenderBid
    extra = 0
    fields = ('bid_number', 'supplier', 'submission_date', 'status', 'total_amount', 'total_score')
    readonly_fields = ('submission_date',)


class TenderEvaluationInline(admin.TabularInline):
    model = TenderEvaluation
    extra = 0
    fields = ('criterion', 'weight', 'score', 'weighted_score', 'evaluator')
    readonly_fields = ('evaluator',)


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ('tender_number', 'title', 'tender_type', 'status', 'estimated_value', 'closing_date', 'created_at')
    list_filter = ('status', 'tender_type', 'department', 'project')
    search_fields = ('title', 'tender_number', 'description')
    inlines = [TenderDocumentInline, TenderBidInline]


@admin.register(TenderDocument)
class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'tender', 'file', 'uploaded_at')
    list_filter = ('tender',)
    search_fields = ('title', 'tender__tender_number', 'tender__title')


@admin.register(TenderBid)
class TenderBidAdmin(admin.ModelAdmin):
    list_display = ('bid_number', 'tender', 'supplier', 'status', 'total_amount', 'total_score', 'submission_date')
    list_filter = ('status', 'tender')
    search_fields = ('bid_number', 'supplier__name', 'tender__tender_number', 'tender__title')
    inlines = [TenderEvaluationInline]


@admin.register(TenderEvaluation)
class TenderEvaluationAdmin(admin.ModelAdmin):
    list_display = ('criterion', 'bid', 'weight', 'score', 'weighted_score', 'evaluator', 'created_at')
    list_filter = ('evaluator',)
    search_fields = ('criterion', 'bid__bid_number', 'bid__supplier__name')


@admin.register(TenderAward)
class TenderAwardAdmin(admin.ModelAdmin):
    list_display = ('tender', 'bid', 'award_date', 'contract_value', 'contract_duration_days', 'status', 'approved_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('tender__tender_number', 'tender__title', 'bid__bid_number', 'bid__supplier__name')
