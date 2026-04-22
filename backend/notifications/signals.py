"""
إشارات نظام الإشعارات - نظام ERP.
مراقبة الأحداث التجارية وإنشاء إشعارات تلقائية عند حدوثها.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


# =============================================
# معالجات إشعارات الإجازات
# =============================================

def _handle_leave_status_change(sender, instance, **kwargs):
    """
    إرسال إشعار عند تغيير حالة طلب إجازة.
    يُستدعى يدوياً من views أو عبر إشارة post_save.
    """
    from notifications.models import Notification

    if not hasattr(instance, 'employee') or not instance.employee:
        return

    employee = instance.employee
    if not employee.user:
        return

    status = instance.approval_status
    leave_type_display = instance.get_leave_type_display()

    if status == 'approved':
        Notification.notify(
            user=employee.user,
            title='تمت الموافقة على طلب الإجازة',
            message=f'تمت الموافقة على طلب إجازة {leave_type_display} من {instance.start_date} إلى {instance.end_date}',
            notification_type='success',
            link='/hr/leave-requests',
        )
        # إشعار للمديرين أيضاً
        Notification.notify_by_role(
            role='admin',
            title='موافقة على طلب إجازة',
            message=f'تمت الموافقة على إجازة {leave_type_display} للموظف {employee.full_name}',
            notification_type='info',
            link='/hr/leave-requests',
        )

    elif status == 'rejected':
        Notification.notify(
            user=employee.user,
            title='تم رفض طلب الإجازة',
            message=f'تم رفض طلب إجازة {leave_type_display} من {instance.start_date} إلى {instance.end_date}',
            notification_type='error',
            link='/hr/leave-requests',
        )


# =============================================
# معالجات إشعارات أوامر البيع
# =============================================

def _handle_order_status_change(sender, instance, **kwargs):
    """
    إرسال إشعار عند تغيير حالة أمر بيع أو شراء.
    """
    from notifications.models import Notification

    status = getattr(instance, 'status', None)
    if not status:
        return

    order_number = getattr(instance, 'order_number', '') or str(instance.id)

    if status == 'completed':
        Notification.notify_by_roles(
            roles=['admin', 'warehouse'],
            title='اكتمل تنفيذ أمر',
            message=f'تم اكتمال تنفيذ الأمر رقم {order_number}',
            notification_type='success',
            link='/sales/orders',
        )

    elif status == 'cancelled':
        Notification.notify_by_roles(
            roles=['admin', 'sales'],
            title='إلغاء أمر',
            message=f'تم إلغاء الأمر رقم {order_number}',
            notification_type='error',
            link='/sales/orders',
        )


# =============================================
# معالجات إشعارات الفواتير
# =============================================

def _handle_invoice_status_change(sender, instance, **kwargs):
    """
    إرسال إشعار عند تغيير حالة فاتورة.
    """
    from notifications.models import Notification

    status = getattr(instance, 'status', None)
    if not status:
        return

    invoice_number = getattr(instance, 'invoice_number', '') or str(instance.id)

    if status == 'paid':
        Notification.notify_by_role(
            role='accountant',
            title='تم سداد فاتورة',
            message=f'تم سداد الفاتورة رقم {invoice_number}',
            notification_type='success',
            notification_type='payment',
            link='/invoicing',
        )

    elif status == 'overdue':
        Notification.notify_by_roles(
            roles=['admin', 'accountant'],
            title='فاتورة متأخرة',
            message=f'الفاتورة رقم {invoice_number} تجاوزت تاريخ الاستحقاق',
            notification_type='warning',
            priority='high',
            link='/invoicing',
        )


# =============================================
# معالجات إشعارات العقود
# =============================================

def _handle_contract_status_change(sender, instance, **kwargs):
    """
    إرسال إشعار عند تغيير حالة عقد.
    """
    from notifications.models import Notification

    status = getattr(instance, 'status', None)
    if not status:
        return

    contract_title = getattr(instance, 'title', '') or str(instance.id)

    if status == 'active':
        Notification.notify_by_roles(
            roles=['admin'],
            title='تفعيل عقد جديد',
            message=f'تم تفعيل العقد: {contract_title}',
            notification_type='success',
            notification_type='contract',
            link='/contracts',
        )

    elif status == 'expired':
        Notification.notify_by_roles(
            roles=['admin'],
            title='انتهاء عقد',
            message=f'انتهت صلاحية العقد: {contract_title}',
            notification_type='warning',
            priority='high',
            link='/contracts',
        )


# =============================================
# معالجات إشعارات المخزون المنخفض (محسّنة)
# =============================================

def notify_low_stock(product, threshold=None):
    """
    إرسال إشعار عند انخفاض مخزون منتج.
    يُستدعى من مهام الصيانة المجدولة أو يدوياً.
    """
    from notifications.models import Notification

    if threshold is None:
        threshold = product.reorder_point or 10

    priority = 'urgent' if product.stock_quantity == 0 else 'high'
    notif_type = 'error' if product.stock_quantity == 0 else 'warning'

    Notification.notify_by_roles(
        roles=['admin', 'warehouse'],
        title='تنبيه مخزون منخفض' if product.stock_quantity > 0 else 'نفاد مخزون',
        message=f'المنتج "{product.name}" - المخزون الحالي: {product.stock_quantity} (الحد الأدنى: {threshold})',
        notification_type=notif_type,
        priority=priority,
        link='/inventory',
    )


# =============================================
# معالجات إشعارات الدفعات
# =============================================

def notify_payment_received(payment_info):
    """
    إرسال إشعار عند استلام دفعة.
    payment_info: قاموس يحتوي على amount, reference, account_name
    """
    from notifications.models import Notification

    amount = payment_info.get('amount', 0)
    reference = payment_info.get('reference', '')
    account = payment_info.get('account_name', '')

    Notification.notify_by_roles(
        roles=['admin', 'accountant'],
        title='دفعة مستلمة',
        message=f'تم استلام دفعة بمبلغ {amount:,.2f} ر.س - المرجع: {reference} - الحساب: {account}',
        notification_type='payment',
        link='/payments',
    )


def notify_payment_due(payment_info):
    """
    إرسال إشعار عند اقتراب موعد دفعة مستحقة.
    """
    from notifications.models import Notification

    amount = payment_info.get('amount', 0)
    due_date = payment_info.get('due_date', '')
    reference = payment_info.get('reference', '')

    Notification.notify_by_roles(
        roles=['admin', 'accountant'],
        title='دفعة مستحقة قريباً',
        message=f'دفعة بمبلغ {amount:,.2f} ر.س مستحقة بتاريخ {due_date} - المرجع: {reference}',
        notification_type='warning',
        priority='high',
        link='/payments',
    )


# =============================================
# دفع الإشعارات عبر WebSocket عند الإنشاء
# =============================================

@receiver(post_save, sender='notifications.Notification')
def push_notification_on_create(sender, instance, created, **kwargs):
    """
    When a new Notification is created, push it to the recipient's
    WebSocket group in real-time via Django Channels.

    This integrates seamlessly with the existing `Notification.notify()`,
    `notify_all()`, `notify_users()`, and `notify_by_role()` static methods —
    no changes needed to callers.
    """
    if not created:
        return  # Only push on creation, not on update

    try:
        from .services import push_notification, serialize_notification
        notification_data = serialize_notification(instance)
        push_notification(instance.recipient_id, notification_data)
    except Exception:
        # Channel layer may not be available (e.g. during management commands)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Could not push notification %d to WebSocket for user %s",
            instance.id, instance.recipient_id,
            exc_info=True,
        )


# =============================================
# تسجيل الإشارات (اختياري)
# =============================================

def register_business_signals():
    """
    تسجيل إشارات Django لمراقبة تغييرات النماذج تلقائياً.
    يمكن استدعاؤها من apps.py.ready() إذا أردت التفعيل التلقائي.
    ملاحظة: التفعيل التلقائي قد يسبب مشاكل في الدوران اللانهائي (recursive signals)
    لذلك يُفضل استدعاء الدوال يدوياً من views.
    """
    # يمكن إضافة تسجيل post_save هنا عند الحاجة
    # مثال:
    # post_save.connect(_handle_leave_status_change, sender='hr.LeaveRequest')
    pass
