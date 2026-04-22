"""
API views for the Attachments module.
Handles listing, uploading, retrieving, updating, downloading, and bulk deleting attachments.
"""

import os
import mimetypes
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, status, permissions, views
from rest_framework.response import Response

from .models import Attachment
from .serializers import (
    AttachmentListSerializer,
    AttachmentDetailSerializer,
    AttachmentUploadSerializer,
    AttachmentUpdateSerializer,
)


class AttachmentListCreateView(generics.ListCreateAPIView):
    """
    GET: List attachments for a specific entity.
         Query params: content_type (app.model), object_id, category
    POST: Upload a new attachment.
    """

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AttachmentUploadSerializer
        return AttachmentListSerializer

    def get_queryset(self):
        queryset = Attachment.objects.select_related(
            'content_type', 'uploaded_by',
        )

        # Filter by content_type and object_id
        content_type_str = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')

        if content_type_str and object_id:
            try:
                app_label, model = content_type_str.split('.', 1)
                ct = ContentType.objects.get(app_label=app_label, model=model)
                queryset = queryset.filter(content_type=ct, object_id=object_id)
            except (ValueError, ContentType.DoesNotExist):
                queryset = queryset.none()
        elif content_type_str or object_id:
            # Both are required together
            queryset = queryset.none()

        # Optional: filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()
        return Response({
            'message': 'تم رفع المرفق بنجاح / Attachment uploaded successfully',
            'attachment': AttachmentDetailSerializer(
                attachment, context={'request': request}
            ).data,
        }, status=status.HTTP_201_CREATED)


class AttachmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve attachment details.
    PATCH: Update attachment metadata (description, category, is_public).
    DELETE: Delete an attachment.
    """

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AttachmentUpdateSerializer
        return AttachmentDetailSerializer

    def get_queryset(self):
        return Attachment.objects.select_related(
            'content_type', 'uploaded_by',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()
        return Response({
            'message': 'تم تحديث المرفق بنجاح / Attachment updated successfully',
            'attachment': AttachmentDetailSerializer(
                attachment, context={'request': request}
            ).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Delete the physical file
        if instance.file:
            try:
                if os.path.isfile(instance.file.path):
                    os.remove(instance.file.path)
            except (OSError, ValueError):
                pass
        instance.delete()
        return Response({
            'message': 'تم حذف المرفق بنجاح / Attachment deleted successfully',
        })


class AttachmentDownloadView(views.APIView):
    """GET: Download an attachment file with proper Content-Disposition header."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            attachment = Attachment.objects.select_related(
                'content_type', 'uploaded_by'
            ).get(pk=pk)
        except Attachment.DoesNotExist:
            return Response(
                {'error': 'المرفق غير موجود / Attachment not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not attachment.file:
            return Response(
                {'error': 'الملف غير موجود / File not found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = attachment.file.path
        if not os.path.exists(file_path):
            return Response(
                {'error': 'الملف غير موجود على الخادم / File not found on server'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Determine content type
        content_type, _ = mimetypes.guess_type(attachment.file_name)
        if not content_type:
            content_type = 'application/octet-stream'

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
        )
        # Force download with original filename
        response['Content-Disposition'] = (
            f'attachment; filename="{attachment.file_name}"'
        )
        response['Content-Length'] = attachment.file_size or os.path.getsize(file_path)
        return response


class AttachmentBulkDeleteView(views.APIView):
    """POST: Delete multiple attachments at once. Body: { ids: [1, 2, 3] }"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response(
                {'error': 'يجب توفير قائمة معرفات المرفقات / A list of attachment IDs is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attachments = Attachment.objects.filter(id__in=ids)
        deleted_count = 0

        for attachment in attachments:
            # Delete the physical file
            if attachment.file:
                try:
                    if os.path.isfile(attachment.file.path):
                        os.remove(attachment.file.path)
                except (OSError, ValueError):
                    pass
            attachment.delete()
            deleted_count += 1

        return Response({
            'message': f'تم حذف {deleted_count} مرفق(ات) بنجاح / '
                       f'{deleted_count} attachment(s) deleted successfully',
            'deleted_count': deleted_count,
        })
