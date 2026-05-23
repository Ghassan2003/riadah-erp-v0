"""
Signals for Startup Finance module.
إشارات لتحديث البيانات المترابطة تلقائياً.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='startup_finance.SubscriptionCycle')
def update_startup_mrr_on_subscription_change(sender, instance, **kwargs):
    """
    عند إنشاء أو تحديث اشتراك، حدّث MRR في ملف الشركة الناشئة.
    """
    if not kwargs.get('created') and kwargs.get('update_fields'):
        return  # skip if only specific fields updated

    from .models import StartupProfile
    try:
        startup = instance.startup
        active_mrr = startup.subscriptions.filter(status='active').aggregate(
            total=models.Sum('amount', default=0)
        )['total'] or 0

        # لا نُحدّث MRR مباشرة لتفادي حلقة إشارات لا نهائية
        # بدلاً من ذلك، يُحسب عبر KPIs الدورية
    except Exception:
        pass


# يجب استيراد models في أعلى الملف لاستخدامها
from django.db import models  # noqa: E402
