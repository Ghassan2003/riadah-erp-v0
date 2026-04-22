"""
اختبارات الوحدات البرمجية لنماذج الإشعارات وسجل التدقيق والصيانة.
Unit Tests for Notifications, AuditLog, and Maintenance Models.
"""

import pytest


class TestNotificationModel:
    """اختبارات نموذج الإشعار."""

    def test_create_notification(self, notification):
        """اختبار إنشاء إشعار."""
        assert notification.title == 'إشعار اختبار'
        assert notification.message == 'هذا إشعار اختبار'
        assert notification.is_read is False

    def test_notification_str(self, notification):
        """اختبار التمثيل النصي."""
        assert 'إشعار اختبار' in str(notification)

    def test_mark_as_read(self, notification):
        """اختبار تعليم الإشعار كمقروء."""
        notification.mark_as_read()
        assert notification.is_read is True

    def test_mark_read_idempotent(self, notification):
        """اختبار أن التعليم كمقروء عملية آمنة."""
        notification.mark_as_read()
        notification.mark_as_read()
        assert notification.is_read is True

    def test_notify_static(self, admin_user):
        """اختبار إنشاء إشعار عبر الطريقة الثابتة."""
        from notifications.models import Notification
        notif = Notification.notify(
            admin_user, 'عنوان', 'رسالة', 'warning'
        )
        assert notif.recipient == admin_user
        assert notif.notification_type == 'warning'

    def test_notify_all_static(self, admin_user, sales_user):
        """اختبار إرسال إشعار لجميع المستخدمين."""
        from notifications.models import Notification
        result = Notification.notify_all('إعلان', 'رسالة عامة', 'info')
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_notification_type_choices(self, admin_user):
        """اختبار جميع أنواع الإشعارات."""
        from notifications.models import Notification
        types = ['info', 'success', 'warning', 'error', 'order', 'task', 'leave', 'system']
        for ntype in types:
            Notification.notify(admin_user, f'اختبار {ntype}', 'رسالة', ntype)


class TestAuditLogModel:
    """اختبارات نموذج سجل التدقيق."""

    def test_create_audit_log(self, admin_user):
        """اختبار إنشاء سجل تدقيق."""
        from auditlog.models import AuditLog
        log = AuditLog.log(
            user=admin_user,
            action='create',
            model_name='Product',
            object_id=1,
            object_repr='منتج اختبار',
        )
        assert log is not None
        assert log.action == 'create'

    def test_audit_log_action_choices(self, db):
        """اختبار جميع أنواع الإجراءات."""
        from auditlog.models import AuditLog
        from users.models import User
        user = User.objects.create_user(username='audit_test', password='Test@1234!', role='admin')
        actions = [
            'create', 'update', 'delete', 'soft_delete', 'restore',
            'status_change', 'login', 'logout', 'export', 'import',
            'backup', 'other',
        ]
        for action in actions:
            AuditLog.log(
                user=user,
                action=action,
                model_name='TestModel',
                object_id=1,
                object_repr=f'test_{action}',
            )


class TestMaintenanceModels:
    """اختبارات نماذج الصيانة."""

    def test_create_error_log(self, db):
        """اختبار إنشاء سجل خطأ."""
        from maintenance.models import ErrorLog
        error = ErrorLog.objects.create(
            level='error',
            source='backend',
            message='خطأ في الاختبار',
            code='TEST_001',
        )
        assert error.level == 'error'
        assert error.is_resolved is False

    def test_error_log_resolved(self, db):
        """اختبار حل خطأ."""
        from maintenance.models import ErrorLog
        error = ErrorLog.objects.create(
            level='warning',
            source='api',
            message='تحذير اختبار',
        )
        error.is_resolved = True
        error.resolution_notes = 'تم الحل'
        error.save()
        assert error.is_resolved is True

    def test_create_cron_job(self, admin_user):
        """اختبار إنشاء مهمة مجدولة."""
        from maintenance.models import CronJob
        job = CronJob.objects.create(
            name='اختبار مجدول',
            task='auto_backup_daily',
            frequency='daily',
            cron_expression='0 2 * * *',
            status='active',
            created_by=admin_user,
        )
        assert job.status == 'active'
        assert job.run_count == 0
        assert job.fail_count == 0

    def test_cron_job_success_rate(self, admin_user):
        """اختبار حساب نسبة النجاح."""
        from maintenance.models import CronJob
        job = CronJob.objects.create(
            name='مهمة اختبار',
            task='clean_old_logs',
            frequency='daily',
            cron_expression='0 3 * * *',
            status='active',
            run_count=10,
            fail_count=2,
            created_by=admin_user,
        )
        assert job.success_rate == 80.0

    def test_create_backup_record(self, admin_user):
        """اختبار إنشاء سجل نسخ احتياطي."""
        from maintenance.models import BackupRecord
        backup = BackupRecord.objects.create(
            filename='backup_test.db',
            file_path='/backups/backup_test.db',
            file_size=1024000,
            backup_type='manual',
            status='completed',
            tables_count=12,
            records_count=5000,
            created_by=admin_user,
        )
        assert backup.file_size_mb > 0
        assert backup.status == 'completed'

    def test_backup_file_size_mb(self, admin_user):
        """اختبار حساب حجم النسخة بالميغابايت."""
        from maintenance.models import BackupRecord
        backup = BackupRecord.objects.create(
            filename='small_backup.db',
            file_path='/backups/small.db',
            file_size=1048576,  # Exactly 1 MB
            backup_type='auto_daily',
            status='completed',
            created_by=admin_user,
        )
        assert backup.file_size_mb == 1.0

    def test_system_backup_settings(self, db):
        """اختبار إعدادات النسخ الاحتياطي."""
        from maintenance.models import SystemBackup
        settings = SystemBackup.objects.create(
            auto_backup_enabled=True,
            backup_frequency='daily',
            backup_time='02:00',
            keep_backups_count=30,
        )
        assert settings.auto_backup_enabled is True
        assert settings.keep_backups_count == 30
