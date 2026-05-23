"""
Generic attachment model for the ERP system.
Supports linking files to any entity via Django's contenttypes framework.
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Attachment(models.Model):
    """Generic file attachment that can be linked to any model."""

    # File information
    file = models.FileField(
        upload_to='attachments/%Y/%m/',
        verbose_name='الملف',
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='اسم الملف',
    )
    file_type = models.CharField(
        max_length=50,
        verbose_name='نوع الملف',
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name='حجم الملف',
    )

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='نوع الكائن',
    )
    object_id = models.PositiveIntegerField(
        verbose_name='معرف الكائن',
        db_index=True,
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # Metadata
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='رفع بواسطة',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='الفئة',
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='عام',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'مرفق'
        verbose_name_plural = 'المرفقات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['file_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.file_name:
                self.file_name = self.file.name.split('/')[-1]
            if not self.file_type:
                self.file_type = self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''
        super().save(*args, **kwargs)
