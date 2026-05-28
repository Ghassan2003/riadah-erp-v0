"""
Shared test fixtures for the ERP test suite.

Provides reusable fixtures for users, API clients, model instances,
and permissions. Designed to work with pytest-django and DRF.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


# ============================================================
# API Client fixtures
# ============================================================


@pytest.fixture
def api_client():
    """DRF APIClient (unauthenticated)."""
    return APIClient()


# ============================================================
# User fixtures
# ============================================================


@pytest.fixture
def admin_user(db):
    """User with role='admin'.

    Username is 'admin_test' to match the str() test assertion:
        assert 'admin_test' in str(admin_user)
    """
    from users.models import User
    return User.objects.create_superuser(
        username='admin_test',
        email='admin@test.com',
        password='Admin@123',
    )


@pytest.fixture
def sales_user(db):
    """User with role='sales'."""
    from users.models import User
    return User.objects.create_user(
        username='sales_user',
        email='sales@test.com',
        password='Sales@123',
        role='sales',
        is_active=True,
    )


@pytest.fixture
def warehouse_user(db):
    """User with role='warehouse'."""
    from users.models import User
    return User.objects.create_user(
        username='warehouse_user',
        email='warehouse@test.com',
        password='Warehouse@123',
        role='warehouse',
        is_active=True,
    )


@pytest.fixture
def accountant_user(db):
    """User with role='accountant'."""
    from users.models import User
    return User.objects.create_user(
        username='accountant_user',
        email='accountant@test.com',
        password='Accountant@123',
        role='accountant',
        is_active=True,
    )


@pytest.fixture
def hr_user(db):
    """User with role='hr'."""
    from users.models import User
    return User.objects.create_user(
        username='hr_user',
        email='hr@test.com',
        password='Hr@123',
        role='hr',
        is_active=True,
    )


# ============================================================
# Authenticated Client fixtures (JWT)
# ============================================================


def _get_auth_client(user):
    """Helper to create an authenticated APIClient with a JWT Bearer token."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def authenticated_client(admin_user, seed_permissions):
    """APIClient authenticated as admin_user via JWT.
    
    Seeds permissions and links all permissions to admin role.
    """
    from users.models import RolePermission, Permission
    # Link all permissions to admin role (admin should have access to everything)
    for perm in Permission.objects.all():
        RolePermission.objects.get_or_create(role='admin', permission=perm)
    return _get_auth_client(admin_user)


@pytest.fixture
def sales_client(sales_user, seed_permissions):
    """APIClient authenticated as sales_user via JWT.
    
    Seeds permissions and links sales permissions to sales role.
    """
    from users.models import RolePermission, Permission
    sales_perms = Permission.objects.filter(
        module__in=['sales', 'inventory', 'dashboard', 'notifications']
    )
    for perm in sales_perms:
        RolePermission.objects.get_or_create(role='sales', permission=perm)
    return _get_auth_client(sales_user)


@pytest.fixture
def accountant_client(accountant_user, seed_permissions):
    """APIClient authenticated as accountant_user via JWT.
    
    Seeds permissions and links accounting permissions to accountant role.
    """
    from users.models import RolePermission, Permission
    # Link accounting permissions to accountant role
    accounting_perms = Permission.objects.filter(module__in=['accounting', 'reports'])
    for perm in accounting_perms:
        RolePermission.objects.get_or_create(role='accountant', permission=perm)
    return _get_auth_client(accountant_user)


@pytest.fixture
def warehouse_client(warehouse_user):
    """APIClient authenticated as warehouse_user via JWT."""
    return _get_auth_client(warehouse_user)


# ============================================================
# Model instance fixtures
# ============================================================


@pytest.fixture
def department(db):
    """Department instance (name='قسم التقنية')."""
    from hr.models import Department
    return Department.objects.create(
        name='قسم التقنية',
        name_en='IT Department',
        description='قسم تكنولوجيا المعلومات',
    )


@pytest.fixture
def customer(db):
    """Customer instance."""
    from sales.models import Customer
    return Customer.objects.create(
        name='عميل اختبار',
        email='customer@test.com',
        phone='0501234567',
        address='الرياض، المملكة العربية السعودية',
    )


@pytest.fixture
def notification(admin_user):
    """Notification instance for admin_user."""
    from notifications.models import Notification
    return Notification.objects.create(
        recipient=admin_user,
        title='إشعار اختبار',
        message='هذا إشعار اختبار',
        notification_type='info',
    )


@pytest.fixture
def account_asset(db):
    """Account with account_type='asset' (code='1000')."""
    from accounting.models import Account
    return Account.objects.create(
        code='1000',
        name='الأصول',
        name_en='Assets',
        account_type='asset',
    )


@pytest.fixture
def account_revenue(db):
    """Account with account_type='income' (code='4000').

    Note: The model uses AccountType.INCOME = 'income', not 'revenue'.
    """
    from accounting.models import Account
    return Account.objects.create(
        code='4000',
        name='الإيرادات',
        name_en='Revenue',
        account_type='income',
    )


# ============================================================
# Permission fixtures
# ============================================================


@pytest.fixture
def seed_permissions(db):
    """Create a standard set of Permission objects (idempotent via get_or_create)."""
    from users.models import Permission

    permissions_data = [
        {'module': 'dashboard', 'action': 'view', 'description': 'عرض لوحة التحكم'},
        {'module': 'inventory', 'action': 'view', 'description': 'عرض المخزون'},
        {'module': 'inventory', 'action': 'create', 'description': 'إنشاء منتج'},
        {'module': 'inventory', 'action': 'edit', 'description': 'تعديل منتج'},
        {'module': 'inventory', 'action': 'delete', 'description': 'حذف منتج'},
        {'module': 'inventory', 'action': 'export', 'description': 'تصدير المخزون'},
        {'module': 'sales', 'action': 'view', 'description': 'عرض المبيعات'},
        {'module': 'sales', 'action': 'create', 'description': 'إنشاء أمر بيع'},
        {'module': 'sales', 'action': 'edit', 'description': 'تعديل أمر بيع'},
        {'module': 'sales', 'action': 'delete', 'description': 'حذف أمر بيع'},
        {'module': 'accounting', 'action': 'view', 'description': 'عرض المحاسبة'},
        {'module': 'accounting', 'action': 'create', 'description': 'إنشاء قيد يومية'},
        {'module': 'accounting', 'action': 'edit', 'description': 'تعديل قيد'},
        {'module': 'hr', 'action': 'view', 'description': 'عرض الموارد البشرية'},
        {'module': 'hr', 'action': 'manage', 'description': 'إدارة كاملة للموارد البشرية'},
        {'module': 'reports', 'action': 'view', 'description': 'عرض التقارير'},
        {'module': 'reports', 'action': 'export', 'description': 'تصدير التقارير'},
        {'module': 'users', 'action': 'view', 'description': 'عرض المستخدمين'},
        {'module': 'users', 'action': 'manage', 'description': 'إدارة كاملة للمستخدمين'},
        {'module': 'notifications', 'action': 'view', 'description': 'عرض الإشعارات'},
        {'module': 'pos', 'action': 'view', 'description': 'عرض نقاط البيع'},
        {'module': 'pos', 'action': 'manage', 'description': 'إدارة نقاط البيع'},
        {'module': 'payments', 'action': 'view', 'description': 'عرض المدفوعات'},
        {'module': 'payments', 'action': 'manage', 'description': 'إدارة المدفوعات'},
        {'module': 'backup', 'action': 'manage', 'description': 'إدارة النسخ الاحتياطي'},
    ]

    for perm_data in permissions_data:
        Permission.objects.get_or_create(
            module=perm_data['module'],
            action=perm_data['action'],
            defaults={'description': perm_data.get('description', '')},
        )

    return Permission.objects.all()


@pytest.fixture
def permission_obj(db):
    """Single Permission instance (module='inventory', action='view')."""
    from users.models import Permission
    return Permission.objects.create(
        module='inventory',
        action='view',
        description='عرض المخزون',
    )


# ============================================================
# Removed module fixtures (skip)
# ============================================================


@pytest.fixture
def product():
    """Product fixture — skipped because the inventory module has been removed.

    Tests that request this fixture will be automatically skipped.
    """
    pytest.skip("inventory module removed — Product model no longer available")
