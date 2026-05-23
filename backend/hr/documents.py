"""
Employee Document Management Models.
Manages employee documents and document templates.
"""

from django.db import models


# =============================================
# Employee Document (وثائق الموظف)
# =============================================

class EmployeeDocument(models.Model):
    """Documents uploaded for an employee with verification tracking."""

    DOCUMENT_TYPE_CHOICES = (
        ('national_id', 'بطاقة الهوية'),
        ('passport', 'جواز السفر'),
        ('contract', 'عقد العمل'),
        ('medical', 'تقرير طبي'),
        ('cv', 'السيرة الذاتية'),
        ('education_certificate', 'شهادة تعليمية'),
        ('other', 'أخرى'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='الموظف',
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='نوع المستند',
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المستند',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    file = models.FileField(
        upload_to='employee_documents/',
        verbose_name='الملف',
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name='حجم الملف (كيلوبايت)',
        help_text='يُحسب تلقائياً بالكيلوبايت',
    )
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_uploaded',
        verbose_name='رفع بواسطة',
    )
    expires_at = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
        help_text='للمستندات ذات تاريخ انتهاء كجواز السفر والعقد',
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تم التحقق',
        db_index=True,
    )
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_verified',
        verbose_name='تحقق بواسطة',
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التحقق',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'وثيقة موظف'
        verbose_name_plural = 'وثائق الموظفين'
        unique_together = ['employee', 'document_type', 'title']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.get_document_type_display()} - {self.title}'

    def save(self, *args, **kwargs):
        """Auto-compute file size in KB."""
        if self.file and hasattr(self.file, 'size'):
            self.file_size = max(self.file.size // 1024, 0)
        super().save(*args, **kwargs)


# =============================================
# Document Template (قوالب المستندات)
# =============================================

class DocumentTemplate(models.Model):
    """Reusable document templates for standardized document generation."""

    DOCUMENT_TYPE_CHOICES = (
        ('national_id', 'بطاقة الهوية'),
        ('passport', 'جواز السفر'),
        ('contract', 'عقد العمل'),
        ('medical', 'تقرير طبي'),
        ('cv', 'السيرة الذاتية'),
        ('education_certificate', 'شهادة تعليمية'),
        ('other', 'أخرى'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم القالب',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم القالب (إنجليزي)',
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='نوع المستند',
        db_index=True,
    )
    template_file = models.FileField(
        upload_to='document_templates/',
        verbose_name='ملف القالب',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'قالب مستند'
        verbose_name_plural = 'قوالب المستندات'
        ordering = ['document_type', 'name']

    def __str__(self):
        return f'{self.name} - {self.get_document_type_display()}'
