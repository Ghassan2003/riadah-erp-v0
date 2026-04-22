"""
اختبارات الوحدات البرمجية لنماذج المستخدمين والمصادقة.
Unit Tests for User Models and Authentication.
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class TestUserModel:
    """اختبارات نموذج المستخدم."""

    def test_create_user(self, db):
        """اختبار إنشاء مستخدم جديد."""
        from users.models import User
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='Test@1234!',
            role='sales',
        )
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
        assert user.role == 'sales'
        assert user.is_active is True
        assert user.check_password('Test@1234!')

    def test_user_role_properties(self, admin_user, sales_user, warehouse_user):
        """اختبار خصائص الأدوار."""
        assert admin_user.is_admin is True
        assert admin_user.is_warehouse is True
        assert admin_user.is_sales is True
        assert admin_user.is_accountant is True
        assert admin_user.is_hr is True
        assert admin_user.is_project_manager is True

        assert sales_user.is_admin is False
        assert sales_user.is_sales is True
        assert sales_user.is_warehouse is False

        assert warehouse_user.is_warehouse is True
        assert warehouse_user.is_admin is False

    def test_user_str_representation(self, admin_user):
        """اختبار التمثيل النصي للمستخدم."""
        assert 'admin_test' in str(admin_user)
        assert 'مدير النظام' in str(admin_user)

    def test_password_change_recording(self, db):
        """اختبار تسجيل تغيير كلمة المرور."""
        from users.models import User
        user = User.objects.create_user(
            username='passtest',
            password='OldPass@1234!',
            role='sales',
        )
        user.record_password_change('OldPass@1234!')
        assert user.password_changed_at is not None
        assert user.must_change_password is False
        assert len(user.password_history) == 1

    def test_password_in_history(self, db):
        """اختبار كشف إعادة استخدام كلمة المرور."""
        from users.models import User
        user = User.objects.create_user(
            username='historytest',
            password='Pass@1234!',
            role='sales',
        )
        user.record_password_change('Pass@1234!')
        assert user.is_password_in_history('Pass@1234!') is True
        assert user.is_password_in_history('NewPass@1234!') is False

    def test_password_expiry_not_expired(self, db):
        """اختبار أن كلمة المرور لم تنتهِ صلاحيتها."""
        from users.models import User
        user = User.objects.create_user(
            username='expirynot',
            password='Pass@1234!',
            role='sales',
        )
        user.password_changed_at = timezone.now() - timedelta(days=30)
        user.save()
        assert user.is_password_expired is False
        assert user.days_until_password_expiry > 50

    def test_password_expiry_expired(self, db):
        """اختبار أن كلمة المرور انتهت صلاحيتها."""
        from users.models import User
        user = User.objects.create_user(
            username='expiredtest',
            password='Pass@1234!',
            role='sales',
        )
        user.password_changed_at = timezone.now() - timedelta(days=100)
        user.save()
        assert user.is_password_expired is True
        assert user.days_until_password_expiry == 0

    def test_generate_backup_codes(self, admin_user):
        """اختبار توليد رموز الاسترداد."""
        codes = admin_user.generate_backup_codes(10)
        assert len(codes) == 10
        assert len(admin_user.two_factor_backup_codes) == 10

    def test_verify_backup_code(self, admin_user):
        """اختبار التحقق من رمز الاسترداد."""
        codes = admin_user.generate_backup_codes(5)
        code = codes[0]
        assert admin_user.verify_backup_code(code) is True
        assert admin_user.verify_backup_code(code) is False  # Used

    def test_verify_invalid_backup_code(self, admin_user):
        """اختبار رمز استرداد غير صالح."""
        assert admin_user.verify_backup_code('INVALID01') is False


class TestPermissionModel:
    """اختبارات نموذج الصلاحيات."""

    def test_create_permission(self, db):
        """اختبار إنشاء صلاحية."""
        from users.models import Permission
        perm = Permission.objects.create(
            module='inventory',
            action='view',
            description='عرض المخزون',
        )
        assert perm.code == 'inventory_view'
        assert perm.module == 'inventory'
        assert perm.action == 'view'

    def test_permission_unique_code(self, db):
        """اختبار تفرد رمز الصلاحية."""
        from users.models import Permission
        Permission.objects.create(module='inventory', action='view')
        with pytest.raises(Exception):
            Permission.objects.create(module='inventory', action='view')

    def test_permission_str(self, permission_obj):
        """اختبار التمثيل النصي للصلاحية."""
        assert 'inventory_view' in str(permission_obj) or 'إدارة المخزون' in str(permission_obj)


class TestRolePermissionModel:
    """اختبارات نموذج صلاحيات الأدوار."""

    def test_create_role_permission(self, db):
        """اختبار ربط دور بصلاحية."""
        from users.models import Permission, RolePermission
        perm = Permission.objects.create(module='inventory', action='create')
        rp = RolePermission.objects.create(role='sales', permission=perm)
        assert rp.role == 'sales'
        assert rp.permission == perm

    def test_unique_role_permission(self, db):
        """اختبار عدم تكرار ربط الدور بالصلاحية."""
        from users.models import Permission, RolePermission
        perm = Permission.objects.create(module='inventory', action='view')
        RolePermission.objects.create(role='sales', permission=perm)
        with pytest.raises(Exception):
            RolePermission.objects.create(role='sales', permission=perm)


class TestSystemSettingModel:
    """اختبارات نموذج إعدادات النظام."""

    def test_set_and_get_setting(self, db):
        """اختبار تعيين وقراءة إعداد."""
        from users.models import SystemSetting
        SystemSetting.set('test_key', 'test_value', 'وصف اختبار')
        assert SystemSetting.get('test_key') == 'test_value'

    def test_get_nonexistent_setting(self, db):
        """اختبار قراءة إعداد غير موجود."""
        from users.models import SystemSetting
        assert SystemSetting.get('nonexistent') == ''
        assert SystemSetting.get('nonexistent', 'default_val') == 'default_val'

    def test_update_setting(self, db):
        """اختبار تحديث إعداد."""
        from users.models import SystemSetting
        SystemSetting.set('update_key', 'old_value')
        SystemSetting.set('update_key', 'new_value')
        assert SystemSetting.get('update_key') == 'new_value'
