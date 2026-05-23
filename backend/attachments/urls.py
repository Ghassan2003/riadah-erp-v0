"""
URL patterns for the attachments app.
"""

from django.urls import path
from .views import (
    AttachmentListCreateView,
    AttachmentDetailView,
    AttachmentDownloadView,
    AttachmentBulkDeleteView,
)

urlpatterns = [
    # List and upload attachments
    path('', AttachmentListCreateView.as_view(), name='attachment-list-create'),
    # Single attachment: detail, update, delete
    path('<int:pk>/', AttachmentDetailView.as_view(), name='attachment-detail'),
    # Download attachment file
    path('<int:pk>/download/', AttachmentDownloadView.as_view(), name='attachment-download'),
    # Bulk delete attachments
    path('bulk-delete/', AttachmentBulkDeleteView.as_view(), name='attachment-bulk-delete'),
]
