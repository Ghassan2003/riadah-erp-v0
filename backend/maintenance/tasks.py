"""
مهام التنفيذ - نظام ERP.
وظائف التنفيذ الفعلي للمهام المجدولة.
"""

import os
import time
import traceback
import zipfile
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.core.management import call_command
from django.apps import apps as django_apps
from django.db.models import Sum, Count, Q, DecimalField, Value
from django.db.models.functions import Coalesce

from .models import ErrorLog, CronJob, BackupRecord, SystemBackup


def run_cron_task(cron_job, force=False):
    """تنفيذ مهمة مجدولة مع تسجيل النتائج."""
    start_time = time.time()

    # Check if job should run (unless forced)
    if not force:
        if cron_job.status != 'active':
            return {'message': 'المهمة غير نشطة', 'status': 'skipped'}
        if cron_job.next_run and timezone.now() < cron_job.next_run:
            return {'message': 'لم يحين وقت التنفيذ بعد', 'status': 'skipped'}

    cron_job.mark_running()

    try:
        task_func = TASK_REGISTRY.get(cron_job.task)
        if not task_func:
            raise Exception(f'المهمة غير معرفة: {cron_job.task}')

        result = task_func(cron_job.config)
        duration = time.time() - start_time
        cron_job.mark_success(duration)

        return {
            'message': f'تم تنفيذ المهمة بنجاح: {cron_job.name}',
            'status': 'success',
            'duration': round(duration, 2),
            'result': result,
        }

    except Exception as e:
        duration = time.time() - start_time
        error_msg = f'{str(e)}\n{traceback.format_exc()}'
        cron_job.mark_failed(str(e), duration)

        ErrorLog.log_error(
            level='error',
            message=f'فشل تنفيذ المهمة المجدولة "{cron_job.name}": {str(e)}',
            source='cron',
            code='CRON_JOB_FAILED',
            stack_trace=traceback.format_exc(),
        )

        return {
            'message': f'فشل تنفيذ المهمة: {str(e)}',
            'status': 'failed',
            'duration': round(duration, 2),
        }


def run_all_due_tasks():
    """تنفيذ جميع المهام المستحقة."""
    now = timezone.now()
    due_jobs = CronJob.objects.filter(
        status='active',
        next_run__lte=now,
    )

    results = []
    for job in due_jobs:
        result = run_cron_task(job)
        results.append({
            'job_id': job.id,
            'job_name': job.name,
            **result,
        })

    return results


# ==========================================
# وظائف المهام المسجلة
# ==========================================

TASK_REGISTRY = {}


def register_task(task_name):
    """ديكوراتور لتسجيل مهمة."""
    def decorator(func):
        TASK_REGISTRY[task_name] = func
        return func
    return decorator


@register_task('auto_backup_daily')
@register_task('auto_backup_weekly')
@register_task('auto_backup_monthly')
def task_auto_backup(config):
    """النسخ الاحتياطي التلقائي."""
    backup_config = SystemBackup.objects.first()
    backup_dir = backup_config.backup_directory if backup_config else 'backups'
    full_dir = os.path.join(settings.BASE_DIR, backup_dir)
    os.makedirs(full_dir, exist_ok=True)

    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f'erp_auto_backup_{timestamp}.zip'
    file_path = os.path.join(full_dir, filename)

    local_apps = [
        'users', 'inventory', 'sales', 'accounting',
        'hr', 'purchases', 'documents', 'projects',
        'notifications', 'auditlog', 'maintenance',
    ]
    models_to_dump = []
    for app_label in local_apps:
        try:
            app_config = django_apps.get_app_config(app_label)
            for model in app_config.get_models():
                models_to_dump.append(f'{app_label}.{model.__name__}')
        except LookupError:
            pass

    import json
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        out = BytesIO()
        call_command('dumpdata', *models_to_dump, '--indent=2', stdout=out)
        out.seek(0)
        json_content = out.read().decode('utf-8')
        data = json.loads(json_content)
        zf.writestr(f'erp_backup_{timestamp}.json', json_content)

    buffer.seek(0)
    with open(file_path, 'wb') as f:
        f.write(buffer.read())

    file_size = os.path.getsize(file_path)

    record = BackupRecord.objects.create(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        backup_type='auto_daily',
        status='completed',
        tables_count=len(models_to_dump),
        records_count=len(data),
        notes='نسخة احتياطية تلقائية',
    )

    # Clean old backups
    keep_count = 30
    if backup_config:
        keep_count = backup_config.keep_backups_count
    old_backups = BackupRecord.objects.filter(
        backup_type__startswith='auto_'
    ).order_by('-created_at')[keep_count:]
    for old in old_backups:
        if old.file_exists:
            try:
                os.remove(old.file_path)
            except Exception:
                pass
        old.delete()

    return {
        'filename': filename,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'records': len(data),
    }


@register_task('inventory_alerts')
def task_inventory_alerts(config):
    """تنبيهات المخزون المنخفض."""
    from inventory.models import Product
    from notifications.models import Notification
    from users.models import User

    threshold = config.get('low_stock_threshold', 10)
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=threshold,
        stock_quantity__gt=0,
    )
    out_of_stock = Product.objects.filter(stock_quantity=0)

    alert_users = User.objects.filter(
        is_active=True,
        role__in=['admin', 'warehouse'],
    )

    alerts_created = 0
    for user in alert_users:
        if low_stock_products.exists():
            product_names = ', '.join([p.name for p in low_stock_products[:10]])
            Notification.notify(
                user=user,
                title='تنبيه مخزون منخفض',
                message=f'يوجد {low_stock_products.count()} منتج بمخزون منخفض: {product_names}',
                notification_type='warning',
                link='/products',
            )
            alerts_created += 1

        if out_of_stock.exists():
            product_names = ', '.join([p.name for p in out_of_stock[:10]])
            Notification.notify(
                user=user,
                title='تنبيه مخزون نفد',
                message=f'يوجد {out_of_stock.count()} منتج نفد مخزونه: {product_names}',
                notification_type='error',
                link='/products',
            )
            alerts_created += 1

    return {
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock.count(),
        'alerts_sent': alerts_created,
    }


@register_task('recurring_invoices')
def task_recurring_invoices(config):
    """فواتير متكررة - إنشاء فواتير دورية."""
    # This is a placeholder for the recurring invoice functionality
    # In a real implementation, this would check for recurring invoice schedules
    # and create new invoices automatically

    from notifications.models import Notification
    from users.models import User

    # Check if there are any recurring invoice configurations
    # For now, just log that the task ran
    return {
        'message': 'تم فحص الفواتير المتكررة',
        'invoices_created': 0,
    }


@register_task('clean_old_logs')
def task_clean_old_logs(config):
    """تنظيف السجلات القديمة."""
    days = config.get('keep_days', 90)

    cutoff = timezone.now() - timedelta(days=days)

    # Clean resolved error logs
    error_deleted, _ = ErrorLog.objects.filter(
        is_resolved=True,
        created_at__lte=cutoff,
    ).delete()

    # Clean old audit logs (keep last N days)
    from auditlog.models import AuditLog
    audit_cutoff = timezone.now() - timedelta(days=config.get('audit_keep_days', 180))
    audit_deleted, _ = AuditLog.objects.filter(
        created_at__lte=audit_cutoff,
    ).delete()

    return {
        'errors_deleted': error_deleted,
        'audit_logs_deleted': audit_deleted,
        'older_than_days': days,
    }


@register_task('clean_old_backups')
def task_clean_old_backups(config):
    """تنظيف النسخ الاحتياطية القديمة."""
    keep_count = config.get('keep_count', 30)

    old_backups = BackupRecord.objects.filter(
        status='completed'
    ).order_by('-created_at')[keep_count:]

    deleted = 0
    for backup in old_backups:
        if backup.file_exists:
            try:
                os.remove(backup.file_path)
            except Exception:
                pass
        backup.delete()
        deleted += 1

    return {'backups_deleted': deleted}


@register_task('employee_attendance_reminder')
def task_employee_attendance_reminder(config):
    """تذكير الموظفين بتسجيل الحضور."""
    from notifications.models import Notification
    from users.models import User
    from hr.models import Employee

    today = timezone.now().date()
    active_employees = Employee.objects.filter(is_active=True)

    # Find users associated with active employees who haven't checked in
    from hr.models import AttendanceRecord
    checked_in = AttendanceRecord.objects.filter(
        date=today,
    ).values_list('employee_id', flat=True)

    missing_attendance = active_employees.exclude(id__in=checked_in)
    reminders_sent = 0

    for emp in missing_attendance:
        if emp.user_id:
            Notification.notify(
                user=emp.user,
                title='تذكير تسجيل الحضور',
                message='لم يتم تسجيل حضورك اليوم، يرجى تسجيل الحضور في أقرب وقت.',
                notification_type='warning',
                link='/attendance',
            )
            reminders_sent += 1

    return {
        'missing_attendance': missing_attendance.count(),
        'reminders_sent': reminders_sent,
    }


@register_task('expense_alerts')
def task_expense_alerts(config):
    """تنبيهات المصروفات."""
    from accounting.models import Account, AccountType
    from notifications.models import Notification
    from users.models import User

    threshold = float(config.get('expense_threshold', 50000))

    # Get expense accounts that exceeded threshold
    expense_accounts = Account.objects.filter(
        account_type=AccountType.EXPENSE,
        is_active=True,
    )

    high_expenses = []
    for acc in expense_accounts:
        if acc.current_balance > threshold:
            high_expenses.append({
                'name': acc.name,
                'balance': float(acc.current_balance),
            })

    alerts_sent = 0
    if high_expenses:
        admin_users = User.objects.filter(
            is_active=True,
            role__in=['admin', 'accountant'],
        )
        for user in admin_users:
            accounts_str = ', '.join([f'{e["name"]}: {e["balance"]:,.0f}' for e in high_expenses[:5]])
            Notification.notify(
                user=user,
                title='تنبيه مصروفات مرتفعة',
                message=f'حسابات مصروفات تجاوزت الحد ({threshold:,.0f}): {accounts_str}',
                notification_type='warning',
                link='/reports',
            )
            alerts_sent += 1

    return {
        'high_expense_accounts': len(high_expenses),
        'alerts_sent': alerts_sent,
    }


@register_task('project_deadline_alerts')
def task_project_deadline_alerts(config):
    """تنبيهات مواعيد المشاريع."""
    from projects.models import Project
    from notifications.models import Notification
    from users.models import User

    days_before = config.get('days_before_deadline', 7)
    deadline_date = timezone.now().date() + timedelta(days=days_before)

    upcoming_projects = Project.objects.filter(
        end_date__lte=deadline_date,
        status__in=['active', 'on_hold'],
    )

    alerts_sent = 0
    if upcoming_projects.exists():
        admin_users = User.objects.filter(
            is_active=True,
            role__in=['admin', 'project_manager'],
        )
        for user in admin_users:
            project_names = ', '.join([p.name for p in upcoming_projects[:5]])
            Notification.notify(
                user=user,
                title='تنبيه مواعيد مشاريع',
                message=f'يوجد {upcoming_projects.count()} مشاريع تقترب مواعيدها النهائية: {project_names}',
                notification_type='warning',
                link='/projects',
            )
            alerts_sent += 1

    return {
        'upcoming_deadlines': upcoming_projects.count(),
        'alerts_sent': alerts_sent,
    }
