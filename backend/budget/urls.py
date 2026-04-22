"""
URL patterns for the Budget Management module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Budget statistics
    path('stats/', views.BudgetStatsView.as_view(), name='budget-stats'),

    # Budgets
    path('budgets/', views.BudgetListView.as_view(), name='budget-list'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget-detail'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget-delete'),

    # Budget Categories
    path('categories/', views.BudgetCategoryListView.as_view(), name='budget-category-list'),
    path('categories/<int:pk>/', views.BudgetCategoryDetailView.as_view(), name='budget-category-detail'),

    # Budget Items
    path('items/', views.BudgetItemListView.as_view(), name='budget-item-list'),
    path('items/<int:pk>/', views.BudgetItemDetailView.as_view(), name='budget-item-detail'),

    # Budget Transfers
    path('transfers/', views.BudgetTransferListView.as_view(), name='budget-transfer-list'),
    path('transfers/<int:pk>/approve/', views.BudgetTransferApproveView.as_view(), name='budget-transfer-approve'),

    # Budget Expenses
    path('expenses/', views.BudgetExpenseListView.as_view(), name='budget-expense-list'),
    path('expenses/<int:pk>/approve/', views.BudgetExpenseApproveView.as_view(), name='budget-expense-approve'),

    # Export
    path('export/', views.BudgetExportView.as_view(), name='budget-export'),
]
