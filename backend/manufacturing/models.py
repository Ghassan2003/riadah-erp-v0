"""
نماذج التصنيع لمنظومة ERP.
يدير قوائم المواد، أوامر الإنتاج، سجلات الإنتاج، مراكز العمل، وخطوات مسارات الإنتاج.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class BillOfMaterials(models.Model):
    """قائمة المواد (BOM) لمنتج معين."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('active', 'نشطة'),
        ('archived', 'مؤرشفة'),
    )

    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='boms',
        verbose_name='المنتج',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    version = models.IntegerField(
        default=1,
        verbose_name='الإصدار',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    effective_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ السريان',
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
        verbose_name = 'قائمة مواد'
        verbose_name_plural = 'قوائم المواد'

    def __str__(self):
        return f'{self.name} - v{self.version}'


class BOMItem(models.Model):
    """بند في قائمة المواد."""

    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='قائمة المواد',
    )
    material = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='bom_items',
        verbose_name='المادة',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية',
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الوحدة',
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
        ordering = ['bom', 'id']
        verbose_name = 'بند قائمة مواد'
        verbose_name_plural = 'بنود قوائم المواد'

    def __str__(self):
        return f'{self.bom.name} - {self.material.name} ({self.quantity})'


class ProductionOrder(models.Model):
    """أمر إنتاج."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('planned', 'مخطط'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغى'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('urgent', 'عاجل'),
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الأمر',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='production_orders',
        verbose_name='المنتج',
    )
    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_orders',
        verbose_name='قائمة المواد',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية المطلوبة',
    )
    quantity_produced = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية المنتجة',
    )
    quantity_defective = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية المعيبة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    planned_start_date = models.DateField(
        verbose_name='تاريخ البدء المخطط',
    )
    planned_end_date = models.DateField(
        verbose_name='تاريخ الانتهاء المخطط',
    )
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ البدء الفعلي',
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء الفعلي',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
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
        verbose_name = 'أمر إنتاج'
        verbose_name_plural = 'أوامر الإنتاج'

    def __str__(self):
        return f'{self.order_number} - {self.product.name}'


class ProductionLog(models.Model):
    """سجل الإنتاج."""

    OPERATION_TYPE_CHOICES = (
        ('setup', 'إعداد'),
        ('production', 'إنتاج'),
        ('quality_check', 'فحص الجودة'),
        ('packaging', 'تغليف'),
        ('maintenance', 'صيانة'),
    )

    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='أمر الإنتاج',
    )
    operation_type = models.CharField(
        max_length=20,
        choices=OPERATION_TYPE_CHOICES,
        verbose_name='نوع العملية',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية',
    )
    defect_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='كمية المعيوبات',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    operator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='المشغل',
    )
    log_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ السجل',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-log_date']
        verbose_name = 'سجل إنتاج'
        verbose_name_plural = 'سجلات الإنتاج'

    def __str__(self):
        return f'{self.production_order.order_number} - {self.get_operation_type_display()} ({self.log_date})'


class WorkCenter(models.Model):
    """مركز عمل."""

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('maintenance', 'صيانة'),
        ('inactive', 'غير نشط'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='الموقع',
    )
    capacity = models.IntegerField(
        default=1,
        verbose_name='السعة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    cost_per_hour = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الساعة',
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
        verbose_name = 'مركز عمل'
        verbose_name_plural = 'مراكز العمل'

    def __str__(self):
        return self.name


class RoutingStep(models.Model):
    """خطوة في مسار الإنتاج."""

    bom = models.ForeignKey(
        BillOfMaterials,
        on_delete=models.CASCADE,
        related_name='routing_steps',
        verbose_name='قائمة المواد',
    )
    step_number = models.IntegerField(
        verbose_name='رقم الخطوة',
    )
    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.CASCADE,
        related_name='routing_steps',
        verbose_name='مركز العمل',
    )
    operation_name = models.CharField(
        max_length=255,
        verbose_name='اسم العملية',
    )
    estimated_minutes = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الوقت المقدر (دقائق)',
    )
    cost_per_unit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الوحدة',
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
        ordering = ['bom', 'step_number']
        verbose_name = 'خطوة مسار إنتاج'
        verbose_name_plural = 'خطوات مسارات الإنتاج'

    def __str__(self):
        return f'{self.bom.name} - خطوة {self.step_number}: {self.operation_name}'
