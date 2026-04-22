"""
Shipping Models for ERP System.
Manages ShippingMethods, Shipments, ShipmentItems, ShipmentEvents, and DeliveryAttempts.
"""

from django.db import models
from django.utils import timezone


class ShippingMethod(models.Model):
    """طريقة الشحن - Shipping method configuration."""

    COST_TYPE_CHOICES = (
        ('flat_rate', 'مبلغ ثابت'),
        ('weight_based', 'حسب الوزن'),
        ('volume_based', 'حسب الحجم'),
        ('free', 'مجاني'),
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
    carrier = models.CharField(
        max_length=255,
        verbose_name='شركة الشحن',
    )
    tracking_url = models.URLField(
        blank=True,
        verbose_name='رابط التتبع',
    )
    cost_type = models.CharField(
        max_length=20,
        choices=COST_TYPE_CHOICES,
        default='flat_rate',
        verbose_name='نوع التكلفة',
    )
    base_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة الأساسية',
    )
    cost_per_unit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة لكل وحدة',
    )
    estimated_days = models.IntegerField(
        default=0,
        verbose_name='الأيام المقدرة للتوصيل',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
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
        verbose_name = 'طريقة شحن'
        verbose_name_plural = 'طرق الشحن'

    def __str__(self):
        return self.name


class Shipment(models.Model):
    """شحنة - Shipment tracking and management."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('picking', 'قيد التجهيز'),
        ('packed', 'مغلف'),
        ('in_transit', 'قيد الشحن'),
        ('out_for_delivery', 'خارج للتوصيل'),
        ('delivered', 'تم التوصيل'),
        ('returned', 'مرتجع'),
        ('cancelled', 'ملغي'),
    )

    shipment_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم الشحنة',
    )
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments',
        verbose_name='أمر البيع',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.CASCADE,
        related_name='shipments',
        verbose_name='العميل',
    )
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        related_name='shipments',
        verbose_name='طريقة الشحن',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الوزن (كجم)',
    )
    dimensions = models.TextField(
        blank=True,
        default='',
        verbose_name='الأبعاد',
    )
    origin_address = models.TextField(
        verbose_name='عنوان المصدر',
    )
    destination_address = models.TextField(
        verbose_name='عنوان الوجهة',
    )
    tracking_number = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='رقم التتبع',
    )
    estimated_delivery = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='التوصيل المقدر',
    )
    actual_delivery = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التوصيل الفعلي',
    )
    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الشحن',
    )
    insurance_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ التأمين',
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
        verbose_name = 'شحنة'
        verbose_name_plural = 'الشحنات'

    def __str__(self):
        return self.shipment_number


class ShipmentItem(models.Model):
    """بند الشحنة - Individual item within a shipment."""

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الشحنة',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='shipment_items',
        verbose_name='المنتج',
    )
    quantity = models.IntegerField(
        verbose_name='الكمية',
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='سعر الوحدة',
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='الوزن (كجم)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'بند شحنة'
        verbose_name_plural = 'بنود الشحنة'

    def __str__(self):
        return f'{self.shipment.shipment_number} - {self.product}'


class ShipmentEvent(models.Model):
    """حدث الشحنة - Timeline event for shipment tracking."""

    EVENT_TYPE_CHOICES = (
        ('created', 'تم الإنشاء'),
        ('picked', 'تم التجهيز'),
        ('packed', 'تم التغليف'),
        ('shipped', 'تم الشحن'),
        ('in_transit', 'قيد النقل'),
        ('out_for_delivery', 'خارج للتوصيل'),
        ('delivered', 'تم التوصيل'),
        ('returned', 'مرتجع'),
        ('exception', 'استثناء'),
    )

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='الشحنة',
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='نوع الحدث',
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='الموقع',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الحدث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'حدث شحنة'
        verbose_name_plural = 'أحداث الشحنة'

    def __str__(self):
        return f'{self.shipment.shipment_number} - {self.get_event_type_display()}'


class DeliveryAttempt(models.Model):
    """محاولة توصيل - Delivery attempt record."""

    STATUS_CHOICES = (
        ('success', 'ناجح'),
        ('fail', 'فاشل'),
        ('partial', 'جزئي'),
    )

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='delivery_attempts',
        verbose_name='الشحنة',
    )
    attempt_number = models.IntegerField(
        verbose_name='رقم المحاولة',
    )
    attempt_date = models.DateTimeField(
        verbose_name='تاريخ المحاولة',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='الحالة',
    )
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم المستلم',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    signature = models.FileField(
        upload_to='signatures/',
        blank=True,
        verbose_name='التوقيع',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-attempt_date']
        verbose_name = 'محاولة توصيل'
        verbose_name_plural = 'محاولات التوصيل'

    def __str__(self):
        return f'{self.shipment.shipment_number} - محاولة {self.attempt_number}'
