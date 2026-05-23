"""
URL patterns for Cost Allocation module.
مراكز التكلفة وقواعد التوزيع وسجلات التنفيذ.
"""

from django.urls import path

from .cost_allocation_views import (
    CostCenterListView,
    CostCenterCreateView,
    CostCenterDetailView,
    CostCenterUpdateView,
    AllocationRuleListView,
    AllocationRuleCreateView,
    AllocationRuleDetailView,
    AllocationRuleExecuteView,
    AllocationRuleBatchExecuteView,
    AllocationLogListView,
)

urlpatterns = [
    # Cost Centers - مراكز التكلفة
    path('cost-centers/', CostCenterListView.as_view(), name='cost-center-list'),
    path('cost-centers/create/', CostCenterCreateView.as_view(), name='cost-center-create'),
    path('cost-centers/<int:pk>/', CostCenterDetailView.as_view(), name='cost-center-detail'),
    path('cost-centers/<int:pk>/update/', CostCenterUpdateView.as_view(), name='cost-center-update'),

    # Allocation Rules - قواعد التوزيع
    path('allocation-rules/', AllocationRuleListView.as_view(), name='allocation-rule-list'),
    path('allocation-rules/create/', AllocationRuleCreateView.as_view(), name='allocation-rule-create'),
    path('allocation-rules/<int:pk>/', AllocationRuleDetailView.as_view(), name='allocation-rule-detail'),
    path('allocation-rules/<int:pk>/execute/', AllocationRuleExecuteView.as_view(), name='allocation-rule-execute'),
    path('allocation-rules/batch-execute/', AllocationRuleBatchExecuteView.as_view(), name='allocation-rule-batch-execute'),

    # Allocation Logs - سجلات التوزيعات
    path('allocation-logs/', AllocationLogListView.as_view(), name='allocation-log-list'),
]
