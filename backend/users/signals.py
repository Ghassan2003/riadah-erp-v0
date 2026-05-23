"""
إشارات Django لتخزين مؤقت للصلاحيات.
يتم استدعاؤها تلقائياً عند إنشاء أو تعديل أو حذف صلاحيات الأدوار.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='users.RolePermission')
@receiver(post_delete, sender='users.RolePermission')
def invalidate_role_permission_cache(sender, instance, **kwargs):
    """
    مسح التخزين المؤقت للصلاحيات عند تغيير صلاحيات أي دور.
    يشمل ذلك مسح كاش الدور وكاش جميع المستخدمين المنتمين لهذا الدور.
    """
    from django.core.cache import cache

    # مسح كاش صلاحيات الدور
    role_cache_key = f'role_perms_{instance.role}'
    cache.delete(role_cache_key)

    # مسح كاش جميع المستخدمين المنتمين لهذا الدور
    from users.models import User
    for user in User.objects.filter(role=instance.role, is_active=True).iterator():
        try:
            cache.delete_pattern(f'user_perms_{user.id}_*')
        except AttributeError:
            # في حال لم يدعم نوع الكاش delete_pattern
            # نسجل هذا ونكمل بدون خطأ
            pass
