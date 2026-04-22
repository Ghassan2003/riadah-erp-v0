"""
URL patterns for the users app.
Includes: Auth, 2FA, Permissions, Password Policy.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    TwoFactorLoginView,
    RegisterView,
    UserProfileView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    UserAdminUpdateView,
    UserDeactivateView,
    UserExportView,
    UserCreateByAdminView,
    # 2FA
    TwoFactorSetupView,
    TwoFactorVerifyView,
    TwoFactorStatusView,
    TwoFactorDisableView,
    AdminResetTwoFactorView,
    AdminForceChangePasswordView,
    # Permissions
    PermissionListView,
    AllRolePermissionsView,
    RolePermissionListView,
    UpdateRolePermissionsView,
    CheckPermissionView,
    UserPermissionsView,
    SeedPermissionsView,
    # Password Policy
    PasswordPolicyView,
    PasswordPolicyInfoView,
    # Forgot / Reset Password
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('login/2fa/', TwoFactorLoginView.as_view(), name='login-2fa'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Forgot / Reset Password
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # Admin user management
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/create/', UserCreateByAdminView.as_view(), name='user-create-admin'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/update/', UserAdminUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/toggle-active/', UserDeactivateView.as_view(), name='user-toggle-active'),
    path('users/<int:pk>/reset-2fa/', AdminResetTwoFactorView.as_view(), name='user-reset-2fa'),
    path('users/<int:pk>/force-change-password/', AdminForceChangePasswordView.as_view(), name='user-force-password-change'),

    # Export
    path('users/export/', UserExportView.as_view(), name='user-export'),

    # 2FA endpoints
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa-verify'),
    path('2fa/status/', TwoFactorStatusView.as_view(), name='2fa-status'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa-disable'),

    # Permission management
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('permissions/roles/', AllRolePermissionsView.as_view(), name='all-role-permissions'),
    path('permissions/roles/<str:role>/', RolePermissionListView.as_view(), name='role-permissions'),
    path('permissions/roles/<str:role>/update/', UpdateRolePermissionsView.as_view(), name='update-role-permissions'),
    path('permissions/check/', CheckPermissionView.as_view(), name='check-permission'),
    path('permissions/my/', UserPermissionsView.as_view(), name='my-permissions'),
    path('permissions/seed/', SeedPermissionsView.as_view(), name='seed-permissions'),

    # Password Policy
    path('password-policy/', PasswordPolicyView.as_view(), name='password-policy'),
    path('password-policy/info/', PasswordPolicyInfoView.as_view(), name='password-policy-info'),
]
