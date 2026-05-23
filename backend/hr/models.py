"""
HR Models for ERP System - Phase 5.
Manages Departments, Employees, Attendance, and Leave Requests.
Enhanced with Holiday Calendar, Employment History, and Payslip models.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
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
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='القسم الأب',
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

    @employees_count.setter
    def employees_count(self, value):
        """Allow queryset annotations to set this value."""
        pass


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
        null=True,
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
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_attendance_employee_date'),
        ]
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


class LeaveBalance(models.Model):
    """Annual leave balance per employee per leave type."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name='الموظف',
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveRequest.LEAVE_TYPE_CHOICES,
        verbose_name='نوع الإجازة',
    )
    year = models.IntegerField(
        verbose_name='السنة',
    )
    total_days = models.PositiveIntegerField(
        default=30,
        verbose_name='الرصيد الإجمالي',
    )
    used_days = models.PositiveIntegerField(
        default=0,
        verbose_name='الأيام المستخدمة',
    )
    remaining_days = models.PositiveIntegerField(
        default=30,
        verbose_name='الأيام المتبقية',
    )
    carried_over = models.PositiveIntegerField(
        default=0,
        verbose_name='الأيام المنقولة',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'leave_type', 'year'], name='unique_leave_balance_employee_type_year'),
        ]
        verbose_name = 'رصيد الإجازات'
        verbose_name_plural = 'أرصدة الإجازات'
        ordering = ['employee__first_name', 'leave_type', '-year']

    def __str__(self):
        return f'{self.employee} - {self.get_leave_type_display()} - {self.year}'


class PerformanceReview(models.Model):
    """Employee performance review with multi-criteria ratings."""

    REVIEW_PERIOD_CHOICES = (
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('self_review', 'تقييم ذاتي'),
        ('manager_review', 'تقييم المدير'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='performance_reviews',
        verbose_name='الموظف',
    )
    reviewer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews_conducted',
        verbose_name='المقيّم',
    )
    review_period = models.CharField(
        max_length=20,
        choices=REVIEW_PERIOD_CHOICES,
        verbose_name='فترة التقييم',
    )
    year = models.IntegerField(
        verbose_name='السنة',
    )
    quarter = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='الربع',
        help_text='1-4 للتقييم الربعي',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )

    # Ratings (1-5 scale)
    goals_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='تقييم الأهداف',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    competencies_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='تقييم الكفاءات',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    teamwork_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='العمل الجماعي',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    communication_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='التواصل',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    initiative_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='المبادرة',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='التقييم العام',
    )

    strengths = models.TextField(
        blank=True,
        default='',
        verbose_name='نقاط القوة',
    )
    areas_for_improvement = models.TextField(
        blank=True,
        default='',
        verbose_name='مجالات التحسين',
    )
    goals_for_next_period = models.TextField(
        blank=True,
        default='',
        verbose_name='أهداف الفترة القادمة',
    )
    comments = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات عامة',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاكتمال',
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
        constraints = [
            models.UniqueConstraint(fields=['employee', 'review_period', 'year', 'quarter'], name='unique_performance_review_employee_period_year_quarter'),
        ]
        verbose_name = 'تقييم أداء'
        verbose_name_plural = 'تقييمات الأداء'
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f'تقييم {self.employee} - {self.year}'

    def save(self, *args, **kwargs):
        # Auto-calculate overall rating average
        ratings = [
            self.goals_rating, self.competencies_rating, self.teamwork_rating,
            self.communication_rating, self.initiative_rating,
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            self.overall_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        super().save(*args, **kwargs)


class Shift(models.Model):
    """Work shift definition with schedule details."""

    name = models.CharField(
        max_length=100,
        verbose_name='اسم الوردية',
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Shift Name (EN)',
    )
    start_time = models.TimeField(
        verbose_name='وقت البداية',
    )
    end_time = models.TimeField(
        verbose_name='وقت النهاية',
    )
    break_duration = models.PositiveIntegerField(
        default=60,
        verbose_name='مدة الاستراحة (دقيقة)',
        help_text='بالدقائق',
    )
    is_night = models.BooleanField(
        default=False,
        verbose_name='وردية ليلية',
    )
    applicable_days = models.JSONField(
        default=list,
        verbose_name='أيام التطبيق',
        help_text='قائمة بأرقام الأيام: 0=أحد, 1=إثنين, ... 6=سبت',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة',
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
        verbose_name = 'وردية'
        verbose_name_plural = 'الورديات'
        ordering = ['start_time']

    def __str__(self):
        return self.name

    @property
    def total_hours(self):
        from datetime import datetime, timedelta, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        if end <= start:
            end += timedelta(days=1)
        total = (end - start).seconds / 3600 - self.break_duration / 60
        return max(total, 0)


class EmployeeShift(models.Model):
    """Assignment of a shift to an employee with effective dates."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shift_assignments',
        verbose_name='الموظف',
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='employee_assignments',
        verbose_name='الوردية',
    )
    effective_date = models.DateField(
        verbose_name='تاريخ السريان',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
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
        verbose_name = 'تعيين وردية'
        verbose_name_plural = 'تعيينات الورديات'
        ordering = ['-effective_date']

    def __str__(self):
        return f'{self.employee} - {self.shift}'


# =============================================
# Holiday Calendar Models
# =============================================

class HolidayCalendar(models.Model):
    """Holiday calendar for a specific year."""

    name = models.CharField(
        max_length=255,
        verbose_name='اسم التقويم',
    )
    year = models.IntegerField(
        verbose_name='السنة',
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )

    class Meta:
        verbose_name = 'تقويم إجازات'
        verbose_name_plural = 'تقويمات الإجازات'
        ordering = ['-year', 'name']

    def __str__(self):
        return f'{self.name} - {self.year}'


class Holiday(models.Model):
    """Individual holiday within a holiday calendar."""

    HOLIDAY_TYPE_CHOICES = (
        ('public', 'إجازة رسمية'),
        ('company', 'إجازة الشركة'),
        ('optional', 'إجازة اختيارية'),
    )

    calendar = models.ForeignKey(
        HolidayCalendar,
        on_delete=models.CASCADE,
        related_name='holidays',
        verbose_name='التقويم',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم الإجازة',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الإجازة (إنجليزي)',
    )
    date = models.DateField(
        verbose_name='التاريخ',
        db_index=True,
    )
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES,
        default='public',
        verbose_name='نوع الإجازة',
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name='إجازة سنوية متكررة',
        help_text='إجازات مثل عيد الفطر وعيد الأضحى تتكرر سنوياً',
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
        verbose_name = 'إجازة رسمية'
        verbose_name_plural = 'الإجازات الرسمية'
        constraints = [
            models.UniqueConstraint(
                fields=['calendar', 'date'],
                name='unique_holiday_calendar_date',
            ),
        ]
        ordering = ['date']

    def __str__(self):
        return f'{self.name} - {self.date}'


# =============================================
# Employment History Model
# =============================================

class EmploymentHistory(models.Model):
    """Track all employment lifecycle events for an employee."""

    ACTION_TYPE_CHOICES = (
        ('hire', 'تعيين'),
        ('transfer', 'نقل'),
        ('promotion', 'ترقية'),
        ('demotion', 'تنزيل'),
        ('salary_change', 'تغيير راتب'),
        ('title_change', 'تغيير مسمى وظيفي'),
        ('termination', 'إنهاء خدمة'),
        ('rehire', 'إعادة تعيين'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='employment_history',
        verbose_name='الموظف',
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        verbose_name='نوع الإجراء',
        db_index=True,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employment_histories',
        verbose_name='القسم',
    )
    position = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المسمى الوظيفي',
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الراتب',
    )
    effective_date = models.DateField(
        verbose_name='تاريخ السريان',
        db_index=True,
    )
    previous_department = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='القسم السابق',
    )
    previous_position = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المسمى الوظيفي السابق',
    )
    previous_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الراتب السابق',
    )
    reason = models.TextField(
        blank=True,
        default='',
        verbose_name='السبب',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employment_histories_created',
        verbose_name='بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'سجل وظيفي'
        verbose_name_plural = 'السجلات الوظيفية'
        ordering = ['-effective_date', '-created_at']

    def __str__(self):
        return f'{self.employee} - {self.get_action_type_display()} - {self.effective_date}'


# =============================================
# Payslip Model
# =============================================

class Payslip(models.Model):
    """Monthly payslip for an employee with detailed salary breakdown."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('approved', 'معتمد'),
        ('paid', 'مدفوع'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدي'),
        ('check', 'شيك'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payslips',
        verbose_name='الموظف',
    )
    month = models.IntegerField(
        verbose_name='الشهر',
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        db_index=True,
    )
    year = models.IntegerField(
        verbose_name='السنة',
        db_index=True,
    )
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='الراتب الأساسي',
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
    overtime_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='أجر إضافي',
    )
    bonuses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='مكافآت',
    )
    deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصومات أخرى',
    )
    insurance_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصم التأمينات',
    )
    tax_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصم الضرائب',
    )
    loan_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصم القروض',
    )
    advance_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصم السلف',
    )
    other_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='خصومات أخرى',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payslips_approved',
        verbose_name='اعتمد بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاعتماد',
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        default='',
        verbose_name='طريقة الدفع',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التوليد',
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
        verbose_name = 'قسيمة راتب'
        verbose_name_plural = 'قسائم الرواتب'
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'month', 'year'],
                name='unique_payslip_employee_month_year',
            ),
        ]
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.employee} - {self.year}/{self.month:02d}'

    @property
    def total_earnings(self):
        """Calculate total earnings (income)."""
        return (
            self.basic_salary + self.housing_allowance + self.transport_allowance
            + self.overtime_pay + self.bonuses
        )

    @property
    def total_deductions(self):
        """Calculate total deductions."""
        return (
            self.deductions + self.insurance_deduction + self.tax_deduction
            + self.loan_deduction + self.advance_deduction + self.other_deduction
        )

    @property
    def net_pay(self):
        """Calculate net pay after all deductions."""
        return self.total_earnings - self.total_deductions
