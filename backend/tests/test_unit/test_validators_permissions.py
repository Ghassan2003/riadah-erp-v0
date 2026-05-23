"""
اختبارات الوحدات البرمجية لمُحقّقات كلمة المرور والأذونات.
Unit Tests for Password Validators and Permission Classes.
"""

import pytest
from django.core.exceptions import ValidationError


class TestMinLengthValidator:
    """اختبارات مُحقّق الحد الأدنى لطول كلمة المرور."""

    def test_valid_length(self):
        """اختبار طول صالح."""
        from core.validators import MinLengthValidator
        v = MinLengthValidator(8)
        v.validate('LongPass@1')  # Should not raise

    def test_invalid_length(self):
        """اختبار طول غير كافٍ."""
        from core.validators import MinLengthValidator
        v = MinLengthValidator(8)
        with pytest.raises(ValidationError):
            v.validate('Short1!')

    def test_custom_min_length(self):
        """اختبار حد أدنى مخصص."""
        from core.validators import MinLengthValidator
        v = MinLengthValidator(12)
        with pytest.raises(ValidationError):
            v.validate('MediumPass1')

    def test_exact_length(self):
        """اختبار الطول المطلوب بالضبط."""
        from core.validators import MinLengthValidator
        v = MinLengthValidator(8)
        v.validate('Exact8@!')  # Exactly 8 chars


class TestComplexityValidator:
    """اختبارات مُحقّق تعقيد كلمة المرور."""

    def test_valid_complexity(self):
        """اختبار كلمة مرور معقدة صالحة."""
        from core.validators import ComplexityValidator
        v = ComplexityValidator()
        v.validate('Complex@Pass123')  # Should not raise

    def test_missing_uppercase(self):
        """اختبار عدم وجود حرف كبير."""
        from core.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('lowerpass@123')

    def test_missing_lowercase(self):
        """اختبار عدم وجود حرف صغير."""
        from core.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('UPPERPASS@123')

    def test_missing_digit(self):
        """اختبار عدم وجود رقم."""
        from core.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('NoDigitPass@')

    def test_missing_special(self):
        """اختبار عدم وجود رمز خاص."""
        from core.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('NoSpecialPass123')


class TestSequentialCharsValidator:
    """اختبارات مُحقّق الأحرف المتتالية والمكررة."""

    def test_valid_password(self):
        """اختبار كلمة مرور بدون تكرار أو تسلسل."""
        from core.validators import SequentialCharsValidator
        v = SequentialCharsValidator()
        v.validate('V@l1dP@ssW0rd')  # Should not raise

    def test_sequential_numbers(self):
        """اختبار كشف أرقام متتالية."""
        from core.validators import SequentialCharsValidator
        v = SequentialCharsValidator()
        with pytest.raises(ValidationError):
            v.validate('Pass123word!')

    def test_sequential_letters(self):
        """اختبار كشف أحرف متتالية."""
        from core.validators import SequentialCharsValidator
        v = SequentialCharsValidator()
        with pytest.raises(ValidationError):
            v.validate('Passabcword!')

    def test_repeating_chars(self):
        """اختبار كشف أحرف مكررة."""
        from core.validators import SequentialCharsValidator
        v = SequentialCharsValidator()
        with pytest.raises(ValidationError):
            v.validate('Passs111word!')

    def test_reverse_sequential(self):
        """اختبار كشف تسلسل عكسي (لا يُكشف - المُحقّق يكشف التسلسل الأمامي فقط)."""
        from core.validators import SequentialCharsValidator
        v = SequentialCharsValidator()
        # Reverse sequences (321, cba) are NOT detected by this validator
        v.validate('Pass321word!')  # Should NOT raise
        # Only forward sequences are detected
        with pytest.raises(ValidationError):
            v.validate('Pass123word!')


class TestUsernameSimilarityArabicValidator:
    """اختبارات مُحقّق تشابه اسم المستخدم."""

    def test_different_password(self):
        """اختبار كلمة مرور مختلفة عن اسم المستخدم."""
        from core.validators import UsernameSimilarityArabicValidator
        from users.models import User
        v = UsernameSimilarityArabicValidator()
        user = User(username='testuser')
        v.validate('TotallyDifferent@123', user)  # Should not raise

    def test_same_as_username(self):
        """اختبار كلمة المرور نفس اسم المستخدم."""
        from core.validators import UsernameSimilarityArabicValidator
        from users.models import User
        v = UsernameSimilarityArabicValidator()
        user = User(username='testuser')
        with pytest.raises(ValidationError):
            v.validate('testuser', user)

    def test_contains_username(self):
        """اختبار كلمة المرور تحتوي على اسم المستخدم."""
        from core.validators import UsernameSimilarityArabicValidator
        from users.models import User
        v = UsernameSimilarityArabicValidator()
        user = User(username='admin')
        with pytest.raises(ValidationError):
            v.validate('Myadmin@Pass1', user)

    def test_short_username(self):
        """اختبار اسم مستخدم قصير (أقل من 3 أحرف)."""
        from core.validators import UsernameSimilarityArabicValidator
        from users.models import User
        v = UsernameSimilarityArabicValidator()
        user = User(username='ab')
        v.validate('abPass@123', user)  # Short username, should pass

    def test_no_user(self):
        """اختبار بدون مستخدم."""
        from core.validators import UsernameSimilarityArabicValidator
        v = UsernameSimilarityArabicValidator()
        v.validate('Any@Password1')  # No user, should pass


class TestPasswordHistoryValidator:
    """اختبارات مُحقّق سجل كلمات المرور."""

    def test_password_in_history(self, admin_user):
        """اختبار كلمة مرور مستخدمة سابقاً."""
        from core.validators import PasswordHistoryValidator
        v = PasswordHistoryValidator(5)
        admin_user.record_password_change('OldPass@1234')
        admin_user.record_password_change('NewPass@1234')
        with pytest.raises(ValidationError):
            v.validate('OldPass@1234', admin_user)

    def test_password_not_in_history(self, admin_user):
        """اختبار كلمة مرور جديدة غير مستخدمة."""
        from core.validators import PasswordHistoryValidator
        v = PasswordHistoryValidator(5)
        admin_user.record_password_change('OldPass@1234')
        v.validate('FreshPass@5678', admin_user)  # Should not raise

    def test_no_history(self, db):
        """اختبار بدون سجل كلمات مرور."""
        from core.validators import PasswordHistoryValidator
        from users.models import User
        v = PasswordHistoryValidator(5)
        user = User.objects.create_user(username='nohist', password='Pass@1234!', role='sales')
        v.validate('AnyPass@1234', user)  # No history, should pass


class TestPermissionClasses:
    """اختبارات فئات الأذونات."""

    def _make_request(self, user):
        """إنشاء طلب وهمي مع مستخدم."""
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        return request

    def test_is_admin_grants_admin(self, admin_user):
        """اختبار أن المدير يملك صلاحية IsAdmin."""
        from users.permissions import IsAdmin
        perm = IsAdmin()
        request = self._make_request(admin_user)
        assert perm.has_permission(request, None) is True

    def test_is_admin_denies_non_admin(self, sales_user):
        """اختبار أن غير المدير لا يملك صلاحية IsAdmin."""
        from users.permissions import IsAdmin
        perm = IsAdmin()
        request = self._make_request(sales_user)
        assert perm.has_permission(request, None) is False

    def test_is_warehouse_or_admin(self, admin_user, warehouse_user, sales_user):
        """اختبار صلاحية المخازن أو المدير."""
        from users.permissions import IsWarehouseOrAdmin
        perm = IsWarehouseOrAdmin()
        assert perm.has_permission(self._make_request(admin_user), None) is True
        assert perm.has_permission(self._make_request(warehouse_user), None) is True
        assert perm.has_permission(self._make_request(sales_user), None) is False

    def test_is_sales_or_admin(self, admin_user, sales_user, accountant_user):
        """اختبار صلاحية المبيعات أو المدير."""
        from users.permissions import IsSalesOrAdmin
        perm = IsSalesOrAdmin()
        assert perm.has_permission(self._make_request(admin_user), None) is True
        assert perm.has_permission(self._make_request(sales_user), None) is True
        assert perm.has_permission(self._make_request(accountant_user), None) is False

    def test_is_accountant_or_admin(self, admin_user, accountant_user, hr_user):
        """اختبار صلاحية المحاسبة أو المدير."""
        from users.permissions import IsAccountantOrAdmin
        perm = IsAccountantOrAdmin()
        assert perm.has_permission(self._make_request(admin_user), None) is True
        assert perm.has_permission(self._make_request(accountant_user), None) is True
        assert perm.has_permission(self._make_request(hr_user), None) is False

    def test_is_owner_or_admin(self, admin_user, sales_user):
        """اختبار صلاحية المالك أو المدير على مستوى الكائن."""
        from users.permissions import IsOwnerOrAdmin
        perm = IsOwnerOrAdmin()
        # Admin can access any object
        assert perm.has_object_permission(self._make_request(admin_user), None, sales_user) is True
        # User can access own object
        assert perm.has_object_permission(self._make_request(sales_user), None, sales_user) is True
        # User cannot access other's object
        assert perm.has_object_permission(self._make_request(sales_user), None, admin_user) is False

    def test_is_hr_or_admin(self, admin_user, hr_user, sales_user):
        """اختبار صلاحية الموارد البشرية أو المدير."""
        from users.permissions import IsHROrAdmin
        perm = IsHROrAdmin()
        assert perm.has_permission(self._make_request(admin_user), None) is True
        assert perm.has_permission(self._make_request(hr_user), None) is True
        assert perm.has_permission(self._make_request(sales_user), None) is False

    def test_is_purchasing_or_admin(self, admin_user, warehouse_user, sales_user):
        """اختبار صلاحية المشتريات أو المدير."""
        from users.permissions import IsPurchasingOrAdmin
        perm = IsPurchasingOrAdmin()
        assert perm.has_permission(self._make_request(admin_user), None) is True
        assert perm.has_permission(self._make_request(warehouse_user), None) is True
        assert perm.has_permission(self._make_request(sales_user), None) is False

    def test_unauthenticated_denied(self):
        """اختبار أن المستخدم غير المصادق يُرفض."""
        from users.permissions import IsAdmin
        from django.contrib.auth.models import AnonymousUser
        perm = IsAdmin()
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        assert perm.has_permission(request, None) is False


class TestPermissionHelperFunctions:
    """اختبارات دوال مساعدة للأذونات."""

    def test_user_has_permission_admin(self, admin_user, seed_permissions):
        """اختبار أن المدير يملك جميع الصلاحيات."""
        from users.permissions import user_has_permission
        assert user_has_permission(admin_user, 'inventory_view') is True
        assert user_has_permission(admin_user, 'hr_create') is True
        assert user_has_permission(admin_user, 'nonexistent_perm') is True  # Admin gets True

    def test_user_has_permission_non_admin(self, sales_user, seed_permissions):
        """اختبار صلاحيات المستخدم غير المدير."""
        from users.permissions import user_has_permission
        assert user_has_permission(sales_user, 'nonexistent_perm') is False

    def test_get_user_permissions_admin(self, admin_user, seed_permissions):
        """اختبار جلب صلاحيات المدير."""
        from users.permissions import get_user_permissions
        perms = get_user_permissions(admin_user)
        assert len(perms) > 0
        assert 'inventory_view' in perms

    def test_get_user_permissions_non_admin(self, sales_user, seed_permissions):
        """اختبار جلب صلاحيات المستخدم العادي بدون تعيين."""
        from users.permissions import get_user_permissions
        perms = get_user_permissions(sales_user)
        assert len(perms) == 0

    def test_has_module_permission(self, admin_user, seed_permissions):
        """اختبار صلاحية وحدة محددة."""
        from users.permissions import user_has_module_permission
        assert user_has_module_permission(admin_user, 'inventory', 'view') is True
        assert user_has_module_permission(admin_user, 'hr', 'delete') is True
