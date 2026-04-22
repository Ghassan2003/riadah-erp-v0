"""
HR Models for ERP System - Phase 5.
Manages Departments, Employees, Attendance, and Leave Requests.
"""

from django.db import models
from django.utils import timezone


class Department(models.Model):
    """Department model for organizing employees by teams."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='اسم القسم',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم القسم (إنجليزي)',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='مدير القسم',
        help_text='موظف مسؤول عن إدارة القسم',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employees_count(self):
        return self.employees.filter(is_active=True).count()


class Employee(models.Model):
    """Employee model linked to the User model with HR-specific fields."""

    GENDER_CHOICES = (
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    )

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('on_leave', 'في إجازة'),
        ('suspended', 'موقوف'),
        ('terminated', 'منتهي الخدمة'),
    )

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='حساب المستخدم',
        null=True,
        blank=True,
        help_text='ربط الموظف بحساب مستخدم في النظام',
    )
    employee_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الموظف',
        db_index=True,
        editable=False,
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name='الاسم الأول',
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='اسم العائلة',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='البريد الإلكتروني',
        db_index=True,
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='رقم الهاتف',
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        default='',
        verbose_name='الجنس',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='القسم',
    )
    position = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المسمى الوظيفي',
    )
    hire_date = models.DateField(
        verbose_name='تاريخ التعيين',
        db_index=True,
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='الراتب الأساسي',
        help_text='الراتب الشهري بالريال السعودي',
    )
    housing_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='بدل سكن',
    )
    transport_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='بدل نقل',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='اسم البنك',
    )
    bank_account = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='رقم الحساب البنكي',
    )
    national_id = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='رقم الهوية',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'موظف'
        verbose_name_plural = 'الموظفون'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee_number} - {self.full_name}'

    def generate_employee_number(self):
        """Generate a unique employee number: EMP-XXXX."""
        last_employee = Employee.objects.filter(
            employee_number__startswith='EMP-'
        ).order_by('-employee_number').first()

        if last_employee:
            try:
                seq = int(last_employee.employee_number.split('-')[1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'EMP-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.employee_number:
            self.employee_number = self.generate_employee_number()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def total_salary(self):
        """Calculate total monthly compensation."""
        return self.salary + self.housing_allowance + self.transport_allowance


class Attendance(models.Model):
    """Daily attendance record for each employee."""

    STATUS_CHOICES = (
        ('present', 'حاضر'),
        ('absent', 'غائب'),
        ('late', 'متأخر'),
        ('half_day', 'نصف يوم'),
        ('holiday', 'إجازة رسمية'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name='الموظف',
    )
    date = models.DateField(
        verbose_name='التاريخ',
        db_index=True,
    )
    check_in = models.TimeField(
        null=True,
        blank=True,
        verbose_name='وقت الحضور',
    )
    check_out = models.TimeField(
        null=True,
        blank=True,
        verbose_name='وقت الانصراف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        verbose_name='الحالة',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'سجل حضور'
        verbose_name_plural = 'سجلات الحضور'
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f'{self.employee.full_name} - {self.date} ({self.get_status_display()})'

    @property
    def hours_worked(self):
        """Calculate hours worked if check_in and check_out exist."""
        if self.check_in and self.check_out:
            from datetime import datetime, time
            dt_in = datetime.combine(self.date, self.check_in)
            dt_out = datetime.combine(self.date, self.check_out)
            diff = (dt_out - dt_in).total_seconds() / 3600
            return round(diff, 2)
        return 0


class LeaveRequest(models.Model):
    """Employee leave/vacation request with approval workflow."""

    LEAVE_TYPE_CHOICES = (
        ('annual', 'إجازة سنوية'),
        ('sick', 'إجازة مرضية'),
        ('emergency', 'إجازة طارئة'),
        ('maternity', 'إجازة أمومة'),
        ('hajj', 'إجازة حج'),
        ('unpaid', 'إجازة بدون راتب'),
        ('other', 'إجازة أخرى'),
    )

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('rejected', 'مرفوضة'),
        ('cancelled', 'ملغاة'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name='الموظف',
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        verbose_name='نوع الإجازة',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
        db_index=True,
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    days = models.PositiveIntegerField(
        verbose_name='عدد الأيام',
        help_text='يُحسب تلقائياً من تاريخ البداية والنهاية',
    )
    reason = models.TextField(
        blank=True,
        default='',
        verbose_name='السبب',
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الموافقة',
        db_index=True,
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'طلب إجازة'
        verbose_name_plural = 'طلبات الإجازات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.get_leave_type_display()} ({self.get_approval_status_display()})'

    def save(self, *args, **kwargs):
        """Auto-calculate days from start and end dates."""
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            self.days = max(delta, 1)
        super().save(*args, **kwargs)
