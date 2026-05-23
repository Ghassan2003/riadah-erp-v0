from django.urls import path
from .enhanced_views import (
    EmployeeDocumentListView, EmployeeDocumentCreateView,
    DocumentTemplateListView, DocumentTemplateDetailView,
)

urlpatterns = [
    path('documents/', EmployeeDocumentListView.as_view(), name='document-list'),
    path('documents/create/', EmployeeDocumentCreateView.as_view(), name='document-create'),
    path('templates/', DocumentTemplateListView.as_view(), name='template-list'),
    path('templates/<int:pk>/', DocumentTemplateDetailView.as_view(), name='template-detail'),
]
