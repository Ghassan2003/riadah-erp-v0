"""
Serializers for the Documents module.
Handles DocumentCategory and Document data transformation and file upload validation.
"""

from rest_framework import serializers
from django.db.models import Count
from .models import DocumentCategory, Document


# =============================================
# DocumentCategory Serializers
# =============================================

class DocumentCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing document categories."""

    class Meta:
        model = DocumentCategory
        fields = (
            'id', 'name', 'name_en', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class DocumentCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new document category."""

    class Meta:
        model = DocumentCategory
        fields = ('name', 'name_en', 'description')

    def validate_name(self, value):
        """Ensure category name is unique."""
        if DocumentCategory.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                'اسم التصنيف مستخدم بالفعل. يجب أن يكون فريداً.'
            )
        return value


class DocumentCategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with documents count."""

    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentCategory
        fields = (
            'id', 'name', 'name_en', 'description',
            'is_active', 'documents_count', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_documents_count(self, obj):
        return obj.document_set.filter(is_active=True).count()


# =============================================
# Document Serializers
# =============================================

class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing documents."""

    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username', read_only=True, default=''
    )
    module_display = serializers.CharField(
        source='get_module_display', read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'category', 'module', 'module_display',
            'file', 'file_url', 'file_size', 'file_type',
            'uploaded_by', 'uploaded_by_name',
            'is_active', 'created_at',
        )
        read_only_fields = (
            'id', 'file_url', 'file_size', 'file_type',
            'uploaded_by', 'uploaded_by_name', 'created_at',
        )

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading documents with file validation."""

    ALLOWED_EXTENSIONS = [
        'pdf', 'doc', 'docx', 'xls', 'xlsx',
        'jpg', 'jpeg', 'png', 'zip', 'txt',
    ]

    class Meta:
        model = Document
        fields = ('title', 'description', 'category', 'module', 'file')

    def validate_file(self, value):
        """Validate file extension."""
        ext = value.name.split('.')[-1].lower() if '.' in value.name else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'نوع الملف غير مدعوم. الأنواع المسموحة: {", ".join(self.ALLOWED_EXTENSIONS)}'
            )
        # Limit file size to 50MB
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                'حجم الملف يتجاوز الحد المسموح (50 ميجابايت)'
            )
        return value

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('عنوان المستند مطلوب')
        return value.strip()


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating document metadata after upload."""

    class Meta:
        model = Document
        fields = ('title', 'description', 'category', 'module')

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('عنوان المستند مطلوب')
        return value.strip()


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for viewing a single document."""

    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username', read_only=True, default=''
    )
    module_display = serializers.CharField(
        source='get_module_display', read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', read_only=True, default=None
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'description', 'category', 'category_name',
            'module', 'module_display', 'content_type', 'object_id',
            'file', 'file_url', 'file_size', 'file_type',
            'uploaded_by', 'uploaded_by_name',
            'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'file_url', 'file_size', 'file_type',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at',
        )

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None
