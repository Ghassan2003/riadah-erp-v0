"""
URL patterns for the Projects module.
"""

from django.urls import path
from .views import (
    ProjectStatsView,
    ProjectListView,
    ProjectDetailView,
    ProjectDeleteView,
    ProjectTaskListView,
    ProjectTaskDetailView,
    ProjectTaskDeleteView,
    TaskCommentListView,
    TaskCommentDetailView,
    TaskCommentUpdateView,
    TaskCommentDeleteView,
    ProjectExpenseListView,
    ProjectExpenseDetailView,
    ProjectExpenseUpdateView,
    ProjectExpenseDeleteView,
    ProjectExportView,
    GanttDataView,
    # New views
    ProjectPhaseListView,
    ProjectPhaseDetailView,
    ProjectPhaseDeleteView,
    ProjectMilestoneListView,
    ProjectMilestoneDetailView,
    ProjectMilestoneDeleteView,
    BudgetItemListView,
    BudgetItemDetailView,
    BudgetItemDeleteView,
    ProjectBudgetStatsView,
    ProjectRiskListView,
    ProjectRiskDetailView,
    ProjectRiskDeleteView,
    RiskMatrixView,
    TimeEntryListView,
    TimeEntryDetailView,
    TimeEntryDeleteView,
    TimeEntryReportView,
    ProjectContractListView,
    ProjectContractDetailView,
    ProjectContractDeleteView,
    ProjectDocumentListView,
    ProjectDocumentDetailView,
    ProjectDocumentDeleteView,
)

urlpatterns = [
    # Project statistics
    path('stats/', ProjectStatsView.as_view(), name='project-stats'),

    # Project CRUD
    path('', ProjectListView.as_view(), name='project-list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),

    # ProjectTask operations
    path('tasks/', ProjectTaskListView.as_view(), name='project-task-list'),
    path('tasks/<int:pk>/', ProjectTaskDetailView.as_view(), name='project-task-detail'),
    path('tasks/<int:pk>/delete/', ProjectTaskDeleteView.as_view(), name='project-task-delete'),

    # TaskComment operations
    path('tasks/<int:task_id>/comments/', TaskCommentListView.as_view(), name='task-comment-list'),
    path('comments/<int:pk>/', TaskCommentDetailView.as_view(), name='task-comment-detail'),
    path('comments/<int:pk>/update/', TaskCommentUpdateView.as_view(), name='task-comment-update'),
    path('comments/<int:pk>/delete/', TaskCommentDeleteView.as_view(), name='task-comment-delete'),

    # ProjectExpense operations
    path('expenses/', ProjectExpenseListView.as_view(), name='project-expense-list'),
    path('expenses/<int:pk>/', ProjectExpenseDetailView.as_view(), name='project-expense-detail'),
    path('expenses/<int:pk>/update/', ProjectExpenseUpdateView.as_view(), name='project-expense-update'),
    path('expenses/<int:pk>/delete/', ProjectExpenseDeleteView.as_view(), name='project-expense-delete'),

    # Excel Export
    path('export/', ProjectExportView.as_view(), name='project-export'),

    # Gantt Data
    path('gantt-data/', GanttDataView.as_view(), name='gantt-data'),

    # ProjectPhase operations
    path('phases/', ProjectPhaseListView.as_view(), name='project-phase-list'),
    path('phases/<int:pk>/', ProjectPhaseDetailView.as_view(), name='project-phase-detail'),
    path('phases/<int:pk>/delete/', ProjectPhaseDeleteView.as_view(), name='project-phase-delete'),

    # ProjectMilestone operations
    path('milestones/', ProjectMilestoneListView.as_view(), name='project-milestone-list'),
    path('milestones/<int:pk>/', ProjectMilestoneDetailView.as_view(), name='project-milestone-detail'),
    path('milestones/<int:pk>/delete/', ProjectMilestoneDeleteView.as_view(), name='project-milestone-delete'),

    # BudgetItem operations
    path('budget-items/', BudgetItemListView.as_view(), name='budget-item-list'),
    path('budget-items/<int:pk>/', BudgetItemDetailView.as_view(), name='budget-item-detail'),
    path('budget-items/<int:pk>/delete/', BudgetItemDeleteView.as_view(), name='budget-item-delete'),
    path('budget-stats/', ProjectBudgetStatsView.as_view(), name='project-budget-stats'),

    # ProjectRisk operations
    path('risks/', ProjectRiskListView.as_view(), name='project-risk-list'),
    path('risks/<int:pk>/', ProjectRiskDetailView.as_view(), name='project-risk-detail'),
    path('risks/<int:pk>/delete/', ProjectRiskDeleteView.as_view(), name='project-risk-delete'),
    path('risk-matrix/', RiskMatrixView.as_view(), name='risk-matrix'),

    # TimeEntry operations
    path('time-entries/', TimeEntryListView.as_view(), name='time-entry-list'),
    path('time-entries/<int:pk>/', TimeEntryDetailView.as_view(), name='time-entry-detail'),
    path('time-entries/<int:pk>/delete/', TimeEntryDeleteView.as_view(), name='time-entry-delete'),
    path('time-report/', TimeEntryReportView.as_view(), name='time-entry-report'),

    # ProjectContract operations
    path('contracts/', ProjectContractListView.as_view(), name='project-contract-list'),
    path('contracts/<int:pk>/', ProjectContractDetailView.as_view(), name='project-contract-detail'),
    path('contracts/<int:pk>/delete/', ProjectContractDeleteView.as_view(), name='project-contract-delete'),

    # ProjectDocument operations
    path('documents/', ProjectDocumentListView.as_view(), name='project-document-list'),
    path('documents/<int:pk>/', ProjectDocumentDetailView.as_view(), name='project-document-detail'),
    path('documents/<int:pk>/delete/', ProjectDocumentDeleteView.as_view(), name='project-document-delete'),
]
