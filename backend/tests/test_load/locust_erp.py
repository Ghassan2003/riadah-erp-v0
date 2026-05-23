"""
اختبارات الضغط (Stress/Load Tests) لنظام ERP باستخدام Locust.
يتم تشغيلها بأمر: locust -f tests/test_load/locustfile.py --headless -u 50 -r 5 -t 5m

أو يمكن تشغيلها عبر Django management command.
"""

import os
import sys
import time
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import django
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


class ERPUser(HttpUser):
    """
    محاكاة مستخدم ERP يتفاعل مع النظام.
    Simulates an ERP user interacting with the system.
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """تسجيل الدخول والحصول على رمز الوصول."""
        self.login()

    def login(self):
        """تسجيل الدخول وجلب رمز JWT."""
        # Use a test admin user
        try:
            user = User.objects.get(username='admin_test')
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username='admin_test',
                email='load@test.com',
                password='LoadTest@1234!',
            )

        refresh = RefreshToken.for_user(user)
        self.token = str(refresh.access_token)
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

    # ===== Dashboard Tasks =====

    @task(5)
    def get_dashboard_stats(self):
        """جلب إحصائيات لوحة التحكم."""
        self.client.get('/api/dashboard/stats/', headers=self.headers, name='Dashboard Stats')

    @task(2)
    def get_system_info(self):
        """جلب معلومات النظام."""
        self.client.get('/api/system/info/', headers=self.headers, name='System Info')

    # ===== Inventory Tasks =====

    @task(8)
    def list_products(self):
        """عرض قائمة المنتجات."""
        self.client.get('/api/inventory/products/', headers=self.headers, name='List Products')

    @task(3)
    def get_inventory_stats(self):
        """جلب إحصائيات المخزون."""
        self.client.get('/api/inventory/stats/', headers=self.headers, name='Inventory Stats')

    @task(2)
    def search_products(self):
        """البحث في المنتجات."""
        search_term = random.choice(['منتج', 'TEST', 'inventory', 'محزون'])
        self.client.get(
            f'/api/inventory/products/?search={search_term}',
            headers=self.headers,
            name='Search Products'
        )

    @task(1)
    def get_product_detail(self):
        """جلب تفاصيل منتج عشوائي."""
        product_id = random.randint(1, 1000)
        self.client.get(
            f'/api/inventory/products/{product_id}/',
            headers=self.headers,
            name='Product Detail'
        )

    # ===== Sales Tasks =====

    @task(6)
    def list_sales_orders(self):
        """عرض قائمة أوامر البيع."""
        self.client.get('/api/sales/orders/', headers=self.headers, name='List Sales Orders')

    @task(4)
    def list_customers(self):
        """عرض قائمة العملاء."""
        self.client.get('/api/sales/customers/', headers=self.headers, name='List Customers')

    @task(2)
    def get_sales_stats(self):
        """جلب إحصائيات المبيعات."""
        self.client.get('/api/sales/stats/', headers=self.headers, name='Sales Stats')

    # ===== Accounting Tasks =====

    @task(5)
    def list_accounts(self):
        """عرض قائمة الحسابات."""
        self.client.get('/api/accounting/accounts/', headers=self.headers, name='List Accounts')

    @task(4)
    def list_journal_entries(self):
        """عرض قيود اليومية."""
        self.client.get('/api/accounting/entries/', headers=self.headers, name='List Journal Entries')

    @task(2)
    def get_accounting_stats(self):
        """جلب إحصائيات المحاسبة."""
        self.client.get('/api/accounting/stats/', headers=self.headers, name='Accounting Stats')

    # ===== HR Tasks =====

    @task(4)
    def list_employees(self):
        """عرض قائمة الموظفين."""
        self.client.get('/api/hr/employees/', headers=self.headers, name='List Employees')

    @task(3)
    def list_departments(self):
        """عرض قائمة الأقسام."""
        self.client.get('/api/hr/departments/', headers=self.headers, name='List Departments')

    @task(3)
    def list_attendance(self):
        """عرض سجلات الحضور."""
        self.client.get('/api/hr/attendance/', headers=self.headers, name='List Attendance')

    @task(2)
    def list_leaves(self):
        """عرض طلبات الإجازة."""
        self.client.get('/api/hr/leaves/', headers=self.headers, name='List Leaves')

    @task(2)
    def get_hr_stats(self):
        """جلب إحصائيات الموارد البشرية."""
        self.client.get('/api/hr/stats/', headers=self.headers, name='HR Stats')

    # ===== Notifications Tasks =====

    @task(5)
    def list_notifications(self):
        """عرض قائمة الإشعارات."""
        self.client.get('/api/notifications/', headers=self.headers, name='List Notifications')

    @task(3)
    def get_unread_count(self):
        """جلب عداد الإشعارات غير المقروءة."""
        self.client.get(
            '/api/notifications/unread-count/',
            headers=self.headers,
            name='Unread Count'
        )

    # ===== Audit Log Tasks =====

    @task(3)
    def list_audit_logs(self):
        """عرض سجل التدقيق."""
        self.client.get('/api/audit-log/', headers=self.headers, name='List Audit Logs')

    # ===== Maintenance Tasks =====

    @task(2)
    def get_system_settings(self):
        """جلب إعدادات النظام."""
        self.client.get('/api/maintenance/settings/', headers=self.headers, name='System Settings')

    @task(2)
    def list_error_logs(self):
        """عرض سجلات الأخطاء."""
        self.client.get('/api/maintenance/errors/', headers=self.headers, name='List Error Logs')

    @task(1)
    def list_backups(self):
        """عرض النسخ الاحتياطية."""
        self.client.get('/api/maintenance/backups/', headers=self.headers, name='List Backups')

    @task(1)
    def list_cron_jobs(self):
        """عرض المهام المجدولة."""
        self.client.get('/api/maintenance/cron-jobs/', headers=self.headers, name='List Cron Jobs')

    # ===== Purchases Tasks =====

    @task(4)
    def list_purchase_orders(self):
        """عرض قائمة أوامر الشراء."""
        self.client.get('/api/purchases/orders/', headers=self.headers, name='List Purchase Orders')

    @task(3)
    def list_suppliers(self):
        """عرض قائمة الموردين."""
        self.client.get('/api/purchases/suppliers/', headers=self.headers, name='List Suppliers')

    @task(2)
    def get_purchase_stats(self):
        """جلب إحصائيات المشتريات."""
        self.client.get('/api/purchases/stats/', headers=self.headers, name='Purchase Stats')

    # ===== Projects Tasks =====

    @task(3)
    def list_projects(self):
        """عرض قائمة المشاريع."""
        self.client.get('/api/projects/', headers=self.headers, name='List Projects')

    @task(2)
    def list_project_tasks(self):
        """عرض مهام المشاريع."""
        self.client.get('/api/projects/tasks/', headers=self.headers, name='List Project Tasks')

    # ===== Documents Tasks =====

    @task(2)
    def list_documents(self):
        """عرض قائمة المستندات."""
        self.client.get('/api/documents/', headers=self.headers, name='List Documents')

    @task(1)
    def list_document_categories(self):
        """عرض فئات المستندات."""
        self.client.get('/api/documents/categories/', headers=self.headers, name='Document Categories')

    # ===== Profile & Permissions =====

    @task(4)
    def get_profile(self):
        """جلب الملف الشخصي."""
        self.client.get('/api/auth/profile/', headers=self.headers, name='Get Profile')

    @task(2)
    def get_my_permissions(self):
        """جلب صلاحياتي."""
        self.client.get('/api/auth/permissions/my/', headers=self.headers, name='My Permissions')

    @task(1)
    def get_password_policy_info(self):
        """جلب معلومات سياسة كلمة المرور."""
        self.client.get(
            '/api/auth/password-policy/info/',
            headers=self.headers,
            name='Password Policy Info'
        )


class StressTestUser(ERPUser):
    """
    مستخدم اختبار الضغط - يرسل طلبات مكثفة.
    Stress test user - sends intensive requests.
    """

    wait_time = between(0.1, 0.5)  # Very short wait time for stress testing

    @task(10)
    def rapid_dashboard(self):
        """طلبات سريعة للوحة التحكم."""
        self.client.get('/api/dashboard/stats/', headers=self.headers, name='[STRESS] Dashboard')

    @task(8)
    def rapid_products(self):
        """طلبات سريعة للمنتجات."""
        self.client.get('/api/inventory/products/', headers=self.headers, name='[STRESS] Products')

    @task(6)
    def rapid_orders(self):
        """طلبات سريعة لأوامر البيع."""
        self.client.get('/api/sales/orders/', headers=self.headers, name='[STRESS] Orders')

    @task(4)
    def rapid_accounts(self):
        """طلبات سريعة للحسابات."""
        self.client.get('/api/accounting/accounts/', headers=self.headers, name='[STRESS] Accounts')

    @task(4)
    def rapid_notifications(self):
        """طلبات سريعة للإشعارات."""
        self.client.get('/api/notifications/', headers=self.headers, name='[STRESS] Notifications')


# Event listeners for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """تسجيل تفاصيل الطلبات."""
    if exception:
        print(f"[ERROR] {name}: {exception}")
    elif response_time > 5000:  # Slow request warning (>5s)
        print(f"[SLOW] {name}: {response_time:.0f}ms")
