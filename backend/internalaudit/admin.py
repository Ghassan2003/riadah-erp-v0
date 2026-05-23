"""
Admin configuration for the Internal Audit & Compliance module.
"""

from django.contrib import admin
from .models import (
    AuditPlan,
    AuditFinding,
    AuditEvidence,
    AuditAction,
    ComplianceCheck,
)


@admin.register(AuditPlan)
class AuditPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_year', 'audit_type', 'status', 'risk_level', 'start_date', 'end_date')
    list_filter = ('status', 'audit_type', 'risk_level', 'fiscal_year')
    search_fields = ('name', 'description')


class AuditFindingInline(admin.TabularInline):
    model = AuditFinding
    extra = 0
    fields = ('finding_number', 'title', 'severity', 'category', 'status', 'responsible_person')
    readonly_fields = ('finding_number', 'title', 'severity', 'category', 'status', 'responsible_person')
    can_delete = False


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ('finding_number', 'title', 'audit_plan', 'severity', 'category', 'status', 'due_date')
    list_filter = ('severity', 'category', 'status')
    search_fields = ('finding_number', 'title', 'description')


class AuditEvidenceInline(admin.TabularInline):
    model = AuditEvidence
    extra = 0
    fields = ('evidence_type', 'description', 'file', 'collected_by', 'collected_at')
    readonly_fields = ('collected_at',)
    can_delete = False


@admin.register(AuditEvidence)
class AuditEvidenceAdmin(admin.ModelAdmin):
    list_display = ('finding', 'evidence_type', 'description', 'collected_by', 'collected_at')
    list_filter = ('evidence_type',)
    search_fields = ('description', 'finding__finding_number', 'finding__title')


@admin.register(AuditAction)
class AuditActionAdmin(admin.ModelAdmin):
    list_display = ('action_number', 'finding', 'assigned_to', 'priority', 'status', 'due_date', 'completion_date')
    list_filter = ('priority', 'status')
    search_fields = ('action_number', 'description', 'finding__finding_number', 'finding__title')


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'regulation', 'department', 'frequency', 'status', 'next_check')
    list_filter = ('status', 'frequency')
    search_fields = ('name', 'regulation', 'description')
