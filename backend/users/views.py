"""
API views for user authentication and profile management.
Includes: Auth, 2FA, Permissions, Password Policy.
"""

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status, permissions, views, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Invitation, Permission, RolePermission, SystemSetting
from .serializers import (
    UserRegistrationSerializer,
    UserUpdateSerializer,
    UserSerializer,
    UserAdminSerializer,
    UserCreateByAdminSerializer,
    ChangePasswordSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    TwoFactorDisableSerializer,
    TwoFactorLoginSerializer,
    PermissionSerializer,
    RolePermissionSerializer,
    RolePermissionUpdateSerializer,
    PasswordPolicySerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    InvitationCreateSerializer,
    InvitationAcceptSerializer,
    InvitationListSerializer,
)
from .permissions import (
    IsOwnerOrAdmin,
    IsAdmin,
    user_has_permission,
    get_user_permissions,
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add user role and details to the JWT token response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        token['two_factor_enabled'] = user.two_factor_enabled
        return token

    def validate(self, attrs):
        # Check account lockout before attempting authentication
        try:
            from users.models import User
            username = attrs.get(self.username_field)
            user = User.objects.get(username=username)

            # Check if user is locked out
            if user.locked_until and timezone.now() < user.locked_until:
                from datetime import timedelta
                remaining_minutes = (user.locked_until - timezone.now()).total_seconds() / 60
                raise serializers.ValidationError({
                    'error': f'الحساب مقفل. حاول مرة أخرى بعد {int(remaining_minutes)} دقيقة'
                })

            # Clear lockout if it has expired
            if user.locked_until and timezone.now() >= user.locked_until:
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save(update_fields=['failed_login_attempts', 'locked_until'])
        except User.DoesNotExist:
            pass
        except serializers.ValidationError:
            raise

        try:
            data = super().validate(attrs)
        except Exception as e:
            # Increment failed login attempts on authentication failure
            try:
                from users.models import User
                username = attrs.get(self.username_field)
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                MAX_ATTEMPTS = 5
                LOCKOUT_MINUTES = 15
                if user.failed_login_attempts >= MAX_ATTEMPTS:
                    from datetime import timedelta
                    user.locked_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
                    user.save(update_fields=['failed_login_attempts', 'locked_until'])
                else:
                    user.save(update_fields=['failed_login_attempts'])
            except Exception:
                pass
            raise e

        # Reset failed attempts on successful login
        if hasattr(self, 'user') and self.user:
            self.user.failed_login_attempts = 0
            self.user.locked_until = None
            self.user.save(update_fields=['failed_login_attempts', 'locked_until'])

        # Check if 2FA is enabled for this user
        if self.user.two_factor_enabled:
            data['requires_2FA'] = True
            # Store the full token in cache for the 2FA verification step
            from django.core.cache import cache
            temp_token_id = f'2fa_{self.user.id}_{timezone.now().timestamp()}'
            cache.set(temp_token_id, {
                'user_id': self.user.id,
                'access': str(data['access']),
                'refresh': str(data['refresh']),
            }, timeout=120)  # 2 minutes to complete 2FA
            data['temp_token'] = temp_token_id
            # Don't return full tokens yet - need 2FA verification
            data.pop('access', None)
            data.pop('refresh', None)
        else:
            data['requires_2fa'] = False
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': self.user.role,
                'role_display': self.user.get_role_display(),
                'two_factor_enabled': self.user.two_factor_enabled,
                'must_change_password': self.user.must_change_password,
            }

            # Log login and update last login IP
            self._log_login()

        return data

    def _log_login(self):
        """Log successful login to audit log."""
        try:
            from auditlog.models import AuditLog
            request = self.context.get('request')
            AuditLog.log(
                user=self.user,
                action='login',
                model_name='User',
                object_id=self.user.id,
                object_repr=self.user.username,
                request=request,
            )
            # Update last login IP
            if request:
                ip = request.META.get('REMOTE_ADDR')
                User.objects.filter(pk=self.user.pk).update(last_login_ip=ip)
        except Exception:
            pass


class LoginView(TokenObtainPairView):
    """Custom login view that returns user info alongside tokens."""
    serializer_class = CustomTokenObtainPairSerializer


class TwoFactorLoginView(APIView):
    """Verify 2FA code after initial login and return full tokens."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TwoFactorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        temp_token = request.data.get('temp_token', '')

        # Verify temp_token from cache
        from django.core.cache import cache
        cached = cache.get(temp_token) if temp_token else None
        if not cached:
            return Response(
                {'error': 'رمز التحقق منتهي الصلاحية أو غير صالح. يرجى تسجيل الدخول مرة أخرى.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Find user from cache
        try:
            user = User.objects.get(pk=cached['user_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verify 2FA code
        if not user.verify_totp(code) and not user.verify_backup_code(code):
            return Response(
                {'error': 'رمز التحقق غير صحيح'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Use the cached tokens instead of generating new ones
        access_token = cached['access']
        refresh_token = cached['refresh']
        cache.delete(temp_token)

        # Log login
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=user,
                action='login',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                request=request,
            )
            User.objects.filter(pk=user.pk).update(last_login_ip=request.META.get('REMOTE_ADDR'))
        except Exception:
            pass

        return Response({
            'access': access_token,
            'refresh': refresh_token,
            'requires_2fa': False,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'role_display': user.get_role_display(),
                'two_factor_enabled': user.two_factor_enabled,
                'must_change_password': user.must_change_password,
            },
        })


class RegisterView(generics.CreateAPIView):
    """API endpoint for registering a new user. Only admin users can create new accounts."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Log user creation
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='create',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                new_values={'username': user.username, 'role': user.role, 'email': user.email},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم إنشاء المستخدم بنجاح',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for viewing and updating the authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        """Return user profile with permissions list."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Include user permissions
        if request.user.role == 'admin':
            data['permissions'] = list(Permission.objects.values_list('code', flat=True))
        else:
            data['permissions'] = list(
                RolePermission.objects.filter(role=request.user.role)
                .values_list('permission__code', flat=True)
            )

        return Response(data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='update',
                model_name='User',
                object_id=instance.id,
                object_repr=instance.username,
                new_values=request.data,
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم تحديث الملف الشخصي بنجاح',
            'user': UserSerializer(instance).data,
        })


class ChangePasswordView(APIView):
    """API endpoint for changing the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log password change
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='update',
                model_name='User',
                object_id=request.user.id,
                object_repr=request.user.username,
                changes={'field': 'password'},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم تغيير كلمة المرور بنجاح'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """API endpoint for listing all users (admin only)."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserAdminSerializer
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering_fields = ('username', 'role', 'created_at')


class UserDetailView(generics.RetrieveAPIView):
    """API endpoint for viewing a specific user's details."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserAdminSerializer


class UserAdminUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Admin can update user details (role, department, etc.)."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserAdminSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                new_values=request.data,
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم تحديث بيانات المستخدم بنجاح',
            'user': UserAdminSerializer(user).data,
        })


class UserDeactivateView(APIView):
    """API endpoint for toggling user active status (admin only)."""

    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='soft_delete' if not user.is_active else 'restore',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'is_active': user.is_active},
                request=request,
            )
        except Exception:
            pass

        if user.is_active:
            return Response({'message': 'تم تفعيل المستخدم بنجاح'})
        return Response({'message': 'تم تعطيل المستخدم بنجاح'})


class UserCreateByAdminView(generics.CreateAPIView):
    """Admin can create users with full control."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserCreateByAdminSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='create',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                new_values={'username': user.username, 'role': user.role},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم إنشاء المستخدم بنجاح',
            'user': UserAdminSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class UserExportView(APIView):
    """GET: Export users to Excel."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = User.objects.all()
        columns = [
            ('username', 'اسم المستخدم', 20),
            ('email', 'البريد الإلكتروني', 30),
            ('first_name', 'الاسم الأول', 20),
            ('last_name', 'اسم العائلة', 20),
            ('role', 'الدور', 15),
            ('phone', 'الهاتف', 15),
            ('is_active', 'نشط', 10),
            ('two_factor_enabled', 'المصادقة الثنائية', 15),
            ('must_change_password', 'يجب تغيير المرور', 15),
            ('last_login_ip', 'آخر IP', 15),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for user in queryset:
            data.append({
                'username': user.username,
                'email': user.email or '',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.get_role_display(),
                'phone': user.phone or '',
                'is_active': 'نعم' if user.is_active else 'لا',
                'two_factor_enabled': 'نعم' if user.two_factor_enabled else 'لا',
                'must_change_password': 'نعم' if user.must_change_password else 'لا',
                'last_login_ip': user.last_login_ip or '',
                'created_at': str(user.created_at.strftime('%Y-%m-%d %H:%M')) if user.created_at else '',
            })
        return export_to_excel(data, columns, 'المستخدمون', 'users.xlsx')


# ===== 2FA Views =====

class TwoFactorSetupView(APIView):
    """POST: Initiate 2FA setup - generates TOTP secret and backup codes."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        # Generate new TOTP secret
        secret = user.generate_totp_secret()
        # Generate backup codes
        backup_codes = user.generate_backup_codes(10)
        # Get provisioning URI
        uri = user.get_totp_uri(secret)

        return Response({
            'secret': secret,
            'uri': uri,
            'backup_codes': backup_codes,
            'message': 'امسح رمز QR أو أدخل المفتاح يدوياً في تطبيق المصادقة',
        })


class TwoFactorVerifyView(APIView):
    """POST: Verify TOTP code and enable 2FA."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled'])

        # Generate new backup codes on enable
        backup_codes = user.generate_backup_codes(10)

        # Log
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'field': 'two_factor_enabled', 'value': True},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم تفعيل المصادقة الثنائية بنجاح',
            'backup_codes': backup_codes,
        })


class TwoFactorStatusView(APIView):
    """GET: Check 2FA status for current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'enabled': request.user.two_factor_enabled,
        })


class TwoFactorDisableView(APIView):
    """POST: Disable 2FA for current user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.two_factor_enabled = False
        user.totp_secret = ''
        user.two_factor_backup_codes = []
        user.save(update_fields=['two_factor_enabled', 'totp_secret', 'two_factor_backup_codes'])

        # Log
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'field': 'two_factor_enabled', 'value': False},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم تعطيل المصادقة الثنائية بنجاح',
        })


class AdminResetTwoFactorView(APIView):
    """POST: Admin can reset 2FA for any user."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        user.two_factor_enabled = False
        user.totp_secret = ''
        user.two_factor_backup_codes = []
        user.save(update_fields=['two_factor_enabled', 'totp_secret', 'two_factor_backup_codes'])

        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'field': 'two_factor_enabled', 'value': False, 'admin_reset': True},
                request=request,
            )
        except Exception:
            pass

        return Response({'message': f'تم إعادة تعيين المصادقة الثنائية للمستخدم {user.username}'})


class AdminForceChangePasswordView(APIView):
    """POST: Admin can force user to change password on next login."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        user.must_change_password = True
        user.save(update_fields=['must_change_password'])

        return Response({'message': f'سيُطلب من المستخدم {user.username} تغيير كلمة المرور عند تسجيل الدخول'})


# ===== Forgot / Reset Password Views =====

class ForgotPasswordView(APIView):
    """POST: Request a password reset code via email."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower().strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Still return success to prevent email enumeration
            return Response({
                'message': 'إذا كان البريد الإلكتروني مسجلاً لدينا، سيتم إرسال رمز التحقق',
                'success': True,
            })

        # Generate 6-digit code
        import random
        code = str(random.randint(100000, 999999))

        # Store code in Django cache (15 minutes expiry)
        from django.core.cache import cache
        cache_key = f'pwd_reset_{email}'
        cache.set(cache_key, {'code': code, 'user_id': user.id}, timeout=900)

        # Attempt to send email (if SMTP is configured)
        email_sent = False
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject='RIADAH - رمز استعادة كلمة المرور',
                message=f'رمز استعادة كلمة المرور الخاص بك هو: {code}\n\nهذا الرمز صالح لمدة 15 دقيقة فقط.\nإذا لم تطلب هذا، تجاهل هذه الرسالة.',
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@riadah.com',
                recipient_list=[email],
                fail_silently=True,
            )
            email_sent = True
        except Exception:
            email_sent = False

        # Log the attempt
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'action': 'forgot_password_request', 'email_sent': email_sent},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'إذا كان البريد الإلكتروني مسجلاً لدينا، سيتم إرسال رمز التحقق',
            'success': True,
            # In development mode, return the code for testing
            '_dev_code': code if (not email_sent and settings.DEBUG) else None,
        })


class ResetPasswordView(APIView):
    """POST: Verify reset code and set new password."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower().strip()
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        # Verify code from cache
        from django.core.cache import cache
        cache_key = f'pwd_reset_{email}'
        cached_data = cache.get(cache_key)

        if not cached_data or cached_data['code'] != code:
            return Response(
                {'error': 'رمز التحقق غير صحيح أو منتهي الصلاحية'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get user and update password
        try:
            user = User.objects.get(pk=cached_data['user_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.set_password(new_password)
        user.must_change_password = False
        # record_password_change must be called BEFORE set_password
        # because set_password changes the password. However, since set_password
        # already hashes the password, we just need to record the timestamp.
        user.record_password_change()
        user.save()

        # Clear the reset code from cache
        cache.delete(cache_key)

        # Log the password reset
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=user,
                action='update',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                changes={'field': 'password', 'action': 'reset_via_code'},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة.',
            'success': True,
        })


# ===== Permission Management Views =====

class PermissionListView(generics.ListAPIView):
    """GET: List all available permissions (admin only)."""

    queryset = Permission.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = PermissionSerializer
    pagination_class = None


class RolePermissionListView(generics.ListAPIView):
    """GET: List permissions for a specific role."""

    permission_classes = [IsAdmin]
    serializer_class = RolePermissionSerializer
    pagination_class = None

    def get_queryset(self):
        role = self.kwargs.get('role')
        return RolePermission.objects.filter(role=role).select_related('permission')


class AllRolePermissionsView(APIView):
    """GET: Get all role-permission mappings grouped by role."""

    permission_classes = [IsAdmin]

    def get(self, request):
        # Get all permissions
        all_permissions = list(Permission.objects.all().order_by('module', 'action'))

        # Get all role-permission mappings
        rp_mappings = RolePermission.objects.all()
        role_perms = {}
        for rp in rp_mappings:
            if rp.role not in role_perms:
                role_perms[rp.role] = set()
            role_perms[rp.role].add(rp.permission_id)

        # Build response grouped by role
        roles = dict(User.ROLE_CHOICES)
        result = {}
        for role_code, role_name in roles.items():
            assigned_ids = role_perms.get(role_code, set())
            result[role_code] = {
                'name': role_name,
                'permissions': [p.id for p in all_permissions if p.id in assigned_ids],
            }

        return Response({
            'permissions': PermissionSerializer(all_permissions, many=True).data,
            'roles': result,
        })


class UpdateRolePermissionsView(APIView):
    """PUT: Update permissions for a specific role."""

    permission_classes = [IsAdmin]

    def put(self, request, role):
        serializer = RolePermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permission_ids = serializer.validated_data['permission_ids']

        # Delete existing role permissions
        RolePermission.objects.filter(role=role).delete()

        # Create new role permissions
        rp_objects = [
            RolePermission(role=role, permission_id=pid)
            for pid in permission_ids
        ]
        RolePermission.objects.bulk_create(rp_objects)

        # Log
        try:
            from auditlog.models import AuditLog
            AuditLog.log(
                user=request.user,
                action='update',
                model_name='RolePermission',
                object_repr=role,
                changes={'permissions_count': len(permission_ids)},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': f'تم تحديث صلاحيات دور {dict(User.ROLE_CHOICES).get(role, role)} بنجاح',
            'permissions_count': len(permission_ids),
        })


class CheckPermissionView(APIView):
    """POST: Check if current user has a specific permission."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '')
        has_perm = user_has_permission(request.user, code)
        return Response({'code': code, 'has_permission': has_perm})


class UserPermissionsView(APIView):
    """GET: Get current user's permissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        perms = get_user_permissions(request.user)
        return Response({
            'role': request.user.role,
            'permissions': perms,
        })


# ===== Password Policy Views =====

class PasswordPolicyView(APIView):
    """GET/PUT: View and update password policy settings."""

    permission_classes = [IsAdmin]

    def get(self, request):
        policy = {
            'min_length': int(SystemSetting.get('password_min_length', '8')),
            'require_uppercase': SystemSetting.get('password_require_uppercase', 'true') == 'true',
            'require_lowercase': SystemSetting.get('password_require_lowercase', 'true') == 'true',
            'require_digit': SystemSetting.get('password_require_digit', 'true') == 'true',
            'require_special': SystemSetting.get('password_require_special', 'true') == 'true',
            'password_expiry_days': int(SystemSetting.get('password_expiry_days', '90')),
            'password_history_count': int(SystemSetting.get('password_history_count', '5')),
        }
        return Response(policy)

    def put(self, request):
        serializer = PasswordPolicySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        SystemSetting.set('password_min_length', str(data['min_length']), 'الحد الأدنى لطول كلمة المرور')
        SystemSetting.set('password_require_uppercase', str(data['require_uppercase']).lower(), 'تطلب حرف كبير')
        SystemSetting.set('password_require_lowercase', str(data['require_lowercase']).lower(), 'تطلب حرف صغير')
        SystemSetting.set('password_require_digit', str(data['require_digit']).lower(), 'تطلب رقم')
        SystemSetting.set('password_require_special', str(data['require_special']).lower(), 'تطلب رمز خاص')
        SystemSetting.set('password_expiry_days', str(data['password_expiry_days']), 'مدة صلاحية كلمة المرور (أيام)')
        SystemSetting.set('password_history_count', str(data['password_history_count']), 'عدد كلمات المرور في السجل')

        return Response({
            'message': 'تم تحديث سياسة كلمة المرور بنجاح',
            'policy': data,
        })


class PasswordPolicyInfoView(APIView):
    """GET: Get password policy info (for all authenticated users)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        policy = {
            'min_length': int(SystemSetting.get('password_min_length', '8')),
            'require_uppercase': SystemSetting.get('password_require_uppercase', 'true') == 'true',
            'require_lowercase': SystemSetting.get('password_require_lowercase', 'true') == 'true',
            'require_digit': SystemSetting.get('password_require_digit', 'true') == 'true',
            'require_special': SystemSetting.get('password_require_special', 'true') == 'true',
            'password_expiry_days': int(SystemSetting.get('password_expiry_days', '90')),
            'password_history_count': int(SystemSetting.get('password_history_count', '5')),
        }
        return Response(policy)


class SeedPermissionsView(APIView):
    """POST: Seed all default permissions (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        """Create default permissions and assign to admin."""
        created_count = 0

        # Define default permissions
        default_perms = [
            ('dashboard', 'view'),
            ('sales', 'view'), ('sales', 'create'), ('sales', 'edit'), ('sales', 'delete'), ('sales', 'export'), ('sales', 'approve'),
            ('purchases', 'view'), ('purchases', 'create'), ('purchases', 'edit'), ('purchases', 'delete'), ('purchases', 'export'), ('purchases', 'approve'),
            ('accounting', 'view'), ('accounting', 'create'), ('accounting', 'edit'), ('accounting', 'delete'), ('accounting', 'export'), ('accounting', 'approve'),
            ('hr', 'view'), ('hr', 'create'), ('hr', 'edit'), ('hr', 'delete'), ('hr', 'export'), ('hr', 'approve'),
            ('documents', 'view'), ('documents', 'create'), ('documents', 'delete'),
            ('projects', 'view'), ('projects', 'create'), ('projects', 'edit'), ('projects', 'delete'), ('projects', 'export'),
            ('notifications', 'view'), ('notifications', 'manage'),
            ('auditlog', 'view'), ('auditlog', 'export'),
            ('users', 'view'), ('users', 'create'), ('users', 'edit'), ('users', 'delete'),
            ('reports', 'view'), ('reports', 'export'),
            ('backup', 'manage'),
            ('permissions', 'view'), ('permissions', 'manage'),
            # ===== الوحدات الجديدة =====
            # نقاط البيع
            ('pos', 'view'), ('pos', 'create'), ('pos', 'edit'), ('pos', 'delete'),
            # الفواتير
            ('invoicing', 'view'), ('invoicing', 'create'), ('invoicing', 'edit'), ('invoicing', 'delete'), ('invoicing', 'export'),
            # الرواتب والأجور
            ('payroll', 'view'), ('payroll', 'create'), ('payroll', 'edit'), ('payroll', 'export'),
            # المستودعات
            ('warehouse', 'view'), ('warehouse', 'create'), ('warehouse', 'edit'), ('warehouse', 'delete'), ('warehouse', 'export'),
            # المدفوعات
            ('payments', 'view'), ('payments', 'create'), ('payments', 'edit'), ('payments', 'delete'),
            # الفيديوهات التعليمية
            ('videos', 'view'), ('videos', 'create'), ('videos', 'delete'), ('videos', 'manage'),
            # المناقصات
            ('tenders', 'view'), ('tenders', 'create'), ('tenders', 'edit'), ('tenders', 'delete'), ('tenders', 'export'),
            # الاستيراد والتصدير
            ('importexport', 'view'), ('importexport', 'create'), ('importexport', 'edit'), ('importexport', 'delete'),
            # صيانة المعدات
            ('equipmaint', 'view'), ('equipmaint', 'create'), ('equipmaint', 'edit'), ('equipmaint', 'delete'),
            # إدارة العلاقات
            ('crm', 'view'), ('crm', 'create'), ('crm', 'edit'), ('crm', 'delete'), ('crm', 'export'),
            # التحليلات الذكية
            ('analytics', 'view'), ('analytics', 'create'), ('analytics', 'manage'),
            # المساعد الذكي
            ('chatbot', 'view'), ('chatbot', 'manage'),
            # تمويل الشركات الناشئة
            ('startup_finance', 'view'), ('startup_finance', 'create'), ('startup_finance', 'edit'), ('startup_finance', 'delete'), ('startup_finance', 'export'),
        ]

        for module, action in default_perms:
            perm, created = Permission.objects.get_or_create(
                module=module,
                action=action,
                defaults={
                    'code': f'{module}_{action}',
                    'description': f'{dict(Permission.MODULE_CHOICES).get(module, module)} - {dict(Permission.ACTION_CHOICES).get(action, action)}',
                }
            )
            if created:
                created_count += 1

        # Assign all permissions to admin
        admin_perms = Permission.objects.all()
        existing_admin = set(
            RolePermission.objects.filter(role='admin').values_list('permission_id', flat=True)
        )
        new_admin_perms = [
            RolePermission(role='admin', permission_id=p.id)
            for p in admin_perms if p.id not in existing_admin
        ]
        if new_admin_perms:
            RolePermission.objects.bulk_create(new_admin_perms)

        return Response({
            'message': f'تم إنشاء {created_count} صلاحية جديدة',
            'total_permissions': Permission.objects.count(),
            'admin_permissions': RolePermission.objects.filter(role='admin').count(),
        })


# ===== Business Owner Registration (Public) =====

class OwnerRegisterView(APIView):
    """Public registration for business owner (creates first admin account)."""
    permission_classes = [AllowAny]
    throttle_scope = 'register'

    def get(self, request):
        """Check if owner registration is available (no admin exists yet)."""
        admin_exists = User.objects.filter(role='admin').exists()
        return Response({
            'registration_available': not admin_exists,
        })

    def post(self, request):
        """Register a new business owner account."""
        # Only allow admin role registration through this endpoint
        data = request.data.copy()
        data['role'] = 'admin'

        # Check if any admin already exists
        if User.objects.filter(role='admin').exists():
            return Response({
                'error': 'يوجد مدير نظام بالفعل. يرجى التواصل مع المدير الحالي.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])

            # Seed default permissions and assign all to admin
            self._seed_permissions(user)

            # Create audit log
            from auditlog.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='other',
                model_name='User',
                object_repr='owner_register',
                changes={'details': 'تسجيل صاحب العمل الأول'},
                ip_address=self.get_client_ip(request),
            )

            # Send welcome notification
            from notifications.models import Notification
            Notification.notify(
                user=user,
                title='مرحباً بك في نظام RIADAH ERP',
                message='تم إنشاء حسابك بنجاح كصاحب العمل. يمكنك الآن إدارة النظام بالكامل وإضافة الموظفين.',
                notification_type='success',
                link='/dashboard',
            )

            # Generate JWT tokens for auto-login
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            refresh['username'] = user.username
            refresh['role'] = user.role
            refresh['email'] = user.email
            refresh['two_factor_enabled'] = user.two_factor_enabled

            return Response({
                'message': 'تم إنشاء حساب صاحب العمل بنجاح',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _seed_permissions(self, admin_user):
        """Seed default permissions and assign all to admin role."""
        default_perms = [
            ('dashboard', 'view'),
            ('inventory', 'view'), ('inventory', 'create'), ('inventory', 'edit'), ('inventory', 'delete'), ('inventory', 'export'),
            ('sales', 'view'), ('sales', 'create'), ('sales', 'edit'), ('sales', 'delete'), ('sales', 'export'), ('sales', 'approve'),
            ('purchases', 'view'), ('purchases', 'create'), ('purchases', 'edit'), ('purchases', 'delete'), ('purchases', 'export'), ('purchases', 'approve'),
            ('accounting', 'view'), ('accounting', 'create'), ('accounting', 'edit'), ('accounting', 'delete'), ('accounting', 'export'), ('accounting', 'approve'),
            ('hr', 'view'), ('hr', 'create'), ('hr', 'edit'), ('hr', 'delete'), ('hr', 'export'), ('hr', 'approve'),
            ('documents', 'view'), ('documents', 'create'), ('documents', 'delete'),
            ('projects', 'view'), ('projects', 'create'), ('projects', 'edit'), ('projects', 'delete'), ('projects', 'export'),
            ('notifications', 'view'), ('notifications', 'manage'),
            ('auditlog', 'view'), ('auditlog', 'export'),
            ('users', 'view'), ('users', 'create'), ('users', 'edit'), ('users', 'delete'),
            ('reports', 'view'), ('reports', 'export'),
            ('backup', 'manage'),
            ('permissions', 'view'), ('permissions', 'manage'),
            ('pos', 'view'), ('pos', 'create'), ('pos', 'edit'), ('pos', 'delete'),
            ('invoicing', 'view'), ('invoicing', 'create'), ('invoicing', 'edit'), ('invoicing', 'delete'), ('invoicing', 'export'),
            ('payroll', 'view'), ('payroll', 'create'), ('payroll', 'edit'), ('payroll', 'export'),
            ('warehouse', 'view'), ('warehouse', 'create'), ('warehouse', 'edit'), ('warehouse', 'delete'), ('warehouse', 'export'),
            ('payments', 'view'), ('payments', 'create'), ('payments', 'edit'), ('payments', 'delete'),
            ('videos', 'view'), ('videos', 'create'), ('videos', 'delete'), ('videos', 'manage'),
        ]
        for module, action in default_perms:
            Permission.objects.get_or_create(
                module=module,
                action=action,
                defaults={
                    'code': f'{module}_{action}',
                    'description': f'{dict(Permission.MODULE_CHOICES).get(module, module)} - {dict(Permission.ACTION_CHOICES).get(action, action)}',
                }
            )
        # Assign ALL permissions to admin
        all_perms = Permission.objects.all()
        existing = set(RolePermission.objects.filter(role='admin').values_list('permission_id', flat=True))
        new_perms = [RolePermission(role='admin', permission_id=p.id) for p in all_perms if p.id not in existing]
        if new_perms:
            RolePermission.objects.bulk_create(new_perms)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


# ===== Invitation Views =====

class InvitationCreateView(APIView):
    """Create employee invitation (admin/HR only)."""
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def post(self, request):
        """Create a new employee invitation."""
        user = request.user
        if user.role not in ('admin', 'hr'):
            return Response(
                {'error': 'فقط المدير وموظف الموارد البشرية يمكنهم إرسال الدعوات'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InvitationCreateSerializer(data=request.data)
        if serializer.is_valid():
            invitation = Invitation(
                email=serializer.validated_data['email'],
                role=serializer.validated_data['role'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                phone=serializer.validated_data.get('phone', ''),
                invited_by=user,
            )
            invitation.generate_token()

            # Set expiry (7 days from now)
            from django.utils import timezone
            from datetime import timedelta
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()

            # Build invitation link
            frontend_url = request.META.get('HTTP_ORIGIN', '') or 'http://localhost:5173'
            invite_link = f"{frontend_url}/accept-invitation/{invitation.token}"

            # Try to send email
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                role_display = dict(User.ROLE_CHOICES).get(invitation.role, invitation.role)
                send_mail(
                    subject=f'RIADAH ERP - دعوة للانضمام كـ{role_display}',
                    message=f'مرحباً،\n\nتمت دعوتك للانضمام إلى نظام RIADAH ERP كـ{role_display}.\n\nللقبول، اضغط على الرابط التالي:\n{invite_link}\n\nينتهي هذا الرابط بعد 7 أيام.\n\nRIADAH ERP',
                    from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@riadah.com',
                    recipient_list=[invitation.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            # Audit log
            from auditlog.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='Invitation',
                object_repr=f'دعوة موظف: {invitation.email} بدور {invitation.get_role_display()}',
                ip_address=self._get_client_ip(request),
            )

            return Response({
                'message': 'تم إرسال الدعوة بنجاح',
                'invitation': InvitationListSerializer(invitation).data,
                'invite_link': invite_link,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class InvitationListView(APIView):
    """List all invitations (admin/HR only)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ('admin', 'hr'):
            return Response(
                {'error': 'غير مصرح بالوصول'},
                status=status.HTTP_403_FORBIDDEN
            )

        invitations = Invitation.objects.all().order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            invitations = invitations.filter(status=status_filter)

        # Simple pagination without PageNumberPagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(invitations, request)
        serializer = InvitationListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class InvitationAcceptView(APIView):
    """Accept an invitation and create user account."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        """Get invitation details by token (for the registration form)."""
        try:
            invitation = Invitation.objects.select_related('invited_by').get(token=token)
        except Invitation.DoesNotExist:
            return Response(
                {'error': 'رمز الدعوة غير صالح'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.status != 'pending':
            return Response(
                {'error': 'هذه الدعوة غير صالحة أو تم استخدامها بالفعل'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {'error': 'انتهت صلاحية هذه الدعوة'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'email': invitation.email,
            'role': invitation.role,
            'role_display': dict(User.ROLE_CHOICES).get(invitation.role, invitation.role),
            'first_name': invitation.first_name,
            'last_name': invitation.last_name,
            'invited_by': invitation.invited_by.get_full_name() or invitation.invited_by.username,
            'company_name': 'RIADAH ERP',
        })

    def post(self, request, token):
        """Accept invitation and create user account."""
        data = request.data.copy()
        data['token'] = token

        serializer = InvitationAcceptSerializer(data=data)
        if serializer.is_valid():
            invitation = serializer.context['invitation']

            # Create user from invitation data
            user = User(
                username=serializer.validated_data['username'],
                email=invitation.email,
                role=invitation.role,
                first_name=invitation.first_name,
                last_name=invitation.last_name,
                phone=invitation.phone,
                must_change_password=False,
                is_active=True,
            )
            user.set_password(serializer.validated_data['password'])
            user.save()
            user.record_password_change(serializer.validated_data['password'])

            # Update invitation status
            from django.utils import timezone
            invitation.status = 'accepted'
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['status', 'accepted_at'])

            # Audit log
            from auditlog.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='User',
                object_repr=f'تم قبول الدعوة من {invitation.invited_by.username}',
                ip_address=self._get_client_ip(request),
            )

            # Notify the inviter
            from notifications.models import Notification
            Notification.notify(
                user=invitation.invited_by,
                title='تم قبول الدعوة',
                message=f'الموظف {user.get_full_name()} ({user.username}) قبل الدعوة وانضم إلى النظام',
                notification_type='success',
                link='/users',
            )

            # Generate JWT tokens for auto-login
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'تم إنشاء حسابك بنجاح!',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class InvitationCancelView(APIView):
    """Cancel a pending invitation (admin/HR only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in ('admin', 'hr'):
            return Response(
                {'error': 'غير مصرح بهذه العملية'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            invitation = Invitation.objects.get(pk=pk)
        except Invitation.DoesNotExist:
            return Response(
                {'error': 'الدعوة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.status != 'pending':
            return Response(
                {'error': 'لا يمكن إلغاء دعوة غير معلقة'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = 'cancelled'
        invitation.save(update_fields=['status'])

        from auditlog.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='delete',
            model_name='Invitation',
            object_repr=f'إلغاء دعوة: {invitation.email}',
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return Response({'message': 'تم إلغاء الدعوة بنجاح'})
