"""
Permission decorators and mixins for granular access control.
يوفر أدوات للتحقق من الصلاحيات المفصّلة على مستوى API.
"""

from functools import wraps
from rest_framework import status
from rest_framework.response import Response

from users.permissions import user_has_module_permission


# ===== وحدة (module) للعرض في رسائل الخطأ =====
_MODULE_LABELS = {
    'inventory': 'إدارة المخزون',
    'sales': 'المبيعات',
    'purchases': 'المشتريات',
    'accounting': 'المحاسبة',
    'hr': 'الموارد البشرية',
    'documents': 'المستندات',
    'projects': 'المشاريع',
    'pos': 'نقاط البيع',
    'warehouse': 'المستودعات',
    'assets': 'الأصول الثابتة',
    'contracts': 'العقود',
    'payments': 'المدفوعات',
    'payroll': 'الرواتب والأجور',
    'invoicing': 'الفواتير',
    'dashboard': 'لوحة التحكم',
    'users': 'إدارة المستخدمين',
    'permissions': 'إدارة الصلاحيات',
    'reports': 'التقارير',
    'backup': 'النسخ الاحتياطي',
    'notifications': 'الإشعارات',
    'auditlog': 'سجل التدقيق',
}

# ===== إجراء (action) للعرض في رسائل الخطأ =====
_ACTION_LABELS = {
    'view': 'عرض',
    'create': 'إنشاء',
    'edit': 'تعديل',
    'delete': 'حذف',
    'export': 'تصدير',
    'approve': 'اعتماد',
    'manage': 'إدارة كاملة',
}


def _get_module_label(module):
    """إرجاع التسمية العربية للوحدة."""
    return _MODULE_LABELS.get(module, module)


def _get_action_label(action):
    """إرجاع التسمية العربية للإجراء."""
    return _ACTION_LABELS.get(action, action)


def _build_denied_message(module, action):
    """بناء رسالة خطأ واضحة بالعربية عند رفض الصلاحية."""
    module_label = _get_module_label(module)
    action_label = _get_action_label(action)
    return (
        f'ليس لديك صلاحية "{action_label}" على وحدة "{module_label}". '
        f'يرجى التواصل مع المسؤول لطلب الصلاحية اللازمة.'
    )


# ===== ديكوريتر للـ Function-Based Views =====

def require_permission(module, action):
    """
    Decorator for function-based API views that enforces granular permissions.
    الديكوريتر يتحقق من أن المستخدم يمتلك صلاحية module_action قبل تنفيذ الدالة.

    Usage:
        @require_permission('inventory', 'create')
        def my_view(request):
            ...

    Admin users bypass all permission checks.
    Returns 403 with Arabic error message if permission denied.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)

            if not user or not user.is_authenticated:
                return Response(
                    {'error': 'يجب تسجيل الدخول للوصول إلى هذا المورد.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not user_has_module_permission(user, module, action):
                return Response(
                    {'error': _build_denied_message(module, action)},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


# ===== Mixin للـ Class-Based Views =====

class PermissionRequiredMixin:
    """
    Mixin for DRF class-based views that enforces granular permissions.
    ماكسين للتحقق من الصلاحيات المفصّلة في الـ views الكلاسيكية.

    Usage - Single action for all HTTP methods:
        class MyListView(PermissionRequiredMixin, generics.ListAPIView):
            permission_module = 'inventory'
            permission_action = 'view'

    Usage - Different action per HTTP method:
        class MyView(PermissionRequiredMixin, generics.ListCreateAPIView):
            permission_module = 'inventory'
            permission_action = {
                'get': 'view',
                'post': 'create',
            }

    The mixin:
    - Runs AFTER standard DRF permission_classes (IsAuthenticated, etc.)
    - Admin users bypass the granular check
    - Returns 403 with a clear Arabic error message if denied
    - Works alongside existing get_permissions() overrides
    """

    permission_module = None
    permission_action = None

    def get_permission_module(self):
        """Return the module name for the permission check."""
        if self.permission_module is None:
            raise NotImplementedError(
                'PermissionRequiredMixin requires `permission_module` to be set. '
                'Example: permission_module = "inventory"'
            )
        return self.permission_module

    def _resolve_action(self, request):
        """
        Resolve the permission action based on the HTTP method.
        Supports both string and dict {method: action} formats.
        """
        action = self.permission_action
        if action is None:
            return None
        if isinstance(action, dict):
            return action.get(request.method.lower())
        return action

    def check_permissions(self, request):
        """
        Override DRF's check_permissions to add granular permission check.

        This first runs all standard DRF permission classes (IsAuthenticated,
        IsAdminUser, etc.) via super(), then additionally checks the
        module_action permission using the existing user_has_module_permission
        infrastructure with caching and admin bypass.
        """
        # Run standard DRF permission checks first
        super().check_permissions(request)

        # Resolve and check granular permission
        module = self.get_permission_module()
        action = self._resolve_action(request)

        if action is None:
            return

        if not user_has_module_permission(request.user, module, action):
            self.permission_denied(
                request,
                message=_build_denied_message(module, action),
            )
