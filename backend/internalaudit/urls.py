"""
URL patterns for the Internal Audit & Compliance module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Internal Audit statistics
    path('stats/', views.InternalAuditStatsView.as_view(), name='internal-audit-stats'),

    # Audit Plans
    path('plans/', views.AuditPlanListView.as_view(), name='audit-plans'),
    path('plans/<int:pk>/', views.AuditPlanDetailView.as_view(), name='audit-plan-detail'),
    path('plans/<int:pk>/complete/', views.AuditPlanCompleteView.as_view(), name='audit-plan-complete'),

    # Audit Findings
    path('findings/', views.AuditFindingListView.as_view(), name='audit-findings'),
    path('findings/<int:pk>/', views.AuditFindingDetailView.as_view(), name='audit-finding-detail'),
    path('findings/create/', views.AuditFindingCreateView.as_view(), name='audit-finding-create'),
    path('findings/<int:pk>/resolve/', views.AuditFindingResolveView.as_view(), name='audit-finding-resolve'),

    # Audit Evidence
    path('evidence/', views.AuditEvidenceListView.as_view(), name='audit-evidence'),
    path('evidence/create/', views.AuditEvidenceCreateView.as_view(), name='audit-evidence-create'),

    # Audit Actions
    path('actions/', views.AuditActionListView.as_view(), name='audit-actions'),
    path('actions/<int:pk>/', views.AuditActionDetailView.as_view(), name='audit-action-detail'),
    path('actions/create/', views.AuditActionCreateView.as_view(), name='audit-action-create'),
    path('actions/<int:pk>/complete/', views.AuditActionCompleteView.as_view(), name='audit-action-complete'),

    # Compliance Checks
    path('compliance/', views.ComplianceCheckListView.as_view(), name='compliance-checks'),
    path('compliance/<int:pk>/', views.ComplianceCheckDetailView.as_view(), name='compliance-check-detail'),
    path('compliance/<int:pk>/perform/', views.ComplianceCheckPerformView.as_view(), name='compliance-check-perform'),

    # Export
    path('export/', views.InternalAuditExportView.as_view(), name='internal-audit-export'),
]
