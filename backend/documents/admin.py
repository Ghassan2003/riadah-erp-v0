"""
Admin configuration for DocumentCategory and Document models.
"""

from django.contrib import admin
from .models import DocumentCategory, Document


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Custom admin interface for DocumentCategory."""

    list_display = (
        'name', 'name_en', 'is_active', 'created_at',
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'name_en')
    ordering = ('name',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('معلومات التصنيف', {
            'fields': ('name', 'name_en', 'description')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Custom admin interface for Document."""

    list_display = (
        'title', 'module', 'category', 'file_type', 'file_size',
        'uploaded_by', 'is_active', 'created_at',
    )
    list_filter = ('module', 'category', 'file_type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'uploaded_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('file_size', 'file_type', 'created_at', 'updated_at')

    fieldsets = (
        ('معلومات المستند', {
            'fields': ('title', 'description', 'category', 'module')
        }),
        ('الربط بكائن', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',),
        }),
        ('الملف', {
            'fields': ('file', 'file_size', 'file_type')
        }),
        ('معلومات إضافية', {
            'fields': ('uploaded_by', 'is_active')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['restore_documents']

    @admin.action(description='استعادة المستندات المحددة')
    def restore_documents(self, request, queryset):
        """Restore soft-deleted documents."""
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f'تم استعادة {count} مستند(ات)')
