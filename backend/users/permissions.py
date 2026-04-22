"""
Custom permissions for role-based and granular access control.
يشمل نظام صلاحيات مفصّل مع تخزين مؤقت للتحقق من الأذونات.
"""

from django.core.cache import cache
from rest_framework.permissions import BasePermission
from .models import Permission, RolePermission


# ===== دوال مساعدة للتخزين المؤقت =====

def _get_permission_cache_key(user_id, permission_code):
    """إنشاء مفتاح التخزين المؤقت للتحقق من صلاحية محددة."""
    return f'user_perms_{user_id}_{permission_code}'


def _get_role_perms_cache_key(role):
    """إنشاء مفتاح التخزين المؤقت لجميع صلاحيات دور معيّن."""
    return f'role_perms_{role}'


def invalidate_user_permission_cache(user):
    """مسح جميع صلاحيات المستخدم من التخزين المؤقت عند تغيير الصلاحيات."""
    if not user or not hasattr(user, 'id'):
        return
    try:
        # مسح جميع مفاتيح المستخدم من التخزين المؤقت
        cache.delete_pattern(f'user_perms_{user.id}_*')
    except AttributeError:
        # في حال لم يدعم التخزين المؤقت delete_pattern (مثل بعض أنواع الـ cache)
        # نقوم بمسح جميع صلاحيات الدور بدلاً من ذلك
        if hasattr(user, 'role'):
            cache.delete(_get_role_perms_cache_key(user.role))


def invalidate_role_permission_cache(role):
    """مسح جميع صلاحيات دور معيّن من التخزين المؤقت."""
    if not role:
        return
    cache.delete(_get_role_perms_cache_key(role))
    # مسح جميع المستخدمين الذين ينتمون لهذا الدور
    from .models import User
    for user in User.objects.filter(role=role, is_active=True).iterator():
        try:
            cache.delete_pattern(f'user_perms_{user.id}_*')
        except AttributeError:
            pass


class IsAdmin(BasePermission):
    """Only admin users can access."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsWarehouseOrAdmin(BasePermission):
    """Only warehouse staff or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'warehouse')


class IsSalesOrAdmin(BasePermission):
    """Only sales staff or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'sales')


class IsAccountantOrAdmin(BasePermission):
    """Only accountant or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'accountant')


class IsOwnerOrAdmin(BasePermission):
    """Users can only modify their own profile, unless they are admin."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'admin' or request.user == obj


class IsHROrAdmin(BasePermission):
    """Only HR staff or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'hr')


class IsPurchasingOrAdmin(BasePermission):
    """Only purchasing staff, warehouse, or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'purchasing', 'warehouse')


class IsProjectManagerOrAdmin(BasePermission):
    """Only project managers or admin can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('admin', 'project_manager')


class IsOwnerOrAdminOrManager(BasePermission):
    """Object-level: owner, admin, or assigned manager can access."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'admin':
            return True
        if hasattr(obj, 'manager') and obj.manager == request.user:
            return True
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        return False


class HasModulePermission(BasePermission):
    """
    Granular permission checker.
    Checks if the user's role has a specific module/action permission.
    Admin users always have all permissions.
    """

    def __init__(self, module, action):
        self.module = module
        self.action = action
        self.permission_code = f'{module}_{action}'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # المدير لديه جميع الصلاحيات دائماً
        if request.user.role == 'admin':
            return True
        # التحقق من التخزين المؤقت أولاً
        cache_key = _get_permission_cache_key(request.user.id, self.permission_code)
        result = cache.get(cache_key)
        if result is not None:
            return result
        # التحقق من قاعدة البيانات
        result = RolePermission.objects.filter(
            role=request.user.role,
            permission__code=self.permission_code,
        ).exists()
        # تخزين النتيجة في الكاش لمدة 5 دقائق
        cache.set(cache_key, result, timeout=300)
        return result


def user_has_permission(user, permission_code):
    """التحقق مما إذا كان المستخدم يمتلك صلاحية محددة (مع التخزين المؤقت)."""
    if not user or not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    # التحقق من التخزين المؤقت أولاً
    cache_key = _get_permission_cache_key(user.id, permission_code)
    result = cache.get(cache_key)
    if result is not None:
        return result
    # التحقق من قاعدة البيانات
    result = RolePermission.objects.filter(
        role=user.role,
        permission__code=permission_code,
    ).exists()
    # تخزين النتيجة في الكاش لمدة 5 دقائق
    cache.set(cache_key, result, timeout=300)
    return result


def user_has_module_permission(user, module, action):
    """التحقق مما إذا كان المستخدم يمتلك صلاحية لوحدة/إجراء محدد."""
    return user_has_permission(user, f'{module}_{action}')


def get_user_permissions(user):
    """الحصول على جميع رموز الصلاحيات للمستخدم (مع التخزين المؤقت)."""
    if not user or not user.is_authenticated:
        return []
    if user.role == 'admin':
        # المدير لديه جميع الصلاحيات - نستخدم كاش خاص بالدور
        cache_key = f'all_perms_admin'
        result = cache.get(cache_key)
        if result is None:
            result = list(Permission.objects.values_list('code', flat=True))
            cache.set(cache_key, result, timeout=300)
        return result
    # التحقق من كاش الدور أولاً
    cache_key = _get_role_perms_cache_key(user.role)
    result = cache.get(cache_key)
    if result is not None:
        return result
    # التحقق من قاعدة البيانات
    result = list(
        RolePermission.objects.filter(role=user.role)
        .values_list('permission__code', flat=True)
    )
    # تخزين النتيجة في الكاش لمدة 5 دقائق
    cache.set(cache_key, result, timeout=300)
    return result
