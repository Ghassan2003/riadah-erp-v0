from django.urls import path
from .enhanced_views import (
    JobRequisitionListView, JobRequisitionDetailView,
    JobPostingListView, JobPostingDetailView,
    JobApplicationListView, JobApplicationDetailView,
    InterviewListView, InterviewCreateView, InterviewDetailView,
    JobOfferListView, JobOfferDetailView,
    HireCandidateView,
)

urlpatterns = [
    path('requisitions/', JobRequisitionListView.as_view(), name='requisition-list'),
    path('requisitions/<int:pk>/', JobRequisitionDetailView.as_view(), name='requisition-detail'),
    path('postings/', JobPostingListView.as_view(), name='posting-list'),
    path('postings/<int:pk>/', JobPostingDetailView.as_view(), name='posting-detail'),
    path('applications/', JobApplicationListView.as_view(), name='application-list'),
    path('applications/<int:pk>/', JobApplicationDetailView.as_view(), name='application-detail'),
    path('interviews/', InterviewListView.as_view(), name='interview-list'),
    path('interviews/create/', InterviewCreateView.as_view(), name='interview-create'),
    path('interviews/<int:pk>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('offers/', JobOfferListView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', JobOfferDetailView.as_view(), name='offer-detail'),
    path('hire/', HireCandidateView.as_view(), name='hire-candidate'),
]
