"""
URL patterns for the documents app.
"""

from django.urls import path
from .views import (
    DocumentCategoryListView,
    DocumentCategoryDetailView,
    DocumentCategoryDeleteView,
    DocumentListView,
    DocumentDetailView,
    DocumentUploadView,
    DocumentUpdateView,
    DocumentDeleteView,
    DocumentDownloadView,
)

urlpatterns = [
    # Document categories
    path('categories/', DocumentCategoryListView.as_view(), name='document-category-list'),
    path('categories/<int:pk>/', DocumentCategoryDetailView.as_view(), name='document-category-detail'),
    path('categories/<int:pk>/delete/', DocumentCategoryDeleteView.as_view(), name='document-category-delete'),

    # Document upload
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),

    # Document list and detail
    path('', DocumentListView.as_view(), name='document-list'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),

    # Document actions
    path('<int:pk>/update/', DocumentUpdateView.as_view(), name='document-update'),
    path('<int:pk>/delete/', DocumentDeleteView.as_view(), name='document-delete'),
    path('<int:pk>/download/', DocumentDownloadView.as_view(), name='document-download'),
]
