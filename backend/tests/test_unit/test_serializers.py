"""
اختبارات الوحدات البرمجية للمسلسلات (Serializers).
Unit Tests for Serializers - User, Product, Sales.
"""

import pytest
from rest_framework import serializers


class TestUserSerializers:
    """اختبارات مسلسلات المستخدم."""

    def test_registration_serializer_valid(self, db):
        """اختبار مسلسل التسجيل ببيانات صالحة."""
        from users.serializers import UserRegistrationSerializer
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'Str0ng!Pass#99',
            'password_confirm': 'Str0ng!Pass#99',
            'role': 'sales',
            'first_name': 'مستخدم',
            'last_name': 'جديد',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid() is True

    def test_registration_serializer_password_mismatch(self, db):
        """اختبار مسلسل التسجيل بكلمات مرور غير متطابقة."""
        from users.serializers import UserRegistrationSerializer
        data = {
            'username': 'newuser2',
            'email': 'new2@test.com',
            'password': 'Str0ng!Pass#99',
            'password_confirm': 'Differ@ntPass1',
            'role': 'sales',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password_confirm' in serializer.errors or 'non_field_errors' in serializer.errors

    def test_registration_serializer_short_password(self, db):
        """اختبار مسلسل التسجيل بكلمة مرور قصيرة."""
        from users.serializers import UserRegistrationSerializer
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'Short1!',
            'password_confirm': 'Short1!',
            'role': 'sales',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid() is False

    def test_registration_serializer_no_complexity(self, db):
        """اختبار مسلسل التسجيل بكلمة مرور بسيطة."""
        from users.serializers import UserRegistrationSerializer
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'simplepassword',
            'password_confirm': 'simplepassword',
            'role': 'sales',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid() is False

    def test_user_update_serializer(self, admin_user):
        """اختبار مسلسل تحديث بيانات المستخدم."""
        from users.serializers import UserUpdateSerializer
        data = {
            'first_name': 'محدث',
            'last_name': 'البيانات',
            'email': 'updated@test.com',
        }
        serializer = UserUpdateSerializer(data=data, context={'request': type('Req', (), {'user': admin_user})()})
        assert serializer.is_valid() is True

    def test_user_serializer_output(self, admin_user):
        """اختبار إخراج مسلسل المستخدم."""
        from users.serializers import UserSerializer
        serializer = UserSerializer(admin_user)
        data = serializer.data
        assert data['username'] == admin_user.username
        assert data['role'] == 'admin'
        assert 'role_display' in data
        assert 'two_factor_enabled' in data
        assert 'days_until_password_expiry' in data

    def test_change_password_serializer_valid(self, admin_user):
        """اختبار مسلسل تغيير كلمة المرور ببيانات صالحة."""
        from users.serializers import ChangePasswordSerializer
        # Create a mock request with user that has password set
        admin_user.set_password('OldPass@1234!')
        admin_user.save()
        admin_user.record_password_change('OldPass@1234!')

        data = {
            'old_password': 'OldPass@1234!',
            'new_password': 'BrandNew@Pass1!',
            'new_password_confirm': 'BrandNew@Pass1!',
        }
        mock_request = type('Req', (), {'user': admin_user})()
        serializer = ChangePasswordSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid() is True

    def test_change_password_wrong_old(self, admin_user):
        """اختبار كلمة المرور القديمة خاطئة."""
        from users.serializers import ChangePasswordSerializer
        admin_user.set_password('CorrectPass@1!')
        admin_user.save()
        data = {
            'old_password': 'WrongPass@1!',
            'new_password': 'NewPass@1234!',
            'new_password_confirm': 'NewPass@1234!',
        }
        mock_request = type('Req', (), {'user': admin_user})()
        serializer = ChangePasswordSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid() is False

    def test_change_password_same_as_old(self, admin_user):
        """اختبار كلمة المرور الجديدة نفس القديمة."""
        from users.serializers import ChangePasswordSerializer
        admin_user.set_password('SamePass@1234!')
        admin_user.save()
        admin_user.record_password_change('SamePass@1234!')

        data = {
            'old_password': 'SamePass@1234!',
            'new_password': 'SamePass@1234!',
            'new_password_confirm': 'SamePass@1234!',
        }
        mock_request = type('Req', (), {'user': admin_user})()
        serializer = ChangePasswordSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid() is False


class TestProductSerializers:
    """اختبارات مسلسلات المنتج."""

    def test_product_create_serializer_valid(self, db):
        """اختبار مسلسل إنشاء منتج ببيانات صالحة."""
        from inventory.serializers import ProductCreateSerializer
        data = {
            'name': 'منتج جديد',
            'sku': 'NEW-001',
            'quantity': 50,
            'unit_price': 100.00,
            'reorder_level': 5,
        }
        serializer = ProductCreateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_product_create_serializer_duplicate_sku(self, product, db):
        """اختبار مسلسل إنشاء منتج برمز SKU مكرر."""
        from inventory.serializers import ProductCreateSerializer
        data = {
            'name': 'منتج مكرر',
            'sku': 'TEST-001',
            'quantity': 10,
            'unit_price': 50.00,
        }
        serializer = ProductCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'sku' in serializer.errors

    def test_product_create_negative_price(self, db):
        """اختبار مسلسل إنشاء منتج بسعر سالب."""
        from inventory.serializers import ProductCreateSerializer
        data = {
            'name': 'منتج مجاني',
            'sku': 'FREE-001',
            'quantity': 10,
            'unit_price': -10.00,
        }
        serializer = ProductCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'unit_price' in serializer.errors

    def test_product_create_negative_quantity(self, db):
        """اختبار مسلسل إنشاء منتج بكمية سالبة."""
        from inventory.serializers import ProductCreateSerializer
        data = {
            'name': 'منتج سالب',
            'sku': 'NEG-001',
            'quantity': -5,
            'unit_price': 50.00,
        }
        serializer = ProductCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'quantity' in serializer.errors

    def test_product_update_serializer_valid(self, product):
        """اختبار مسلسل تحديث منتج."""
        from inventory.serializers import ProductUpdateSerializer
        data = {
            'name': 'منتج محدث',
            'price': 75.00,  # Wrong field - should use unit_price
        }
        serializer = ProductUpdateSerializer(product, data={'name': 'منتج محدث', 'unit_price': 75.00}, partial=True)
        assert serializer.is_valid() is True

    def test_product_list_serializer_output(self, product):
        """اختبار إخراج مسلسل قائمة المنتجات."""
        from inventory.serializers import ProductListSerializer
        serializer = ProductListSerializer(product)
        data = serializer.data
        assert data['name'] == product.name
        assert data['sku'] == product.sku
        assert 'is_low_stock' in data
        assert 'total_value' in data


class TestPermissionSerializers:
    """اختبارات مسلسلات الصلاحيات."""

    def test_permission_serializer(self, permission_obj):
        """اختبار مسلسل الصلاحية."""
        from users.serializers import PermissionSerializer
        serializer = PermissionSerializer(permission_obj)
        data = serializer.data
        assert data['code'] == 'inventory_view'
        assert 'module_display' in data
        assert 'action_display' in data

    def test_role_permission_update_serializer(self, permission_obj):
        """اختبار مسلسل تحديث صلاحيات الأدوار."""
        from users.serializers import RolePermissionUpdateSerializer
        data = {
            'role': 'sales',
            'permission_ids': [permission_obj.id],
        }
        serializer = RolePermissionUpdateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_role_permission_update_invalid_ids(self, db):
        """اختبار صلاحيات غير موجودة."""
        from users.serializers import RolePermissionUpdateSerializer
        data = {
            'role': 'sales',
            'permission_ids': [99999],
        }
        serializer = RolePermissionUpdateSerializer(data=data)
        assert serializer.is_valid() is False

    def test_password_policy_serializer_valid(self):
        """اختبار مسلسل سياسة كلمة المرور ببيانات صالحة."""
        from users.serializers import PasswordPolicySerializer
        data = {
            'min_length': 10,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
            'password_expiry_days': 90,
            'password_history_count': 5,
        }
        serializer = PasswordPolicySerializer(data=data)
        assert serializer.is_valid() is True

    def test_password_policy_serializer_invalid_min_length(self):
        """اختبار مسلسل سياسة كلمة المرور بحد أدنى صغير."""
        from users.serializers import PasswordPolicySerializer
        data = {
            'min_length': 3,  # Too short
            'password_expiry_days': 90,
        }
        serializer = PasswordPolicySerializer(data=data)
        assert serializer.is_valid() is False
