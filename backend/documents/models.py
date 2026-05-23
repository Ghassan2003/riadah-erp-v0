"""
Document management models for the ERP system.
Supports file uploads, categorization, and module linking via generic foreign keys.
"""

from django.db import models
from django.utils import timezone


class DocumentCategory(models.Model):
    """Category for organizing documents across modules."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='اسم التصنيف',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='التصنيف (إنجليزي)',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تصنيف مستندات'
        verbose_name_plural = 'تصنيفات المستندات'
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """Document model with file storage, categorization, and module linking."""

    MODULE_CHOICES = (
        ('general', 'عام'),
        ('inventory', 'المخازن'),
        ('sales', 'المبيعات'),
        ('accounting', 'المحاسبة'),
        ('hr', 'الموارد البشرية'),
        ('purchases', 'المشتريات'),
        ('projects', 'المشاريع'),
    )

    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المستند',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='التصنيف',
    )
    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        default='general',
        verbose_name='الوحدة',
        db_index=True,
    )
    # Generic foreign key - link to any model
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name='الملف',
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name='حجم الملف',
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نوع الملف',
    )
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='رفع بواسطة',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'مستند'
        verbose_name_plural = 'المستندات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Mark document as inactive instead of deleting."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restore a soft-deleted document."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
