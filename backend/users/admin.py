"""
Admin configuration for custom User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Permission, RolePermission, SystemSetting


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin interface for the User model."""

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'is_active', 'two_factor_enabled', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'two_factor_enabled')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)

    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {
            'fields': ('role', 'phone', 'last_login_ip', 'must_change_password')
        }),
        ('المصادقة الثنائية', {
            'fields': ('two_factor_enabled', 'totp_secret', 'two_factor_backup_codes')
        }),
        ('سياسة كلمة المرور', {
            'fields': ('password_changed_at', 'password_history')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات إضافية', {
            'fields': ('role', 'phone')
        }),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin interface for Permission model."""

    list_display = ('code', 'module', 'action', 'description')
    list_filter = ('module', 'action')
    search_fields = ('code', 'description', 'module')
    ordering = ('module', 'action')
    list_per_page = 50

    fieldsets = (
        ('معلومات الصلاحية', {
            'fields': ('module', 'action', 'code', 'description')
        }),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin interface for RolePermission model."""

    list_display = ('role', 'permission', 'created_at')
    list_filter = ('role',)
    search_fields = ('role', 'permission__code', 'permission__description')
    ordering = ('role', 'permission__module', 'permission__action')
    list_per_page = 50

    raw_id_fields = ('permission',)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """Admin interface for SystemSetting model."""

    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'value', 'description')
    ordering = ('key',)
    list_per_page = 50

    fieldsets = (
        ('إعداد النظام', {
            'fields': ('key', 'value', 'description')
        }),
    )
