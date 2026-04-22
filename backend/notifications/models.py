"""
نماذج نظام الإشعارات - نظام ERP.
يوفر إدارة الإشعارات الداخلية للمستخدمين مع تصنيفات متعددة.
"""

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """
    نموذج الإشعار - يمثل إشعاراً داخلياً لمستخدم محدد.
    يدعم أنواعاً متعددة من الإشعارات مع إمكانية ربطه برابط خارجي.
    """

    TYPE_CHOICES = (
        ('info', 'معلومة'),
        ('success', 'نجاح'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
        ('order', 'أمر'),
        ('task', 'مهمة'),
        ('leave', 'إجازة'),
        ('system', 'نظام'),
        ('payment', 'دفعة'),
        ('invoice', 'فاتورة'),
        ('contract', 'عقد'),
        ('inventory', 'مخزون'),
        ('expense', 'مصروف'),
        ('payroll', 'راتب'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفضة'),
        ('normal', 'عادية'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    )

    recipient = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستلم',
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        verbose_name='العنوان',
    )
    message = models.TextField(
        verbose_name='الرسالة',
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        verbose_name='النوع',
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='الرابط',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='مقروء',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
        db_index=True,
    )

    # إشعارات المرسل
    sender = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name='المرسل',
    )

    # ربط بنموذج محدد (generic relation)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='نوع المحتوى',
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='معرّف الكائن',
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # أولوية الإشعار
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='الأولوية',
    )

    # تاريخ انتهاء الصلاحية
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
    )

    # إشعار مرتبط (للردود)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='إشعار أصلي',
    )

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['recipient', 'priority', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f'{self.title} -> {self.recipient.username}'

    def mark_as_read(self):
        """تحديد الإشعار كمقروء."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @staticmethod
    def notify(user, title, message, notification_type='info', link='', sender=None):
        """إنشاء إشعار لمستخدم محدد."""
        return Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            sender=sender,
        )

    @staticmethod
    def notify_all(title, message, notification_type='info', link='', sender=None):
        """إرسال إشعار لجميع المستخدمين النشطين."""
        from users.models import User
        users = User.objects.filter(is_active=True)
        notifications = []
        for user in users:
            notifications.append(Notification(
                recipient=user,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link,
                sender=sender,
            ))
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def notify_users(user_ids, title, message, notification_type='info', link='', sender=None):
        """إرسال إشعار لمجموعة مستخدمين محددة."""
        from users.models import User
        users = User.objects.filter(id__in=user_ids, is_active=True)
        notifications = []
        for user in users:
            notifications.append(Notification(
                recipient=user, title=title, message=message,
                notification_type=notification_type, link=link, sender=sender,
            ))
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def notify_by_role(role, title, message, notification_type='info', link='', sender=None):
        """إرسال إشعار لجميع المستخدمين بدور معين."""
        from users.models import User
        users = User.objects.filter(role=role, is_active=True)
        notifications = []
        for user in users:
            notifications.append(Notification(
                recipient=user, title=title, message=message,
                notification_type=notification_type, link=link, sender=sender,
            ))
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def notify_by_roles(roles, title, message, notification_type='info', link='', sender=None):
        """إرسال إشعار لمجموعة أدوار."""
        from users.models import User
        users = User.objects.filter(role__in=roles, is_active=True)
        notifications = []
        for user in users:
            notifications.append(Notification(
                recipient=user, title=title, message=message,
                notification_type=notification_type, link=link, sender=sender,
            ))
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def cleanup_expired():
        """حذف الإشعارات المنتهية الصلاحية."""
        from django.utils import timezone
        return Notification.objects.filter(expires_at__lte=timezone.now(), is_read=True).delete()

    @staticmethod
    def cleanup_old(days=90):
        """حذف الإشعارات المقروءة الأقدم من عدد أيام."""
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return Notification.objects.filter(is_read=True, created_at__lte=cutoff).delete()
