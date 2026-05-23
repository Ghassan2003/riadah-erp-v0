"""
Equipment Maintenance Models for ERP System.
Manages Equipment, MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart, and EquipmentInspection.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    """Equipment model representing physical assets that require maintenance."""

    CATEGORY_CHOICES = (
        ('machinery', 'آلات'),
        ('vehicle', 'مركبات'),
        ('electrical', 'كهربائية'),
        ('plumbing', 'سباكة'),
        ('hvac', 'تكييف وتبريد'),
        ('safety', 'سلامة'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('operational', 'تعمل'),
        ('maintenance', 'صيانة'),
        ('broken', 'معطلة'),
        ('retired', 'متقاعدة'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
    )
    equipment_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم المعدة',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='التصنيف',
    )
    brand = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='العلامة التجارية',
    )
    model_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='رقم الموديل',
    )
    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='الرقم التسلسلي',
    )
    location = models.TextField(
        verbose_name='الموقع',
    )
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الشراء',
    )
    purchase_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الشراء',
    )
    warranty_end = models.DateField(
        null=True,
        blank=True,
        verbose_name='انتهاء الضمان',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='operational',
        verbose_name='الحالة',
        db_index=True,
    )
    assigned_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='القسم المكلف',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='مسؤول الصيانة',
    )
    current_meter_reading = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='قراءة العداد الحالية',
    )
    image = models.ImageField(
        upload_to='equipment/',
        blank=True,
        verbose_name='صورة المعدة',
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
        ordering = ['name']
        verbose_name = 'المعدة'
        verbose_name_plural = 'المعدات'

    def __str__(self):
        return f'{self.name} ({self.equipment_number})'


class MaintenanceSchedule(models.Model):
    """Maintenance schedule for periodic equipment maintenance."""

    MAINTENANCE_TYPE_CHOICES = (
        ('preventive', 'وقائية'),
        ('corrective', 'تصحيحية'),
        ('emergency', 'طوارئ'),
        ('inspection', 'فحص'),
    )

    FREQUENCY_TYPE_CHOICES = (
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
        ('custom', 'مخصص'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='المعدة',
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES,
        verbose_name='نوع الصيانة',
    )
    frequency_type = models.CharField(
        max_length=20,
        choices=FREQUENCY_TYPE_CHOICES,
        verbose_name='نوع التكرار',
    )
    frequency_value = models.IntegerField(
        default=1,
        verbose_name='قيمة التكرار',
        help_text='عدد الوحدات (أيام/أسابيع/أشهر)',
    )
    last_performed = models.DateField(
        null=True,
        blank=True,
        verbose_name='آخر تنفيذ',
    )
    next_due = models.DateField(
        verbose_name='تاريخ الاستحقاق التالي',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='المسؤول',
    )
    estimated_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة المقدرة',
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='الساعات المقدرة',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
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
        ordering = ['next_due']
        verbose_name = 'جدول الصيانة'
        verbose_name_plural = 'جداول الصيانة'

    def __str__(self):
        return f'صيانة {self.equipment.name} - {self.get_maintenance_type_display()} ({self.next_due})'


class MaintenanceWorkOrder(models.Model):
    """Maintenance work order for tracking maintenance tasks."""

    WORK_TYPE_CHOICES = (
        ('preventive', 'وقائية'),
        ('corrective', 'تصحيحية'),
        ('emergency', 'طوارئ'),
        ('inspection', 'فحص'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    STATUS_CHOICES = (
        ('requested', 'مطلوب'),
        ('approved', 'موافق عليه'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    work_order_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم أمر العمل',
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='work_orders',
        verbose_name='المعدة',
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name='جدول الصيانة',
    )
    work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        verbose_name='نوع العمل',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='requested',
        verbose_name='الحالة',
        db_index=True,
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_requests',
        verbose_name='مقدم الطلب',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_assignments',
        verbose_name='المسؤول عن التنفيذ',
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ البدء',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإنجاز',
    )
    actual_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة الفعلية',
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='الساعات الفعلية',
    )
    parts_used = models.TextField(
        blank=True,
        default='',
        verbose_name='القطع المستخدمة',
    )
    completion_notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات الإنجاز',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_approvals',
        verbose_name='وافق بواسطة',
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
        verbose_name = 'أمر عمل صيانة'
        verbose_name_plural = 'أوامر عمل الصيانة'

    def __str__(self):
        return f'{self.work_order_number} - {self.equipment.name} ({self.get_status_display()})'


class MaintenancePart(models.Model):
    """Maintenance parts used in work orders."""

    work_order = models.ForeignKey(
        MaintenanceWorkOrder,
        on_delete=models.CASCADE,
        related_name='parts',
        verbose_name='أمر العمل',
    )
    part_name = models.CharField(
        max_length=255,
        verbose_name='اسم القطعة',
    )
    part_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='رقم القطعة',
    )
    quantity = models.IntegerField(
        default=1,
        verbose_name='الكمية',
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الوحدة',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='المورد',
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
        ordering = ['part_name']
        verbose_name = 'قطعة غيار'
        verbose_name_plural = 'قطع الغيار'

    def __str__(self):
        return f'{self.part_name} ({self.quantity})'

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost


class EquipmentInspection(models.Model):
    """Equipment inspection records."""

    INSPECTION_TYPE_CHOICES = (
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
        ('annual', 'سنوي'),
        ('special', 'خاص'),
    )

    CONDITION_RATING_CHOICES = (
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('poor', 'ضعيف'),
        ('critical', 'حرج'),
    )

    STATUS_CHOICES = (
        ('pass', 'ناجح'),
        ('conditional_pass', 'ناجح بشروط'),
        ('fail', 'فاشل'),
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name='المعدة',
    )
    inspection_type = models.CharField(
        max_length=20,
        choices=INSPECTION_TYPE_CHOICES,
        verbose_name='نوع الفحص',
    )
    inspector = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='المفتش',
    )
    inspection_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الفحص',
    )
    condition_rating = models.CharField(
        max_length=20,
        choices=CONDITION_RATING_CHOICES,
        verbose_name='تقييم الحالة',
    )
    findings = models.TextField(
        blank=True,
        default='',
        verbose_name='الملاحظات',
    )
    recommendations = models.TextField(
        blank=True,
        default='',
        verbose_name='التوصيات',
    )
    next_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الفحص التالي',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pass',
        verbose_name='النتيجة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-inspection_date']
        verbose_name = 'فحص المعدة'
        verbose_name_plural = 'فحوصات المعدات'

    def __str__(self):
        return f'فحص {self.equipment.name} - {self.get_condition_rating_display()} ({self.inspection_date.strftime("%Y-%m-%d")})'
