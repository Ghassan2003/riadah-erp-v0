"""
اختبارات التكامل لنقاط نهاية المصادقة والمستخدمين.
Integration Tests for Authentication and User API Endpoints.
"""

import pytest
from rest_framework import status


class TestAuthEndpoints:
    """اختبارات نقاط نهاية المصادقة."""

    def test_login_success(self, db, api_client):
        """اختبار تسجيل الدخول بنجاح."""
        from users.models import User
        user = User.objects.create_user(
            username='login_test',
            password='Login@1234!',
            role='admin',
            is_staff=True,
        )
        response = api_client.post('/api/auth/login/', {
            'username': 'login_test',
            'password': 'Login@1234!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['requires_2fa'] is False
        assert 'user' in response.data

    def test_login_invalid_credentials(self, db, api_client):
        """اختبار تسجيل الدخول ببيانات خاطئة."""
        response = api_client.post('/api/auth/login/', {
            'username': 'nonexistent',
            'password': 'wrongpass',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, db, api_client):
        """اختبار تسجيل الدخول بحساب معطّل."""
        from users.models import User
        user = User.objects.create_user(
            username='inactive_user',
            password='Test@1234!',
            role='sales',
        )
        user.is_active = False
        user.save()
        response = api_client.post('/api/auth/login/', {
            'username': 'inactive_user',
            'password': 'Test@1234!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_2fa_enabled(self, db, api_client):
        """اختبار تسجيل الدخول مع المصادقة الثنائية."""
        from users.models import User
        user = User.objects.create_user(
            username='twofa_user',
            password='TwoFA@1234!',
            role='admin',
        )
        user.two_factor_enabled = True
        user.totp_secret = 'JBSWY3DPEHPK3PXP'
        user.save()
        response = api_client.post('/api/auth/login/', {
            'username': 'twofa_user',
            'password': 'TwoFA@1234!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['requires_2fa'] is True

    def test_token_refresh(self, admin_user, api_client):
        """اختبار تجديد رمز الوصول."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(admin_user)
        response = api_client.post('/api/auth/refresh/', {
            'refresh': str(refresh),
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


class TestUserProfileEndpoints:
    """اختبارات نقاط نهاية الملف الشخصي."""

    def test_get_profile(self, authenticated_client, admin_user):
        """اختبار جلب الملف الشخصي."""
        response = authenticated_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == admin_user.username
        assert response.data['role'] == 'admin'
        assert 'permissions' in response.data

    def test_update_profile(self, authenticated_client):
        """اختبار تحديث الملف الشخصي."""
        response = authenticated_client.patch('/api/auth/profile/', {
            'first_name': 'محدث',
            'last_name': 'الاسم',
            'phone': '0551234567',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_profile_access(self, api_client):
        """اختبار محاولة الوصول للملف الشخصي بدون مصادقة."""
        response = api_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePasswordEndpoint:
    """اختبارات نقطة نهاية تغيير كلمة المرور."""

    def test_change_password_success(self, authenticated_client, admin_user):
        """اختبار تغيير كلمة المرور بنجاح."""
        admin_user.set_password('OldPass@1234!')
        admin_user.save()
        admin_user.record_password_change('OldPass@1234!')

        response = authenticated_client.post('/api/auth/change-password/', {
            'old_password': 'OldPass@1234!',
            'new_password': 'BrandNew@Pass1!',
            'new_password_confirm': 'BrandNew@Pass1!',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client):
        """اختبار كلمة المرور القديمة خاطئة."""
        response = authenticated_client.post('/api/auth/change-password/', {
            'old_password': 'WrongOld@1!',
            'new_password': 'NewPass@1234!',
            'new_password_confirm': 'NewPass@1234!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserManagementEndpoints:
    """اختبارات نقاط نهاية إدارة المستخدمين."""

    def test_list_users_admin(self, authenticated_client, admin_user, sales_user):
        """اختبار قائمة المستخدمين كمدير."""
        response = authenticated_client.get('/api/auth/users/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_non_admin(self, sales_client):
        """اختبار منع غير المدير من رؤية قائمة المستخدمين."""
        response = sales_client.get('/api/auth/users/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_detail(self, authenticated_client, sales_user):
        """اختبار جلب تفاصيل مستخدم."""
        response = authenticated_client.get(f'/api/auth/users/{sales_user.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_by_admin(self, authenticated_client):
        """اختبار إنشاء مستخدم بواسطة المدير."""
        response = authenticated_client.post('/api/auth/users/create/', {
            'username': 'new_staff_user',
            'email': 'newstaff@test.com',
            'password': 'Str0ngP@ssw0rd!',
            'password_confirm': 'Str0ngP@ssw0rd!',
            'role': 'sales',
            'first_name': 'مستخدم',
            'last_name': 'جديد',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_toggle_user_active(self, authenticated_client, sales_user):
        """اختبار تفعيل/تعطيل مستخدم."""
        response = authenticated_client.patch(f'/api/auth/users/{sales_user.id}/toggle-active/')
        assert response.status_code == status.HTTP_200_OK
        sales_user.refresh_from_db()
        assert sales_user.is_active is False

        # Toggle back
        response = authenticated_client.patch(f'/api/auth/users/{sales_user.id}/toggle-active/')
        assert response.status_code == status.HTTP_200_OK

    def test_non_admin_cannot_create_user(self, sales_client):
        """اختبار منع غير المدير من إنشاء مستخدم."""
        response = sales_client.post('/api/auth/users/create/', {
            'username': 'unauthorized',
            'password': 'Test@1234!',
            'password_confirm': 'Test@1234!',
            'role': 'sales',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class Test2FAEndpoints:
    """اختبارات نقاط نهاية المصادقة الثنائية."""

    def test_2fa_status(self, authenticated_client):
        """اختبار حالة المصادقة الثنائية."""
        response = authenticated_client.get('/api/auth/2fa/status/')
        assert response.status_code == status.HTTP_200_OK
        assert 'enabled' in response.data

    def test_2fa_setup(self, authenticated_client, admin_user):
        """اختبار إعداد المصادقة الثنائية."""
        admin_user.set_password('Pass@1234!')
        admin_user.save()
        response = authenticated_client.post('/api/auth/2fa/setup/', {
            'password': 'Pass@1234!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'secret' in response.data
        assert 'backup_codes' in response.data

    def test_2fa_disable(self, authenticated_client, admin_user):
        """اختبار تعطيل المصادقة الثنائية."""
        admin_user.two_factor_enabled = True
        admin_user.save()
        admin_user.set_password('Pass@1234!')
        admin_user.save()
        response = authenticated_client.post('/api/auth/2fa/disable/', {
            'password': 'Pass@1234!',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_admin_reset_2fa(self, authenticated_client, sales_user):
        """اختبار إعادة تعيين المصادقة الثنائية بواسطة المدير."""
        sales_user.two_factor_enabled = True
        sales_user.save()
        response = authenticated_client.post(f'/api/auth/users/{sales_user.id}/reset-2fa/')
        assert response.status_code == status.HTTP_200_OK
        sales_user.refresh_from_db()
        assert sales_user.two_factor_enabled is False

    def test_admin_force_change_password(self, authenticated_client, sales_user):
        """اختبار إجبار تغيير كلمة المرور."""
        response = authenticated_client.post(
            f'/api/auth/users/{sales_user.id}/force-change-password/'
        )
        assert response.status_code == status.HTTP_200_OK
        sales_user.refresh_from_db()
        assert sales_user.must_change_password is True


class TestPermissionEndpoints:
    """اختبارات نقاط نهاية الصلاحيات."""

    def test_list_permissions(self, authenticated_client, seed_permissions):
        """اختبار قائمة الصلاحيات."""
        response = authenticated_client.get('/api/auth/permissions/')
        assert response.status_code == status.HTTP_200_OK

    def test_all_role_permissions(self, authenticated_client, seed_permissions):
        """اختبار صلاحيات جميع الأدوار."""
        response = authenticated_client.get('/api/auth/permissions/roles/')
        assert response.status_code == status.HTTP_200_OK

    def test_check_permission(self, authenticated_client):
        """اختبار التحقق من صلاحية."""
        response = authenticated_client.post('/api/auth/permissions/check/', {
            'code': 'inventory_view',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'has_permission' in response.data

    def test_my_permissions(self, authenticated_client):
        """اختبار صلاحياتي."""
        response = authenticated_client.get('/api/auth/permissions/my/')
        assert response.status_code == status.HTTP_200_OK

    def test_seed_permissions(self, authenticated_client):
        """اختبار بذر الصلاحيات."""
        response = authenticated_client.post('/api/auth/permissions/seed/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_role_permissions(self, authenticated_client, seed_permissions):
        """اختبار تحديث صلاحيات دور."""
        perm_ids = [p.id for p in seed_permissions[:3]]
        response = authenticated_client.put('/api/auth/permissions/roles/sales/update/', {
            'role': 'sales',
            'permission_ids': perm_ids,
        })
        assert response.status_code == status.HTTP_200_OK


class TestPasswordPolicyEndpoints:
    """اختبارات نقاط نهاية سياسة كلمة المرور."""

    def test_get_password_policy(self, authenticated_client):
        """اختبار جلب سياسة كلمة المرور."""
        response = authenticated_client.get('/api/auth/password-policy/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_password_policy(self, authenticated_client):
        """اختبار تحديث سياسة كلمة المرور."""
        response = authenticated_client.put('/api/auth/password-policy/', {
            'min_length': 10,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
            'password_expiry_days': 60,
            'password_history_count': 8,
        })
        assert response.status_code == status.HTTP_200_OK

    def test_password_policy_info(self, authenticated_client):
        """اختبار معلومات سياسة كلمة المرور."""
        response = authenticated_client.get('/api/auth/password-policy/info/')
        assert response.status_code == status.HTTP_200_OK
