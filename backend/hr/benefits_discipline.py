"""
Benefits, Discipline & Offboarding Models for ERP System.
Manages Health Insurance, Employee Insurance, Disciplinary Actions,
Grievances, and Employee Offboarding.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


# =============================================
# Helper Functions
# =============================================

def generate_action_number():
    """Generate a unique disciplinary action number: DIS-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'DIS-{today}-'

    from hr.benefits_discipline import DisciplinaryAction
    last_action = DisciplinaryAction.objects.filter(
        action_number__startswith=prefix,
    ).order_by('-action_number').first()

    if last_action:
        try:
            seq = int(last_action.action_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def generate_grievance_number():
    """Generate a unique grievance number: GRI-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'GRI-{today}-'

    from hr.benefits_discipline import Grievance
    last_grievance = Grievance.objects.filter(
        grievance_number__startswith=prefix,
    ).order_by('-grievance_number').first()

    if last_grievance:
        try:
            seq = int(last_grievance.grievance_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


# =============================================
# Health Insurance (تأمين صحي)
# =============================================

class HealthInsurance(models.Model):
    """Health insurance plan offered by the company to employees."""

    PLAN_TYPE_CHOICES = (
        ('basic', 'أساسي'),
        ('premium', 'متميز'),
        ('executive', 'تنفيذي'),
    )

    NETWORK_TYPE_CHOICES = (
        ('a', 'شبكة أ'),
        ('b', 'شبكة ب'),
        ('c', 'شبكة ج'),
    )

    insurance_provider = models.CharField(
        max_length=255,
        verbose_name='شركة التأمين',
        help_text='اسم شركة التأمين',
    )
    plan_name = models.CharField(
        max_length=255,
        verbose_name='اسم الخطة',
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPE_CHOICES,
        verbose_name='نوع الخطة',
        db_index=True,
    )
    monthly_premium_employee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='القسط الشهري (حصة الموظف)',
        help_text='المبلغ الذي يخصم من الموظف شهرياً بالريال السعودي',
    )
    monthly_premium_company = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='القسط الشهري (حصة الشركة)',
        help_text='المبلغ الذي تتحمله الشركة شهرياً بالريال السعودي',
    )
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='سقف التغطية',
        help_text='الحد الأقصى للتغطية السنوية بالريال السعودي',
    )
    network_type = models.CharField(
        max_length=10,
        choices=NETWORK_TYPE_CHOICES,
        verbose_name='نوع الشبكة',
        db_index=True,
        help_text='تصنيف شبكة التأمين السعودية',
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
        verbose_name = 'تأمين صحي'
        verbose_name_plural = 'التأمينات الصحية'
        ordering = ['insurance_provider', 'plan_name']

    def __str__(self):
        return f'{self.insurance_provider} - {self.plan_name} ({self.get_plan_type_display()})'

    @property
    def total_monthly_premium(self):
        """Total monthly premium (employee + company share)."""
        return self.monthly_premium_employee + self.monthly_premium_company

    @property
    def total_annual_premium(self):
        """Total annual premium (employee + company share)."""
        return self.total_monthly_premium * Decimal('12')


# =============================================
# Employee Insurance Registration (تسجيل تأمين موظف)
# =============================================

class EmployeeInsurance(models.Model):
    """Registration of an employee in a specific health insurance plan."""

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('expired', 'منتهي'),
        ('cancelled', 'ملغي'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='insurance_records',
        verbose_name='الموظف',
    )
    insurance = models.ForeignKey(
        HealthInsurance,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='خطة التأمين',
    )
    policy_number = models.CharField(
        max_length=100,
        verbose_name='رقم الوثيقة',
        db_index=True,
    )
    member_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='رقم العضوية',
        help_text='رقم عضوية الموظف لدى شركة التأمين',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
        db_index=True,
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    dependents_count = models.IntegerField(
        default=0,
        verbose_name='عدد المعالين',
        help_text='عدد الأفراد المضافين تحت تغطية الموظف',
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
        verbose_name = 'تسجيل تأمين موظف'
        verbose_name_plural = 'تسجيلات تأمين الموظفين'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.insurance.plan_name} ({self.get_status_display()})'


# =============================================
# Disciplinary Action (إجراء تأديبي)
# =============================================

class DisciplinaryAction(models.Model):
    """Disciplinary action issued to an employee with severity tracking."""

    ACTION_TYPE_CHOICES = (
        ('verbal_warning', 'إنذار شفهي'),
        ('written_warning', 'إنذار كتابي'),
        ('final_warning', 'إنذار نهائي'),
        ('suspension', 'إيقاف'),
        ('demotion', 'تنزيل مرتبة'),
        ('termination', 'فصل من العمل'),
    )

    SEVERITY_CHOICES = (
        (1, 'طفيف'),
        (2, 'متوسط'),
        (3, 'كبير'),
        (4, 'حرج'),
    )

    action_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الإجراء',
        db_index=True,
        editable=False,
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='disciplinary_actions',
        verbose_name='الموظف',
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        verbose_name='نوع الإجراء',
        db_index=True,
    )
    severity_level = models.IntegerField(
        choices=SEVERITY_CHOICES,
        verbose_name='مستوى الخطورة',
        db_index=True,
        help_text='1=طفيف، 2=متوسط، 3=كبير، 4=حرج',
    )
    reason = models.TextField(
        verbose_name='السبب',
    )
    incident_date = models.DateField(
        verbose_name='تاريخ الحادثة',
        db_index=True,
    )
    incident_description = models.TextField(
        verbose_name='وصف الحادثة',
    )
    witnesses = models.TextField(
        blank=True,
        default='',
        verbose_name='الشهود',
        help_text='أسماء شهود الحادثة',
    )
    issued_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disciplinary_actions_issued',
        verbose_name='صادر من',
    )
    acknowledged_by_employee = models.BooleanField(
        default=False,
        verbose_name='تم الاعتراف من الموظف',
        db_index=True,
        help_text='هل اعترف الموظف بالإجراء التأديبي',
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاعتراف',
    )
    effective_date = models.DateField(
        verbose_name='تاريخ السريان',
        db_index=True,
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
        help_text='للإيقاف المؤقت - تاريخ انتهاء الإيقاف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    related_docs = models.JSONField(
        blank=True,
        default=dict,
        verbose_name='الوثائق المرتبطة',
        help_text='مراجع الوثائق المرتبطة بالإجراء',
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
        verbose_name = 'إجراء تأديبي'
        verbose_name_plural = 'الإجراءات التأديبية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action_number} - {self.employee.full_name} - {self.get_action_type_display()} ({self.get_severity_level_display()})'

    def save(self, *args, **kwargs):
        if not self.action_number:
            self.action_number = generate_action_number()
        super().save(*args, **kwargs)


# =============================================
# Grievance (شكوى)
# =============================================

class Grievance(models.Model):
    """Employee grievance with investigation workflow and resolution tracking."""

    GRIEVANCE_TYPE_CHOICES = (
        ('workplace', 'بيئة العمل'),
        ('harassment', 'تحرش'),
        ('discrimination', 'تمييز'),
        ('salary', 'راتب'),
        ('benefits', 'مزايا'),
        ('other', 'أخرى'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('critical', 'حرجة'),
    )

    STATUS_CHOICES = (
        ('submitted', 'مُقدّمة'),
        ('under_review', 'قيد المراجعة'),
        ('investigating', 'قيد التحقيق'),
        ('resolved', 'تم الحل'),
        ('rejected', 'مرفوضة'),
        ('closed', 'مغلقة'),
    )

    grievance_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الشكوى',
        db_index=True,
        editable=False,
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='grievances',
        verbose_name='الموظف',
    )
    grievance_type = models.CharField(
        max_length=20,
        choices=GRIEVANCE_TYPE_CHOICES,
        verbose_name='نوع الشكوى',
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='تفاصيل الشكوى',
    )
    resolution_requested = models.TextField(
        blank=True,
        default='',
        verbose_name='الحل المطلوب',
        help_text='ما يتوقعه الموظف كحل للشكوى',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name='الحالة',
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grievances_assigned',
        verbose_name='المسؤول عن الشكوى',
        help_text='المستخدم المكلف بالتحقيق في الشكوى',
    )
    resolution = models.TextField(
        blank=True,
        default='',
        verbose_name='الحل',
        help_text='وصف الحل النهائي المُتخذ',
    )
    resolution_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحل',
    )
    resolved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grievances_resolved',
        verbose_name='حُلّت بواسطة',
    )
    attachments = models.JSONField(
        blank=True,
        default=list,
        verbose_name='المرفقات',
        help_text='قائمة بالملفات المرفقة',
    )
    is_confidential = models.BooleanField(
        default=False,
        verbose_name='سرية',
        db_index=True,
        help_text='هل الشكوى سرية وتتطلب خصوصية',
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
        verbose_name = 'شكوى'
        verbose_name_plural = 'الشكاوى'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.grievance_number} - {self.employee.full_name} - {self.get_grievance_type_display()} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.grievance_number:
            self.grievance_number = generate_grievance_number()
        super().save(*args, **kwargs)


# =============================================
# Offboarding (إنهاء خدمات)
# =============================================

class Offboarding(models.Model):
    """Employee offboarding process with clearance checklist and final settlement."""

    OFFBOARDING_TYPE_CHOICES = (
        ('resignation', 'استقالة'),
        ('termination', 'فصل'),
        ('retirement', 'تقاعد'),
        ('end_of_contract', 'انتهاء العقد'),
    )

    CLEARANCE_STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
    )

    STATUS_CHOICES = (
        ('initiated', 'بدأت'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='offboarding_records',
        verbose_name='الموظف',
    )
    offboarding_type = models.CharField(
        max_length=20,
        choices=OFFBOARDING_TYPE_CHOICES,
        verbose_name='نوع إنهاء الخدمة',
        db_index=True,
    )
    last_working_day = models.DateField(
        verbose_name='آخر يوم عمل',
        db_index=True,
    )
    reason = models.TextField(
        verbose_name='السبب',
        help_text='سبب إنهاء الخدمة',
    )
    exit_interview_conducted = models.BooleanField(
        default=False,
        verbose_name='تم إجراء مقابلة المغادرة',
    )
    exit_interview_notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات مقابلة المغادرة',
    )
    exit_interview_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ مقابلة المغادرة',
    )
    clearance_status = models.CharField(
        max_length=20,
        choices=CLEARANCE_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة التصفية',
        db_index=True,
    )
    final_settlement_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='مبلغ التسوية النهائية',
        help_text='إجمالي المستحقات النهائية بالريال السعودي',
    )
    end_of_service_benefit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='مكافأة نهاية الخدمة',
        help_text='مكافأة نهاية الخدمة المستحقة بالريال السعودي',
    )
    outstanding_loans = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='القروض المستحقة',
        help_text='إجمالي القروض غير المسددة بالريال السعودي',
    )
    outstanding_advances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='السلف المستحقة',
        help_text='إجمالي السلف غير المستردة بالريال السعودي',
    )
    checklist = models.JSONField(
        default=dict,
        verbose_name='قائمة التحقق',
        help_text='مثال: {"it_clearance": false, "library_return": true}',
    )
    knowledge_transfer_done = models.BooleanField(
        default=False,
        verbose_name='تم نقل المعرفة',
        help_text='هل تم إكمال نقل المعرفة والمهام',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offboardings_approved',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated',
        verbose_name='الحالة',
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
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'إنهاء خدمات'
        verbose_name_plural = 'عمليات إنهاء الخدمات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.get_offboarding_type_display()} ({self.get_status_display()})'

    @property
    def net_settlement(self):
        """Auto-calculated net settlement: final settlement - outstanding deductions."""
        settlement = self.final_settlement_amount or Decimal('0')
        benefits = self.end_of_service_benefit or Decimal('0')
        total_deductions = self.outstanding_loans + self.outstanding_advances
        return (settlement + benefits) - total_deductions

    @property
    def total_deductions(self):
        """Total outstanding deductions (loans + advances)."""
        return self.outstanding_loans + self.outstanding_advances
