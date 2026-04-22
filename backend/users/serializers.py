"""
Serializers for the User model.
Handles data validation and transformation for API requests/responses.
Includes: User CRUD, Password Policy, 2FA, Permissions.
"""

import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import User, Permission, RolePermission, SystemSetting

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'role',
        )

    def validate_password(self, value):
        """Validate password with custom validators."""
        from core.validators import (
            MinLengthValidator,
            ComplexityValidator,
            UsernameSimilarityArabicValidator,
            SequentialCharsValidator,
        )
        user = User(username=self.initial_data.get('username', ''))
        MinLengthValidator(8).validate(value, user)
        ComplexityValidator().validate(value, user)
        UsernameSimilarityArabicValidator().validate(value, user)
        SequentialCharsValidator().validate(value, user)
        # Also run Django's built-in validators
        validate_password(value, user)
        return value

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'كلمتا المرور غير متطابقتين'
            })
        return attrs

    def create(self, validated_data):
        """Create a new user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.record_password_change(password)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (password change excluded)."""

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'phone',
        )
        extra_kwargs = {
            'email': {'required': False},
        }

    def validate_email(self, value):
        """Ensure email uniqueness."""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('هذا البريد الإلكتروني مستخدم بالفعل')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password with enhanced policy."""

    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_new_password(self, value):
        """Validate new password with all custom validators."""
        from core.validators import (
            MinLengthValidator,
            ComplexityValidator,
            PasswordHistoryValidator,
            UsernameSimilarityArabicValidator,
            SequentialCharsValidator,
        )
        user = self.context['request'].user
        MinLengthValidator(8).validate(value, user)
        ComplexityValidator().validate(value, user)
        PasswordHistoryValidator(5).validate(value, user)
        UsernameSimilarityArabicValidator().validate(value, user)
        SequentialCharsValidator().validate(value, user)
        validate_password(value, user)
        return value

    def validate_old_password(self, value):
        """Verify the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('كلمة المرور الحالية غير صحيحة')
        return value

    def validate(self, attrs):
        """Validate that new passwords match and are different from old."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'كلمتا المرور الجديدتين غير متطابقتين'
            })
        if attrs['new_password'] == attrs['old_password']:
            raise serializers.ValidationError({
                'new_password': 'كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية'
            })
        return attrs

    def save(self):
        """Save the new password with policy tracking."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        user.record_password_change(self.validated_data['new_password'])


class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying user information."""

    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True,
    )
    two_factor_enabled = serializers.BooleanField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    days_until_password_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'role_display',
            'is_active', 'created_at', 'updated_at',
            'two_factor_enabled', 'must_change_password',
            'days_until_password_expiry',
        )
        read_only_fields = ('id', 'username', 'role', 'is_active', 'created_at', 'updated_at')


class UserAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin user management (full details)."""

    role_display = serializers.CharField(source='get_role_display', read_only=True)
    two_factor_enabled = serializers.BooleanField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    days_until_password_expiry = serializers.IntegerField(read_only=True)
    last_login_ip = serializers.CharField(read_only=True)
    password_changed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'role_display',
            'is_active', 'created_at', 'updated_at',
            'two_factor_enabled', 'must_change_password',
            'days_until_password_expiry', 'last_login_ip',
            'password_changed_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'password_changed_at', 'last_login_ip')


class UserCreateByAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin creating users with password policy."""

    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'role', 'must_change_password',
        )

    def validate_password(self, value):
        from core.validators import (
            MinLengthValidator, ComplexityValidator,
            UsernameSimilarityArabicValidator, SequentialCharsValidator,
        )
        user = User(username=self.initial_data.get('username', ''))
        MinLengthValidator(8).validate(value, user)
        ComplexityValidator().validate(value, user)
        UsernameSimilarityArabicValidator().validate(value, user)
        SequentialCharsValidator().validate(value, user)
        validate_password(value, user)
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'كلمتا المرور غير متطابقتين'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        must_change = validated_data.pop('must_change_password', True)
        user = User(**validated_data)
        user.set_password(password)
        user.must_change_password = must_change
        user.save()
        user.record_password_change(password)
        return user


# ===== 2FA Serializers =====

class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for initiating 2FA setup."""

    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('كلمة المرور غير صحيحة')
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying and enabling 2FA."""

    code = serializers.CharField(
        max_length=6,
        min_length=6,
        write_only=True,
    )

    def validate_code(self, value):
        user = self.context['request'].user
        if not user.verify_totp(value) and not user.verify_backup_code(value):
            raise serializers.ValidationError('رمز التحقق غير صحيح')
        return value


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA."""

    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        write_only=True,
        required=False,
    )

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('كلمة المرور غير صحيحة')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if user.two_factor_enabled:
            code = attrs.get('code')
            if code and not user.verify_totp(code):
                raise serializers.ValidationError({'code': 'رمز التحقق غير صحيح'})
        return attrs


class TwoFactorLoginSerializer(serializers.Serializer):
    """Serializer for 2FA verification during login."""

    code = serializers.CharField(
        max_length=6,
        min_length=6,
        write_only=True,
    )


# ===== Permission Serializers =====

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for permission objects."""

    module_display = serializers.CharField(source='get_module_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = Permission
        fields = ('id', 'module', 'module_display', 'action', 'action_display',
                  'code', 'description')


class RolePermissionSerializer(serializers.ModelSerializer):
    """Serializer for role-permission mappings."""

    permission_detail = PermissionSerializer(source='permission', read_only=True)

    class Meta:
        model = RolePermission
        fields = ('id', 'role', 'permission', 'permission_detail', 'created_at')
        read_only_fields = ('id', 'created_at')


class RolePermissionUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating role permissions."""

    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
    )

    def validate_permission_ids(self, value):
        existing = Permission.objects.filter(id__in=value).count()
        if existing != len(value):
            raise serializers.ValidationError('بعض الصلاحيات غير موجودة')
        return value


class PermissionCheckSerializer(serializers.Serializer):
    """Serializer for checking if user has a specific permission."""

    code = serializers.CharField(max_length=60)


class SystemSettingSerializer(serializers.ModelSerializer):
    """Serializer for system settings."""

    class Meta:
        model = SystemSetting
        fields = ('id', 'key', 'value', 'description', 'updated_at')


# ===== Forgot / Reset Password Serializers =====

class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting a password reset code."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('لا يوجد حساب مرتبط بهذا البريد الإلكتروني')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for verifying reset code and setting new password."""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('لا يوجد حساب مرتبط بهذا البريد الإلكتروني')
        return value

    def validate_new_password(self, value):
        from core.validators import (
            MinLengthValidator,
            ComplexityValidator,
            UsernameSimilarityArabicValidator,
            SequentialCharsValidator,
        )
        user = User(username=self.initial_data.get('email', '').split('@')[0])
        MinLengthValidator(8).validate(value, user)
        ComplexityValidator().validate(value, user)
        UsernameSimilarityArabicValidator().validate(value, user)
        SequentialCharsValidator().validate(value, user)
        validate_password(value, user)
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'كلمتا المرور غير متطابقتين'
            })
        return attrs


class PasswordPolicySerializer(serializers.Serializer):
    """Serializer for getting/setting password policy."""

    min_length = serializers.IntegerField(default=8, min_value=6, max_value=128)
    require_uppercase = serializers.BooleanField(default=True)
    require_lowercase = serializers.BooleanField(default=True)
    require_digit = serializers.BooleanField(default=True)
    require_special = serializers.BooleanField(default=True)
    password_expiry_days = serializers.IntegerField(default=90, min_value=0, max_value=365)
    password_history_count = serializers.IntegerField(default=5, min_value=0, max_value=20)
