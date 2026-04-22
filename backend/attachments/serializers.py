"""
Serializers for the Attachments module.
Handles file upload validation and data transformation for generic attachments.
"""

import os
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Attachment


# Allowed file extensions and their corresponding MIME types
ALLOWED_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx',
    'png', 'jpg', 'jpeg', 'gif', 'zip', 'txt',
]

# MIME type whitelist for secure validation
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ],
    'xls': ['application/vnd.ms-excel'],
    'xlsx': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    'png': ['image/png'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'gif': ['image/gif'],
    'zip': [
        'application/zip',
        'application/x-zip-compressed',
        'application/x-zip',
    ],
    'txt': ['text/plain'],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class AttachmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing attachments."""

    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username', read_only=True, default=''
    )
    content_type_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            'id', 'file_name', 'file_type', 'file_size',
            'content_type', 'content_type_name', 'object_id',
            'description', 'category', 'is_public',
            'uploaded_by', 'uploaded_by_name',
            'file_url', 'created_at',
        )
        read_only_fields = (
            'id', 'file_type', 'file_size',
            'content_type', 'object_id',
            'uploaded_by', 'uploaded_by_name',
            'file_url', 'created_at',
        )

    def get_content_type_name(self, obj):
        return f'{obj.content_type.app_label}.{obj.content_type.model}'

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class AttachmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for viewing a single attachment."""

    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username', read_only=True, default=''
    )
    content_type_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            'id', 'file', 'file_name', 'file_type', 'file_size',
            'content_type', 'content_type_name', 'object_id',
            'description', 'category', 'is_public',
            'uploaded_by', 'uploaded_by_name',
            'file_url', 'created_at',
        )
        read_only_fields = (
            'id', 'file', 'file_name', 'file_type', 'file_size',
            'content_type', 'object_id',
            'uploaded_by', 'uploaded_by_name',
            'file_url', 'created_at',
        )

    def get_content_type_name(self, obj):
        return f'{obj.content_type.app_label}.{obj.content_type.model}'

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class AttachmentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading attachments with strict file validation."""

    content_type_str = serializers.CharField(
        write_only=True,
        help_text='Content type in format "app_label.model", e.g. "sales.order"',
    )
    object_id = serializers.PositiveIntegerField(write_only=True)

    class Meta:
        model = Attachment
        fields = (
            'file', 'content_type_str', 'object_id',
            'description', 'category', 'is_public',
        )

    def validate_file(self, value):
        """Validate file extension AND MIME type for security."""
        # Check file extension
        ext = value.name.split('.')[-1].lower() if '.' in value.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'نوع الملف غير مدعوم. الأنواع المسموحة: {", ".join(ALLOWED_EXTENSIONS)} / '
                f'Unsupported file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            )

        # Check MIME type
        if hasattr(value, 'content_type'):
            mime = value.content_type
            allowed_mimes = ALLOWED_MIME_TYPES.get(ext, [])
            if allowed_mimes and mime not in allowed_mimes:
                raise serializers.ValidationError(
                    f'نوع MIME غير مطابق للامتداد. الملف قد يكون تالفاً أو مزيفاً / '
                    f'MIME type does not match extension. File may be corrupted or spoofed.'
                )

        # Check file size
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'حجم الملف يتجاوز الحد المسموح (50 ميجابايت) / '
                f'File size exceeds the maximum limit (50MB).'
            )

        # Check for empty file
        if value.size == 0:
            raise serializers.ValidationError(
                'الملف فارغ / The file is empty.'
            )

        return value

    def validate_content_type_str(self, value):
        """Validate that the content type string resolves to a real model."""
        try:
            app_label, model = value.split('.', 1)
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ValueError:
            raise serializers.ValidationError(
                'صيغة content_type غير صحيحة. استخدم "app.model" / '
                'Invalid content_type format. Use "app.model".'
            )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f'نوع الكائن "{value}" غير موجود / '
                f'Content type "{value}" does not exist.'
            )
        return ct

    def validate(self, attrs):
        """Cross-field validation."""
        if not attrs.get('file'):
            raise serializers.ValidationError({
                'file': 'الملف مطلوب / File is required.'
            })
        return attrs

    def create(self, validated_data):
        """Create attachment with resolved content type."""
        ct = validated_data.pop('content_type_str')
        object_id = validated_data.pop('object_id')

        attachment = Attachment(
            content_type=ct,
            object_id=object_id,
            **validated_data,
        )
        if 'request' in self.context:
            attachment.uploaded_by = self.context['request'].user
        attachment.save()
        return attachment


class AttachmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating attachment metadata (description, category, is_public)."""

    class Meta:
        model = Attachment
        fields = ('description', 'category', 'is_public')
