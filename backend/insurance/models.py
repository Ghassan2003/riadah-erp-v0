"""
Insurance & Pension Models for ERP System.
Manages InsurancePolicy, InsuranceClaim, PensionRecord, and PensionPayment.
"""

from django.db import models


class InsurancePolicy(models.Model):
    """بوليصة تأمين - Insurance Policy."""

    INSURANCE_TYPE_CHOICES = (
        ('health', 'تأمين صحي'),
        ('life', 'تأمين حياة'),
        ('property', 'تأمين ممتلكات'),
        ('vehicle', 'تأمين مركبات'),
        ('liability', 'تأمين مسؤولية'),
        ('workers_comp', 'تأمين إصابات عمل'),
        ('other', 'أخرى'),
    )

    PREMIUM_FREQUENCY_CHOICES = (
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
    )

    STATUS_CHOICES = (
        ('active', 'نشطة'),
        ('expired', 'منتهية'),
        ('cancelled', 'ملغاة'),
        ('pending', 'قيد الانتظار'),
    )

    INSURED_ENTITY_CHOICES = (
        ('company', 'الشركة'),
        ('employee', 'موظف'),
        ('asset', 'أصل'),
        ('vehicle', 'مركبة'),
    )

    policy_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم البوليصة',
    )
    policy_name = models.CharField(
        max_length=255,
        verbose_name='اسم البوليصة',
    )
    insurance_provider = models.CharField(
        max_length=255,
        verbose_name='شركة التأمين',
    )
    insurance_type = models.CharField(
        max_length=20,
        choices=INSURANCE_TYPE_CHOICES,
        verbose_name='نوع التأمين',
    )
    coverage_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='مبلغ التغطية',
    )
    premium_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='مبلغ القسط',
    )
    premium_frequency = models.CharField(
        max_length=15,
        choices=PREMIUM_FREQUENCY_CHOICES,
        default='annual',
        verbose_name='تكرار القسط',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    insured_entity = models.CharField(
        max_length=20,
        choices=INSURED_ENTITY_CHOICES,
        verbose_name='الجهة المؤمنة',
    )
    related_entity_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='معرف الكيان المرتبط',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        verbose_name = 'بوليصة تأمين'
        verbose_name_plural = 'بوالص التأمين'

    def __str__(self):
        return f'{self.policy_number} - {self.policy_name}'


class InsuranceClaim(models.Model):
    """طلب تعويض - Insurance Claim."""

    CLAIM_TYPE_CHOICES = (
        ('full', 'تعويض كامل'),
        ('partial', 'تعويض جزئي'),
    )

    STATUS_CHOICES = (
        ('submitted', 'مقدم'),
        ('under_review', 'قيد المراجعة'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('paid', 'مدفوع'),
    )

    claim_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم الطلب',
    )
    policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='claims',
        verbose_name='البوليصة',
    )
    claim_type = models.CharField(
        max_length=10,
        choices=CLAIM_TYPE_CHOICES,
        default='full',
        verbose_name='نوع التعويض',
    )
    incident_date = models.DateField(
        verbose_name='تاريخ الحادث',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    claimed_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ المطلوب',
    )
    approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المعتمد',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name='الحالة',
        db_index=True,
    )
    submitted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_claims_submitted',
        verbose_name='قدم بواسطة',
    )
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_claims_reviewed',
        verbose_name='راجع بواسطة',
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ المراجعة',
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    documents = models.TextField(
        blank=True,
        default='',
        verbose_name='المستندات',
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
        verbose_name = 'طلب تعويض'
        verbose_name_plural = 'طلبات التعويض'

    def __str__(self):
        return f'{self.claim_number} - {self.get_status_display()}'


class PensionRecord(models.Model):
    """سجل معاش - Pension Record."""

    CONTRIBUTION_TYPE_CHOICES = (
        ('employer', 'صاحب العمل'),
        ('employee', 'الموظف'),
        ('both', 'الطرفان'),
    )

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('suspended', 'معلق'),
        ('withdrawn', 'مسحوب'),
        ('retired', 'متقاعد'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='pension_records',
        verbose_name='الموظف',
    )
    pension_scheme = models.CharField(
        max_length=255,
        verbose_name='نظام المعاش',
    )
    contribution_type = models.CharField(
        max_length=20,
        choices=CONTRIBUTION_TYPE_CHOICES,
        default='both',
        verbose_name='نوع المساهمة',
    )
    monthly_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المساهمة الشهرية',
    )
    employer_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مساهمة صاحب العمل',
    )
    employee_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مساهمة الموظف',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
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
    total_contributions = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي المساهمات',
    )
    last_contribution_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر مساهمة',
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
        verbose_name = 'سجل معاش'
        verbose_name_plural = 'سجلات المعاشات'

    def __str__(self):
        return f'{self.employee.full_name if self.employee else ""} - {self.pension_scheme}'


class PensionPayment(models.Model):
    """دفعة معاش - Pension Payment."""

    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدي'),
    )

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('paid', 'مدفوعة'),
        ('failed', 'فاشلة'),
    )

    pension_record = models.ForeignKey(
        PensionRecord,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='سجل المعاش',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    payment_date = models.DateField(
        verbose_name='تاريخ الدفع',
    )
    month = models.IntegerField(
        verbose_name='الشهر',
    )
    year = models.IntegerField(
        verbose_name='السنة',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer',
        verbose_name='طريقة الدفع',
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='رقم المرجع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'دفعة معاش'
        verbose_name_plural = 'دفعات المعاشات'

    def __str__(self):
        return f'{self.pension_record} - {self.month}/{self.year} - {self.amount}'
