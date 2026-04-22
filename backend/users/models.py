"""
Custom User model with role-based access control.
Roles: admin, warehouse, sales, accountant, hr, purchasing, project_manager
Includes: 2FA (TOTP), Password Policy, Granular Permissions
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp
import base64
import secrets


class User(AbstractUser):
    """Custom user model with role-based permissions, 2FA, and password policy."""

    ROLE_CHOICES = (
        ('admin', 'مدير النظام'),
        ('warehouse', 'موظف المخازن'),
        ('sales', 'موظف المبيعات'),
        ('accountant', 'المحاسب'),
        ('hr', 'موظف الموارد البشرية'),
        ('purchasing', 'موظف المشتريات'),
        ('project_manager', 'مدير المشاريع'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='sales',
        verbose_name='الدور الوظيفي',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    # ===== 2FA Fields =====
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name='المصادقة الثنائية مفعّلة',
    )
    totp_secret = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='مفتاح TOTP',
    )
    two_factor_backup_codes = models.JSONField(
        default=list,
        blank=True,
        verbose_name='رموز الاسترداد',
    )

    # ===== Password Policy Fields =====
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر تغيير لكلمة المرور',
    )
    password_history = models.JSONField(
        default=list,
        blank=True,
        verbose_name='سجل كلمات المرور السابقة',
    )
    must_change_password = models.BooleanField(
        default=False,
        verbose_name='يجب تغيير كلمة المرور',
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP آخر تسجيل دخول',
    )

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_warehouse(self):
        return self.role in ('admin', 'warehouse')

    @property
    def is_sales(self):
        return self.role in ('admin', 'sales')

    @property
    def is_accountant(self):
        return self.role in ('admin', 'accountant')

    @property
    def is_hr(self):
        return self.role in ('admin', 'hr')

    @property
    def is_purchasing(self):
        return self.role in ('admin', 'purchasing', 'warehouse')

    @property
    def is_project_manager(self):
        return self.role in ('admin', 'project_manager')

    @property
    def is_password_expired(self):
        """Check if password has expired based on system policy (90 days)."""
        if not self.password_changed_at:
            return False
        from django.utils import timezone
        from datetime import timedelta
        expiry_days = 90
        return timezone.now() > self.password_changed_at + timedelta(days=expiry_days)

    @property
    def days_until_password_expiry(self):
        """Days remaining until password expires."""
        if not self.password_changed_at:
            return 90
        from django.utils import timezone
        from datetime import timedelta
        expiry_days = 90
        remaining = (self.password_changed_at + timedelta(days=expiry_days)) - timezone.now()
        return max(0, remaining.days)

    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA."""
        secret = pyotp.random_base32()
        self.totp_secret = secret
        self.save(update_fields=['totp_secret'])
        return secret

    def get_totp_uri(self, secret=None):
        """Get otpauth:// URI for QR code generation."""
        s = secret or self.totp_secret
        if not s:
            return ''
        totp = pyotp.TOTP(s)
        return totp.provisioning_uri(
            name=self.username,
            issuer_name='نظام ERP',
        )

    def verify_totp(self, code):
        """Verify a TOTP code."""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code, valid_window=1)

    def verify_backup_code(self, code):
        """Verify and consume a backup code."""
        codes = self.two_factor_backup_codes or []
        if code in codes:
            codes.remove(code)
            self.two_factor_backup_codes = codes
            self.save(update_fields=['two_factor_backup_codes'])
            return True
        return False

    def generate_backup_codes(self, count=10):
        """Generate backup codes for 2FA."""
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        self.two_factor_backup_codes = codes
        self.save(update_fields=['two_factor_backup_codes'])
        return codes

    def record_password_change(self, raw_password=None):
        """Record a password change for history and policy tracking."""
        from django.utils import timezone
        self.password_changed_at = timezone.now()
        self.must_change_password = False
        # Save password hash to history (keep last 5)
        history = list(self.password_history or [])
        if raw_password:
            # Store a hash for comparison, not the raw password
            import hashlib
            pw_hash = hashlib.sha256(raw_password.encode()).hexdigest()
            history.append(pw_hash)
            history = history[-5:]  # Keep only last 5
        self.password_history = history
        self.save(update_fields=['password_changed_at', 'must_change_password', 'password_history'])

    def is_password_in_history(self, raw_password):
        """Check if a password was recently used."""
        import hashlib
        pw_hash = hashlib.sha256(raw_password.encode()).hexdigest()
        return pw_hash in (self.password_history or [])


class Permission(models.Model):
    """نظام صلاحيات مفصّل - تحكم دقيق بالأذونات لكل وحدة/عملية"""

    MODULE_CHOICES = (
        ('dashboard', 'لوحة التحكم'),
        ('inventory', 'إدارة المخزون'),
        ('sales', 'المبيعات'),
        ('purchases', 'المشتريات'),
        ('accounting', 'المحاسبة'),
        ('hr', 'الموارد البشرية'),
        ('documents', 'المستندات'),
        ('projects', 'المشاريع'),
        ('notifications', 'الإشعارات'),
        ('auditlog', 'سجل التدقيق'),
        ('users', 'إدارة المستخدمين'),
        ('reports', 'التقارير'),
        ('backup', 'النسخ الاحتياطي'),
        ('permissions', 'إدارة الصلاحيات'),
        ('pos', 'نقاط البيع'),
        ('invoicing', 'الفواتير'),
        ('payroll', 'الرواتب والأجور'),
        ('warehouse', 'المستودعات'),
        ('assets', 'الأصول الثابتة'),
        ('contracts', 'العقود'),
        ('payments', 'المدفوعات'),
        ('videos', 'الفيديوهات التعليمية'),
    )

    ACTION_CHOICES = (
        ('view', 'عرض'),
        ('create', 'إنشاء'),
        ('edit', 'تعديل'),
        ('delete', 'حذف'),
        ('export', 'تصدير'),
        ('approve', 'اعتماد'),
        ('manage', 'إدارة كاملة'),
    )

    module = models.CharField(
        max_length=30,
        choices=MODULE_CHOICES,
        verbose_name='الوحدة',
        db_index=True,
    )
    action = models.CharField(
        max_length=15,
        choices=ACTION_CHOICES,
        verbose_name='الإجراء',
        db_index=True,
    )
    code = models.CharField(
        max_length=60,
        unique=True,
        verbose_name='رمز الصلاحية',
        db_index=True,
    )
    description = models.CharField(
        max_length=200,
        verbose_name='الوصف',
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'صلاحية'
        verbose_name_plural = 'الصلاحيات'
        unique_together = ('module', 'action')
        ordering = ['module', 'action']

    def __str__(self):
        return f'{self.get_module_display()} - {self.get_action_display()}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f'{self.module}_{self.action}'
        super().save(*args, **kwargs)


class RolePermission(models.Model):
    """ربط الأدوار بالصلاحيات"""

    role = models.CharField(
        max_length=20,
        choices=User.ROLE_CHOICES,
        verbose_name='الدور',
        db_index=True,
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name='الصلاحية',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'صلاحية دور'
        verbose_name_plural = 'صلاحيات الأدوار'
        unique_together = ('role', 'permission')
        ordering = ['role']

    def __str__(self):
        return f'{self.get_role_display()} - {self.permission}'


class SystemSetting(models.Model):
    """إعدادات النظام - سياسات الأمان والعمليات"""

    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='المفتاح',
        db_index=True,
    )
    value = models.TextField(
        verbose_name='القيمة',
        blank=True,
        default='',
    )
    description = models.CharField(
        max_length=300,
        verbose_name='الوصف',
        blank=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'إعداد نظام'
        verbose_name_plural = 'إعدادات النظام'
        ordering = ['key']

    def __str__(self):
        return f'{self.key}: {self.value}'

    @classmethod
    def get(cls, key, default=''):
        try:
            obj = cls.objects.get(key=key)
            return obj.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=''):
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': str(value), 'description': description}
        )
        return obj
