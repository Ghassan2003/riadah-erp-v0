"""
API views for the Documents module.
Handles document upload, listing, detail, soft delete, and download URL retrieval.
"""

from rest_framework import generics, status, permissions, filters, views
from rest_framework.response import Response
from django.db.models import Count, Q
from django.conf import settings

from .models import DocumentCategory, Document
from .serializers import (
    DocumentCategoryListSerializer,
    DocumentCategoryCreateSerializer,
    DocumentCategoryDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    DocumentUpdateSerializer,
    DocumentDetailSerializer,
)
from users.permissions import IsAdmin


# =============================================
# DocumentCategory Views
# =============================================

class DocumentCategoryListView(generics.ListCreateAPIView):
    """GET: List document categories. POST: Create category (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentCategoryCreateSerializer
        return DocumentCategoryListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return DocumentCategory.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response({
            'message': 'تم إنشاء تصنيف المستندات بنجاح',
            'category': DocumentCategoryDetailSerializer(category).data,
        }, status=status.HTTP_201_CREATED)


class DocumentCategoryDetailView(generics.RetrieveUpdateAPIView):
    """GET: Category details. PATCH: Update category (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DocumentCategoryCreateSerializer
        return DocumentCategoryDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return DocumentCategory.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response({
            'message': 'تم تحديث تصنيف المستندات بنجاح',
            'category': DocumentCategoryDetailSerializer(category).data,
        })


# =============================================
# Document Views
# =============================================

class DocumentListView(generics.ListAPIView):
    """GET: List documents with filtering by module, category, date range, and search."""

    serializer_class = DocumentListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'module', 'file_size', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Document.objects.select_related('category', 'uploaded_by')
        # Filter by module
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        # Filter by uploaded_by (current user)
        my_only = self.request.query_params.get('my')
        if my_only and my_only.lower() == 'true':
            queryset = queryset.filter(uploaded_by=self.request.user)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset


class DocumentDetailView(generics.RetrieveAPIView):
    """GET: Retrieve detailed document information."""

    serializer_class = DocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.select_related('category', 'uploaded_by')


class DocumentUploadView(generics.CreateAPIView):
    """POST: Upload a new document (any authenticated user)."""

    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(uploaded_by=request.user)
        return Response({
            'message': 'تم رفع المستند بنجاح',
            'document': DocumentDetailSerializer(document, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class DocumentCategoryDeleteView(views.APIView):
    """DELETE: Soft-delete a document category (admin only)."""

    def delete(self, request, pk):
        try:
            category = DocumentCategory.objects.get(pk=pk)
        except DocumentCategory.DoesNotExist:
            return Response(
                {'error': 'تصنيف المستندات غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not category.is_active:
            return Response(
                {'error': 'تصنيف المستندات محذوف بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category.is_active = False
        category.save(update_fields=['is_active'])

        return Response({'message': 'تم حذف تصنيف المستندات بنجاح (حذف ناعم)'})


class DocumentUpdateView(generics.UpdateAPIView):
    """PATCH: Update document metadata (title, description, category, module)."""

    serializer_class = DocumentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.select_related('category', 'uploaded_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response({
            'message': 'تم تحديث المستند بنجاح',
            'document': DocumentDetailSerializer(document, context={'request': request}).data,
        })


class DocumentDeleteView(views.APIView):
    """DELETE: Soft-delete a document (admin or owner only)."""

    def delete(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {'error': 'المستند غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only admin or owner can delete
        if not (request.user.role == 'admin' or document.uploaded_by == request.user):
            return Response(
                {'error': 'غير مصرح بحذف هذا المستند'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not document.is_active:
            return Response(
                {'error': 'المستند محذوف بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.soft_delete()
        return Response({'message': 'تم حذف المستند بنجاح (حذف ناعم)'})


class DocumentDownloadView(views.APIView):
    """GET: Return the download URL for a document."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {'error': 'المستند غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not document.is_active:
            return Response(
                {'error': 'المستند محذوف'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not document.file:
            return Response(
                {'error': 'الملف غير موجود'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_url = request.build_absolute_uri(document.file.url)
        return Response({
            'id': document.id,
            'title': document.title,
            'file_url': file_url,
            'file_type': document.file_type,
            'file_size': document.file_size,
        })
