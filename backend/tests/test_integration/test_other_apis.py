"""
اختبارات التكامل لنقاط نهاية الموارد البشرية والإشعارات وسجل التدقيق والصيانة.
Integration Tests for HR, Notifications, AuditLog, and Maintenance APIs.
"""

import pytest
from rest_framework import status


class TestDepartmentEndpoints:
    """اختبارات نقاط نهاية الأقسام."""

    def test_list_departments(self, authenticated_client, department):
        """اختبار قائمة الأقسام."""
        response = authenticated_client.get('/api/hr/departments/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_department(self, authenticated_client):
        """اختبار إنشاء قسم (مدير فقط)."""
        response = authenticated_client.post('/api/hr/departments/', {
            'name': 'قسم جديد',
            'name_en': 'New Department',
            'description': 'وصف القسم الجديد',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_department_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء قسم."""
        response = sales_client.post('/api/hr/departments/', {
            'name': 'ممنوع',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEmployeeEndpoints:
    """اختبارات نقاط نهاية الموظفين."""

    def test_list_employees(self, authenticated_client):
        """اختبار قائمة الموظفين."""
        response = authenticated_client.get('/api/hr/employees/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_employee(self, authenticated_client, department):
        """اختبار إنشاء موظف."""
        from users.models import User
        user = User.objects.create_user(username='new_emp', password='Emp@1234!', role='sales')
        response = authenticated_client.post('/api/hr/employees/', {
            'user': user.id,
            'first_name': 'موظف',
            'last_name': 'جديد',
            'email': 'emp@test.com',
            'department': department.id,
            'hire_date': '2024-01-15',
            'salary': '8000.00',
        })
        assert response.status_code == status.HTTP_201_CREATED


class TestLeaveRequestEndpoints:
    """اختبارات نقاط نهاية طلبات الإجازة."""

    def test_list_leaves(self, authenticated_client):
        """اختبار قائمة طلبات الإجازة."""
        response = authenticated_client.get('/api/hr/leaves/')
        assert response.status_code == status.HTTP_200_OK


class TestHRStatsEndpoint:
    """اختبارات نقطة نهاية إحصائيات الموارد البشرية."""

    def test_hr_stats(self, authenticated_client):
        """اختبار إحصائيات الموارد البشرية."""
        response = authenticated_client.get('/api/hr/stats/')
        assert response.status_code == status.HTTP_200_OK


class TestNotificationEndpoints:
    """اختبارات نقاط نهاية الإشعارات."""

    def test_list_notifications(self, authenticated_client, notification):
        """اختبار قائمة الإشعارات (ليست مقسمة لصفحات)."""
        response = authenticated_client.get('/api/notifications/')
        assert response.status_code == status.HTTP_200_OK
        # Notifications are not paginated (pagination_class = None)
        assert isinstance(response.data, list)

    def test_unread_count(self, authenticated_client, notification):
        """اختبار عداد الإشعارات غير المقروءة."""
        response = authenticated_client.get('/api/notifications/unread-count/')
        assert response.status_code == status.HTTP_200_OK
        assert 'unread_count' in response.data
        assert response.data['unread_count'] >= 1

    def test_mark_notification_read(self, authenticated_client, notification):
        """اختبار تعليم إشعار كمقروء."""
        response = authenticated_client.post(f'/api/notifications/{notification.id}/read/')
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read(self, authenticated_client, admin_user):
        """اختبار تعليم جميع الإشعارات كمقروءة."""
        from notifications.models import Notification
        Notification.notify(admin_user, 'إشعار 1', 'رسالة 1')
        Notification.notify(admin_user, 'إشعار 2', 'رسالة 2')
        response = authenticated_client.post('/api/notifications/mark-all-read/')
        assert response.status_code == status.HTTP_200_OK


class TestAuditLogEndpoints:
    """اختبارات نقاط نهاية سجل التدقيق."""

    def test_list_audit_logs_admin(self, authenticated_client):
        """اختبار قائمة سجل التدقيق (مدير)."""
        response = authenticated_client.get('/api/audit-log/')
        assert response.status_code == status.HTTP_200_OK

    def test_audit_log_stats(self, authenticated_client):
        """اختبار إحصائيات سجل التدقيق."""
        response = authenticated_client.get('/api/audit-log/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_audit_log_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من رؤية سجل التدقيق."""
        response = sales_client.get('/api/audit-log/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMaintenanceEndpoints:
    """اختبارات نقاط نهاية الصيانة - تستخدم البادئة المزدوجة الصحيحة."""

    def test_system_settings_get(self, authenticated_client):
        """اختبار جلب إعدادات النظام."""
        response = authenticated_client.get('/api/maintenance/maintenance/settings/')
        assert response.status_code == status.HTTP_200_OK

    def test_error_log_list(self, authenticated_client):
        """اختبار قائمة سجلات الأخطاء."""
        response = authenticated_client.get('/api/maintenance/maintenance/errors/')
        assert response.status_code == status.HTTP_200_OK

    def test_error_log_stats(self, authenticated_client):
        """اختبار إحصائيات الأخطاء."""
        response = authenticated_client.get('/api/maintenance/maintenance/errors/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_backup_list(self, authenticated_client):
        """اختبار قائمة النسخ الاحتياطية."""
        response = authenticated_client.get('/api/maintenance/maintenance/backups/')
        assert response.status_code == status.HTTP_200_OK

    def test_backup_stats(self, authenticated_client):
        """اختبار إحصائيات النسخ الاحتياطية."""
        response = authenticated_client.get('/api/maintenance/maintenance/backups/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_cron_jobs_list(self, authenticated_client):
        """اختبار قائمة المهام المجدولة."""
        response = authenticated_client.get('/api/maintenance/maintenance/cron-jobs/')
        assert response.status_code == status.HTTP_200_OK

    def test_cron_jobs_stats(self, authenticated_client):
        """اختبار إحصائيات المهام المجدولة."""
        response = authenticated_client.get('/api/maintenance/maintenance/cron-jobs/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_maintenance_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من الوصول للصيانة."""
        response = sales_client.get('/api/maintenance/maintenance/settings/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = sales_client.get('/api/maintenance/maintenance/errors/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = sales_client.get('/api/maintenance/maintenance/backups/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDashboardEndpoints:
    """اختبارات نقاط نهاية لوحة التحكم."""

    def test_system_info(self, authenticated_client):
        """اختبار معلومات النظام."""
        response = authenticated_client.get('/api/system/info/')
        assert response.status_code == status.HTTP_200_OK
        assert 'version' in response.data
        assert 'python_version' in response.data
        assert 'django_version' in response.data

    def test_dashboard_unauthenticated(self, api_client):
        """اختبار منع غير المصادق من لوحة التحكم."""
        response = api_client.get('/api/dashboard/stats/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
