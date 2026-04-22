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
]
