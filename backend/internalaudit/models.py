"""
Internal Audit & Compliance Models for ERP System.
Manages AuditPlans, AuditFindings, AuditEvidence, AuditActions, and ComplianceChecks.
"""

from django.db import models
from django.utils import timezone


class AuditPlan(models.Model):
    """خطة التدقيق - Audit plan representing a scheduled audit engagement."""

    AUDIT_TYPE_CHOICES = (
        ('financial', 'تدقيق مالي'),
        ('operational', 'تدقيق تشغيلي'),
        ('compliance', 'تدقيق توافق'),
        ('it', 'تدقيق تقنية المعلومات'),
        ('investigation', 'تحقيق'),
        ('special', 'تدقيق خاص'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    RISK_LEVEL_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
        help_text='اسم خطة التدقيق',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    fiscal_year = models.IntegerField(
        verbose_name='السنة المالية',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_plans',
        verbose_name='القسم',
    )
    audit_type = models.CharField(
        max_length=20,
        choices=AUDIT_TYPE_CHOICES,
        verbose_name='نوع التدقيق',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
    )
    lead_auditor = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_audit_plans',
        verbose_name='رئيس فريق التدقيق',
    )
    team_members = models.TextField(
        blank=True,
        default='',
        verbose_name='أعضاء الفريق',
        help_text='أسماء أعضاء فريق التدقيق',
    )
    scope = models.TextField(
        blank=True,
        default='',
        verbose_name='نطاق التدقيق',
    )
    objectives = models.TextField(
        blank=True,
        default='',
        verbose_name='أهداف التدقيق',
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='medium',
        verbose_name='مستوى المخاطر',
        db_index=True,
    )
    budget_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='ساعات الميزانية',
    )
    actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='الساعات الفعلية',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_plans_created',
        verbose_name='أنشئ بواسطة',
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
        ordering = ['-created_at']
        verbose_name = 'خطة تدقيق'
        verbose_name_plural = 'خطط التدقيق'

    def __str__(self):
        return self.name


class AuditFinding(models.Model):
    """ملاحظة تدقيق - Finding identified during an audit engagement."""

    SEVERITY_CHOICES = (
        ('info', 'معلومات'),
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    CATEGORY_CHOICES = (
        ('financial', 'مالي'),
        ('operational', 'تشغيلي'),
        ('compliance', 'توافق'),
        ('control', 'رقابي'),
        ('risk', 'مخاطر'),
        ('fraud', 'احتيال'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('open', 'مفتوحة'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'تم الحل'),
        ('closed', 'مغلقة'),
        ('accepted', 'مقبولة'),
    )

    audit_plan = models.ForeignKey(
        AuditPlan,
        on_delete=models.CASCADE,
        related_name='findings',
        verbose_name='خطة التدقيق',
    )
    finding_number = models.CharField(
        max_length=50,
        verbose_name='رقم الملاحظة',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='العنوان',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name='الخطورة',
        db_index=True,
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='التصنيف',
        db_index=True,
    )
    condition = models.TextField(
        verbose_name='الشرط',
        help_text='الوضع الحالي الذي تم رصده',
    )
    criteria = models.TextField(
        blank=True,
        default='',
        verbose_name='المعيار',
        help_text='المعيار أو المعايير التي يجب الالتزام بها',
    )
    cause = models.TextField(
        blank=True,
        default='',
        verbose_name='السبب',
        help_text='السبب الجذري للملاحظة',
    )
    effect = models.TextField(
        blank=True,
        default='',
        verbose_name='الأثر',
        help_text='الأثر المحتمل للملاحظة',
    )
    recommendation = models.TextField(
        verbose_name='التوصية',
        help_text='التوصيات لمعالجة الملاحظة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='الحالة',
        db_index=True,
    )
    responsible_person = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_findings_responsible',
        verbose_name='المسؤول',
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستحقاق',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحل',
    )
    resolved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_findings_resolved',
        verbose_name='تم الحل بواسطة',
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
        ordering = ['-created_at']
        verbose_name = 'ملاحظة تدقيق'
        verbose_name_plural = 'ملاحظات التدقيق'
        unique_together = ('audit_plan', 'finding_number')

    def __str__(self):
        return f'{self.finding_number} - {self.title}'


class AuditEvidence(models.Model):
    """دليل التدقيق - Evidence collected to support an audit finding."""

    EVIDENCE_TYPE_CHOICES = (
        ('document', 'مستند'),
        ('interview_observation', 'مقابلة/ملاحظة'),
        ('data_analysis', 'تحليل بيانات'),
        ('physical', 'فحص مادي'),
        ('other', 'أخرى'),
    )

    finding = models.ForeignKey(
        AuditFinding,
        on_delete=models.CASCADE,
        related_name='evidence',
        verbose_name='ملاحظة التدقيق',
    )
    evidence_type = models.CharField(
        max_length=30,
        choices=EVIDENCE_TYPE_CHOICES,
        verbose_name='نوع الدليل',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    file = models.FileField(
        upload_to='audit_evidence/',
        blank=True,
        verbose_name='الملف',
    )
    collected_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_evidence_collected',
        verbose_name='تم الجمع بواسطة',
    )
    collected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الجمع',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-collected_at']
        verbose_name = 'دليل تدقيق'
        verbose_name_plural = 'أدلة التدقيق'

    def __str__(self):
        return f'دليل - {self.get_evidence_type_display()} - {self.finding.finding_number}'


class AuditAction(models.Model):
    """إجراء تصحيحي - Corrective action to address an audit finding."""

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('overdue', 'متأخر'),
        ('cancelled', 'ملغي'),
    )

    finding = models.ForeignKey(
        AuditFinding,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name='ملاحظة التدقيق',
    )
    action_number = models.CharField(
        max_length=50,
        verbose_name='رقم الإجراء',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions_assigned',
        verbose_name='مسند إلى',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإنجاز',
    )
    evidence_of_completion = models.TextField(
        blank=True,
        default='',
        verbose_name='دليل الإنجاز',
    )
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions_verified',
        verbose_name='تم التحقق بواسطة',
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التحقق',
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
        ordering = ['-created_at']
        verbose_name = 'إجراء تصحيحي'
        verbose_name_plural = 'الإجراءات التصحيحية'
        unique_together = ('finding', 'action_number')

    def __str__(self):
        return f'{self.action_number} - {self.finding.finding_number}'


class ComplianceCheck(models.Model):
    """فحص توافق - Periodic compliance check against regulations."""

    FREQUENCY_CHOICES = (
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
    )

    STATUS_CHOICES = (
        ('compliant', 'متوافق'),
        ('partially_compliant', 'متوافق جزئياً'),
        ('non_compliant', 'غير متوافق'),
        ('not_checked', 'لم يتم الفحص'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
    )
    regulation = models.CharField(
        max_length=255,
        verbose_name='اللائحة/النظام',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compliance_checks',
        verbose_name='القسم',
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name='التكرار',
    )
    last_check = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر فحص',
    )
    next_check = models.DateField(
        verbose_name='تاريخ الفحص القادم',
    )
    responsible = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compliance_checks_responsible',
        verbose_name='المسؤول',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_checked',
        verbose_name='الحالة',
        db_index=True,
    )
    findings = models.TextField(
        blank=True,
        default='',
        verbose_name='الملاحظات',
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
        ordering = ['-created_at']
        verbose_name = 'فحص توافق'
        verbose_name_plural = 'فحوصات التوافق'

    def __str__(self):
        return f'{self.name} - {self.regulation}'
