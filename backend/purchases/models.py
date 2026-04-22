"""
Models for the Purchases module: Supplier, PurchaseOrder, PurchaseOrderItem.
Handles supplier management and purchase order processing with inventory integration.
"""

from django.db import models, transaction
from django.utils import timezone
from datetime import date


class Supplier(models.Model):
    """Supplier model for managing vendor information."""

    name = models.CharField(
        max_length=255,
        verbose_name='اسم المورد',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم المورد (إنجليزي)',
    )
    contact_person = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='جهة الاتصال',
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
    address = models.TextField(
        blank=True,
        default='',
        verbose_name='العنوان',
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='الرقم الضريبي',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الرصيد',
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
        verbose_name = 'مورد'
        verbose_name_plural = 'الموردون'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class PurchaseOrder(models.Model):
    """Purchase order model with status tracking and inventory integration."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('received', 'مستلم'),
        ('partial', 'استلام جزئي'),
        ('cancelled', 'ملغي'),
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الأمر',
        db_index=True,
        editable=False,
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='المورد',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    order_date = models.DateField(
        default=date.today,
        verbose_name='تاريخ الأمر',
        db_index=True,
    )
    expected_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستلام المتوقع',
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الإجمالي',
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
        verbose_name = 'أمر شراء'
        verbose_name_plural = 'أوامر الشراء'
        ordering = ['-created_at']
        permissions = [
            ('confirm_order', 'Can confirm purchase orders'),
            ('cancel_order', 'Can cancel purchase orders'),
            ('change_status', 'Can change order status'),
        ]

    def __str__(self):
        return f'{self.order_number} - {self.supplier.name}'

    def generate_order_number(self):
        """Generate a unique order number: PO-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        # Find the last order for today
        last_order = PurchaseOrder.objects.filter(
            order_number__startswith=f'PO-{today}'
        ).order_by('-order_number').first()

        if last_order:
            # Extract the sequence number and increment
            try:
                seq = int(last_order.order_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'PO-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        """Auto-generate order number if not set."""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Recalculate total amount from order items."""
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount', 'updated_at'])
        return total

    @transaction.atomic
    def confirm_order(self):
        """Confirm the order and add inventory quantities (purchases add stock)."""
        if self.status != 'draft':
            raise ValueError('يمكن تأكيد الأوامر في حالة "مسودة" فقط')

        # Add quantities to inventory
        for item in self.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save(update_fields=['quantity', 'updated_at'])

        # Capture unit prices at confirmation time
        for item in self.items.all():
            item.unit_price = item.product.unit_price
            item.subtotal = item.unit_price * item.quantity
            item.save(update_fields=['unit_price', 'subtotal'])

        self.status = 'confirmed'
        self.calculate_total()
        self.save(update_fields=['status', 'total_amount', 'updated_at'])

    @transaction.atomic
    def cancel_order(self):
        """Cancel the order and deduct inventory quantities if confirmed."""
        if self.status not in ('draft', 'confirmed'):
            raise ValueError('يمكن إلغاء الأوامر في حالة "مسودة" أو "مؤكد" فقط')

        # Deduct quantities only if order was confirmed
        if self.status == 'confirmed':
            for item in self.items.all():
                product = item.product
                product.quantity -= item.quantity
                product.save(update_fields=['quantity', 'updated_at'])

        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])

    def change_status(self, new_status):
        """Change order status with validation."""
        valid_transitions = {
            'draft': ['confirmed', 'cancelled'],
            'confirmed': ['received', 'partial', 'cancelled'],
            'partial': ['received', 'cancelled'],
            'received': [],
            'cancelled': [],
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(
                f'لا يمكن الانتقال من "{self.get_status_display()}" إلى '
                f'"{dict(self.STATUS_CHOICES).get(new_status, new_status)}"'
            )

        # Special handling for confirm and cancel
        if new_status == 'confirmed':
            self.confirm_order()
        elif new_status == 'cancelled':
            self.cancel_order()
        else:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])


class PurchaseOrderItem(models.Model):
    """Individual line item within a purchase order."""

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='أمر الشراء',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name='المنتج',
    )
    quantity = models.PositiveIntegerField(
        verbose_name='الكمية',
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='سعر الوحدة',
        help_text='السعر عند إنشاء الأمر',
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الإجمالي الفرعي',
    )
    received_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='الكمية المستلمة',
    )

    class Meta:
        verbose_name = 'بند أمر شراء'
        verbose_name_plural = 'بنود أوامر الشراء'
        unique_together = ('order', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        """Auto-calculate subtotal before saving."""
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
