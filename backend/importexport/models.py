"""
Import/Export Models for ERP System.
Manages ImportOrders, ImportItems, ExportOrders, ExportItems, and CustomsDeclarations.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class ImportOrder(models.Model):
    """أمر استيراد - Import order for purchasing goods from international suppliers."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('submitted', 'مقدم'),
        ('customs', 'جمارك'),
        ('transit', 'عبور'),
        ('warehouse', 'مستودع'),
        ('customs_hold', 'احتجاز جمركي'),
        ('received', 'مستلم'),
        ('cancelled', 'ملغي'),
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الأمر',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.CASCADE,
        related_name='import_orders',
        verbose_name='المورد',
    )
    order_date = models.DateField(
        verbose_name='تاريخ الأمر',
    )
    expected_arrival = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الوصول المتوقع',
    )
    actual_arrival = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الوصول الفعلي',
    )
    port_of_entry = models.CharField(
        max_length=200,
        verbose_name='ميناء الدخول',
    )
    country_of_origin = models.CharField(
        max_length=200,
        verbose_name='بلد المنشأ',
    )
    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name='العملة',
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name='سعر الصرف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي المبلغ',
    )
    customs_duties = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرسوم الجمركية',
    )
    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='تكلفة الشحن',
    )
    insurance_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='تكلفة التأمين',
    )
    other_costs = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='تكاليف أخرى',
    )
    total_landed_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي التكلفة الواردة',
    )
    payment_terms = models.TextField(
        blank=True,
        default='',
        verbose_name='شروط الدفع',
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
        related_name='import_orders_created',
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
        ordering = ['-order_date', '-created_at']
        verbose_name = 'أمر استيراد'
        verbose_name_plural = 'أوامر الاستيراد'

    def __str__(self):
        return f'{self.order_number} - {self.get_status_display()}'

    def recalculate(self):
        """Recalculate total_landed_cost and save."""
        self.total_landed_cost = (
            self.total_amount
            + self.customs_duties
            + self.shipping_cost
            + self.insurance_cost
            + self.other_costs
        )
        self.save(update_fields=[
            'total_landed_cost', 'total_amount',
            'customs_duties', 'shipping_cost',
            'insurance_cost', 'other_costs', 'updated_at',
        ])


class ImportItem(models.Model):
    """بند الاستيراد - Individual line item within an import order."""

    import_order = models.ForeignKey(
        ImportOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='أمر الاستيراد',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_items',
        verbose_name='المنتج',
    )
    description = models.CharField(
        max_length=500,
        verbose_name='الوصف',
    )
    hs_code = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='رمز النظام المنسق',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية',
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='سعر الوحدة',
    )
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='إجمالي السعر',
    )
    customs_duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الرسوم الجمركية',
    )
    customs_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مبلغ الرسوم الجمركية',
    )
    unit = models.CharField(
        max_length=50,
        default='piece',
        verbose_name='الوحدة',
    )
    country_of_origin = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='بلد المنشأ',
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
        ordering = ['id']
        verbose_name = 'بند استيراد'
        verbose_name_plural = 'بنود الاستيراد'

    def __str__(self):
        return f'{self.description} - {self.import_order.order_number}'

    def save(self, *args, **kwargs):
        """Auto-calculate total_price and customs_amount before saving."""
        self.total_price = self.quantity * self.unit_price
        self.customs_amount = self.total_price * (self.customs_duty_rate / Decimal('100'))
        super().save(*args, **kwargs)


class ExportOrder(models.Model):
    """أمر تصدير - Export order for selling goods to international customers."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('packed', 'معبأ'),
        ('customs', 'جمارك'),
        ('shipped', 'مشحون'),
        ('delivered', 'مسلّم'),
        ('cancelled', 'ملغي'),
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الأمر',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.CASCADE,
        related_name='export_orders',
        verbose_name='العميل',
    )
    order_date = models.DateField(
        verbose_name='تاريخ الأمر',
    )
    ship_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الشحن',
    )
    port_of_loading = models.CharField(
        max_length=200,
        verbose_name='ميناء التحميل',
    )
    destination_country = models.CharField(
        max_length=200,
        verbose_name='بلد الوجهة',
    )
    destination_port = models.CharField(
        max_length=200,
        verbose_name='ميناء الوجهة',
    )
    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name='العملة',
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name='سعر الصرف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي المبلغ',
    )
    shipping_terms = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='شروط الشحن',
    )
    payment_terms = models.TextField(
        blank=True,
        default='',
        verbose_name='شروط الدفع',
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
        related_name='export_orders_created',
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
        ordering = ['-order_date', '-created_at']
        verbose_name = 'أمر تصدير'
        verbose_name_plural = 'أوامر التصدير'

    def __str__(self):
        return f'{self.order_number} - {self.get_status_display()}'


class ExportItem(models.Model):
    """بند التصدير - Individual line item within an export order."""

    export_order = models.ForeignKey(
        ExportOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='أمر التصدير',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='export_items',
        verbose_name='المنتج',
    )
    description = models.CharField(
        max_length=500,
        verbose_name='الوصف',
    )
    hs_code = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='رمز النظام المنسق',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية',
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='سعر الوحدة',
    )
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='إجمالي السعر',
    )
    unit = models.CharField(
        max_length=50,
        default='piece',
        verbose_name='الوحدة',
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
        ordering = ['id']
        verbose_name = 'بند تصدير'
        verbose_name_plural = 'بنود التصدير'

    def __str__(self):
        return f'{self.description} - {self.export_order.order_number}'

    def save(self, *args, **kwargs):
        """Auto-calculate total_price before saving."""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class CustomsDeclaration(models.Model):
    """إقرار جمركي - Customs declaration for import/export processing."""

    DECLARATION_TYPE_CHOICES = (
        ('import', 'استيراد'),
        ('export', 'تصدير'),
        ('transit', 'عبور'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('submitted', 'مقدم'),
        ('cleared', 'مخلى'),
        ('hold', 'معلق'),
        ('rejected', 'مرفوض'),
    )

    declaration_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الإقرار',
    )
    import_order = models.ForeignKey(
        ImportOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customs_declarations',
        verbose_name='أمر الاستيراد',
    )
    export_order = models.ForeignKey(
        ExportOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customs_declarations',
        verbose_name='أمر التصدير',
    )
    declaration_type = models.CharField(
        max_length=20,
        choices=DECLARATION_TYPE_CHOICES,
        verbose_name='نوع الإقرار',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    submitted_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التقديم',
    )
    cleared_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التخليص',
    )
    declared_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='القيمة المصرّح بها',
    )
    duties_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مبلغ الرسوم',
    )
    taxes_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مبلغ الضرائب',
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
        related_name='customs_declarations_created',
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
        verbose_name = 'إقرار جمركي'
        verbose_name_plural = 'الإقرارات الجمركية'

    def __str__(self):
        return f'{self.declaration_number} - {self.get_declaration_type_display()} ({self.get_status_display()})'
