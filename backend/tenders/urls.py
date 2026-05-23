"""
URL patterns for the Tender Management module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Tender statistics
    path('stats/', views.TenderStatsView.as_view(), name='tender-stats'),

    # Tenders
    path('', views.TenderListView.as_view(), name='tenders'),
    path('<int:pk>/', views.TenderDetailView.as_view(), name='tender-detail'),
    path('<int:pk>/delete/', views.TenderDeleteView.as_view(), name='tender-delete'),
    path('<int:pk>/publish/', views.TenderPublishView.as_view(), name='tender-publish'),

    # Tender Documents
    path('documents/', views.TenderDocumentListView.as_view(), name='tender-documents'),
    path('documents/<int:pk>/', views.TenderDocumentDetailView.as_view(), name='tender-document-detail'),

    # Tender Bids
    path('bids/', views.TenderBidListView.as_view(), name='tender-bids'),
    path('bids/<int:pk>/', views.TenderBidDetailView.as_view(), name='tender-bid-detail'),
    path('bids/<int:pk>/disqualify/', views.TenderBidDisqualifyView.as_view(), name='tender-bid-disqualify'),

    # Tender Evaluations
    path('evaluations/', views.TenderEvaluationListView.as_view(), name='tender-evaluations'),
    path('evaluations/<int:pk>/', views.TenderEvaluationDetailView.as_view(), name='tender-evaluation-detail'),

    # Tender Awards
    path('awards/', views.TenderAwardListView.as_view(), name='tender-awards'),
    path('awards/create/', views.TenderAwardCreateView.as_view(), name='tender-award-create'),
    path('awards/<int:pk>/', views.TenderAwardDetailView.as_view(), name='tender-award-detail'),
    path('awards/<int:pk>/approve/', views.TenderAwardApproveView.as_view(), name='tender-award-approve'),

    # Export
    path('export/', views.TenderExportView.as_view(), name='tender-export'),
]
