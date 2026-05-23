"""
Contracts Models for ERP System.
Contract management with milestones and payments.
"""

from django.db import models
from django.utils import timezone


class Contract(models.Model):
    """Contract model for managing various types of agreements."""

    TYPE_CHOICES = (
        ('sales', 'بيع'),
        ('purchase', 'شراء'),
        ('service', 'خدمات'),
        ('rental', 'إيجار'),
        ('employment', 'توظيف'),
        ('consultancy', 'استشارات'),
        ('maintenance', 'صيانة'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('active', 'نشط'),
        ('expired', 'منتهي الصلاحية'),
        ('terminated', 'ملغي'),
        ('renewed', 'مجدّد'),
        ('cancelled', 'ملغي نهائياً'),
    )

    contract_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم العقد',
        db_index=True,
        editable=False,
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان العقد',
    )
    title_en = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='عنوان العقد (إنجليزي)',
    )
    contract_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='نوع العقد',
        db_index=True,
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name='العميل',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name='المورد',
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name='المشروع',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
    )
    value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='قيمة العقد',
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name='العملة',
    )
    vat_inclusive = models.BooleanField(
        default=True,
        verbose_name='شامل ضريبة القيمة المضافة',
    )
    payment_terms = models.TextField(
        blank=True,
        default='',
        verbose_name='شروط الدفع',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    terms_conditions = models.TextField(
        blank=True,
        default='',
        verbose_name='الشروط والأحكام',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    renewal_reminder_days = models.IntegerField(
        default=30,
        verbose_name='أيام تذكير التجديد',
        help_text='عدد الأيام قبل تاريخ الانتهاء لإرسال تذكير التجديد',
    )
    attachment = models.FileField(
        upload_to='contracts/',
        blank=True,
        verbose_name='المرفق',
    )
    signed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التوقيع',
    )
    signed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_contracts',
        verbose_name='وقع بواسطة',
    )
    responsible_person = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_contracts',
        verbose_name='المسؤول',
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
        related_name='created_contracts',
        verbose_name='أنشئ بواسطة',
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
        ordering = ['-created_at']
        verbose_name = 'عقد'
        verbose_name_plural = 'العقود'

    def __str__(self):
        return f'{self.contract_number} - {self.title}'

    def generate_contract_number(self):
        """Generate a unique contract number: CTR-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_ctr = Contract.objects.filter(
            contract_number__startswith=f'CTR-{today}'
        ).order_by('-contract_number').first()

        if last_ctr:
            try:
                seq = int(last_ctr.contract_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'CTR-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        super().save(*args, **kwargs)

    @property
    def remaining_days(self):
        """Days remaining until end_date."""
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(delta.days, 0)
        return None

    @property
    def days_active(self):
        """Number of days the contract has been active."""
        start = self.start_date or self.created_at.date()
        end = self.end_date or timezone.now().date()
        return (end - start).days

    @property
    def is_expired(self):
        """Check if contract has expired."""
        if self.end_date:
            return self.end_date < timezone.now().date()
        return False


class ContractMilestone(models.Model):
    """Milestone/deliverable within a contract."""

    STATUS_CHOICES = (
        ('pending', 'معلق'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('overdue', 'متأخر'),
    )

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='العقد',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان المرحلة',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )

    class Meta:
        verbose_name = 'مرحلة عقد'
        verbose_name_plural = 'مراحل العقود'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.contract.title} - {self.title}'


class ContractPayment(models.Model):
    """Payment schedule for a contract."""

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'معلقة'),
        ('paid', 'مدفوعة'),
        ('partially_paid', 'مدفوعة جزئياً'),
        ('overdue', 'متأخرة'),
    )

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='contract_payments',
        verbose_name='العقد',
    )
    milestone = models.ForeignKey(
        ContractMilestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='المرحلة',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الدفع',
        db_index=True,
    )
    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المدفوع',
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='طريقة الدفع',
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المرجع',
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
        verbose_name = 'دفعة عقد'
        verbose_name_plural = 'دفعات العقود'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.contract.title} - {self.amount} ({self.get_payment_status_display()})'
