from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """سجل تدقيق - تتبع جميع التغييرات في النظام"""

    ACTION_CHOICES = (
        ('create', 'إنشاء'),
        ('update', 'تعديل'),
        ('delete', 'حذف'),
        ('soft_delete', 'حذف ناعم'),
        ('restore', 'إعادة تفعيل'),
        ('status_change', 'تغيير حالة'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('export', 'تصدير'),
        ('import', 'استيراد'),
        ('backup', 'نسخ احتياطي'),
        ('other', 'أخرى'),
    )

    user = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='المستخدم', db_index=True,
        related_name='audit_logs',
    )
    action = models.CharField(
        max_length=20, choices=ACTION_CHOICES,
        verbose_name='الإجراء', db_index=True,
    )
    model_name = models.CharField(
        max_length=100, verbose_name='اسم النموذج', db_index=True,
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name='رقم الكائن',
    )
    object_repr = models.CharField(
        max_length=255, blank=True, verbose_name='تمثيل الكائن',
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
    )
    changes = models.JSONField(
        default=dict, blank=True, verbose_name='التغييرات',
    )
    old_values = models.JSONField(
        default=dict, blank=True, verbose_name='القيم القديمة',
    )
    new_values = models.JSONField(
        default=dict, blank=True, verbose_name='القيم الجديدة',
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='عنوان IP',
    )
    user_agent = models.TextField(
        blank=True, verbose_name='متصفح المستخدم',
    )
    url_path = models.CharField(
        max_length=500, blank=True, verbose_name='المسار',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='التاريخ', db_index=True,
    )

    class Meta:
        verbose_name = 'سجل تدقيق'
        verbose_name_plural = 'سجلات التدقيق'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.get_action_display()} - {self.model_name} - {self.object_repr}'

    @staticmethod
    def log(user, action, model_name, object_id=None, object_repr='',
            old_values=None, new_values=None, request=None, changes=None):
        """Helper to create an audit log entry."""
        ip_address = None
        user_agent = ''
        url_path = ''
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            url_path = request.path

        return AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            url_path=url_path,
            changes=changes or {},
        )
