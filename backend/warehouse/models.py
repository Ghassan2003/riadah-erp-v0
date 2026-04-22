"""
Warehouse Models for ERP System.
Multi-Warehouse Management with stock tracking, transfers, adjustments, and counts.
"""

from django.db import models
from django.utils import timezone


class Warehouse(models.Model):
    """Warehouse model for managing multiple storage locations."""

    name = models.CharField(
        max_length=200,
        verbose_name='اسم المستودع',
        db_index=True,
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز المستودع',
        db_index=True,
        editable=False,
    )
    address = models.TextField(
        blank=True,
        default='',
        verbose_name='العنوان',
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المدينة',
    )
    manager = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        verbose_name='مدير المستودع',
    )
    capacity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='السعة الاستيعابية',
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
        verbose_name = 'مستودع'
        verbose_name_plural = 'المستودعات'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def generate_code(self):
        """Generate a unique warehouse code: WH-XXXX."""
        last_wh = Warehouse.objects.filter(
            code__startswith='WH-'
        ).order_by('-code').first()

        if last_wh:
            try:
                seq = int(last_wh.code.split('-')[1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'WH-{seq:03d}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    @property
    def current_stock_level(self):
        """Total stock quantity across all products in this warehouse."""
        total = self.stocks.aggregate(
            total=models.Sum('quantity')
        )['total']
        return total or 0

    @property
    def utilized_capacity(self):
        """Percentage of capacity utilized."""
        if self.capacity > 0:
            return round((self.current_stock_level / self.capacity) * 100, 1)
        return 0

    @property
    def products_count(self):
        """Number of distinct products stored in this warehouse."""
        return self.stocks.filter(quantity__gt=0).count()


class WarehouseStock(models.Model):
    """Stock level per product per warehouse."""

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name='المستودع',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='warehouse_stocks',
        verbose_name='المنتج',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية',
    )
    reserved_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية المحجوزة',
    )
    min_stock_level = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الحد الأدنى للمخزون',
    )
    max_stock_level = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الحد الأقصى للمخزون',
    )
    last_restock_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر تزويد',
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
        unique_together = ('warehouse', 'product')
        verbose_name = 'رصيد مخزون'
        verbose_name_plural = 'أرصدة المخزون'

    def __str__(self):
        return f'{self.warehouse.code} - {self.product.name}: {self.quantity}'

    @property
    def available_quantity(self):
        """Quantity available after subtracting reserved."""
        return self.quantity - self.reserved_quantity


class StockTransfer(models.Model):
    """Transfer stock between warehouses."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('pending', 'قيد الانتظار'),
        ('in_transit', 'قيد النقل'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    transfer_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم التحويل',
        db_index=True,
        editable=False,
    )
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='transfers_out',
        verbose_name='من مستودع',
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='transfers_in',
        verbose_name='إلى مستودع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_transfers',
        verbose_name='طلب بواسطة',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transfers',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
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
        verbose_name = 'تحويل مخزون'
        verbose_name_plural = 'تحويلات المخزون'

    def __str__(self):
        return f'{self.transfer_number}: {self.from_warehouse.code} → {self.to_warehouse.code}'

    def generate_transfer_number(self):
        """Generate a unique transfer number: TRF-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_trf = StockTransfer.objects.filter(
            transfer_number__startswith=f'TRF-{today}'
        ).order_by('-transfer_number').first()

        if last_trf:
            try:
                seq = int(last_trf.transfer_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'TRF-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            self.transfer_number = self.generate_transfer_number()
        super().save(*args, **kwargs)


class StockTransferItem(models.Model):
    """Line item for a stock transfer."""

    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='التحويل',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج',
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية',
    )
    received_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الكمية المستلمة',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )

    class Meta:
        verbose_name = 'بند تحويل'
        verbose_name_plural = 'بنود التحويل'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class StockAdjustment(models.Model):
    """Stock adjustment record for corrections, damage, loss, etc."""

    REASON_CHOICES = (
        ('damage', 'تلف'),
        ('theft', 'سرقة'),
        ('loss', 'فقدان'),
        ('correction', 'تصحيح'),
        ('count', 'جرد'),
        ('received', 'استلام'),
    )

    adjustment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم التسوية',
        db_index=True,
        editable=False,
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='adjustments',
        verbose_name='المستودع',
    )
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        verbose_name='السبب',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج',
    )
    previous_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية السابقة',
    )
    new_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية الجديدة',
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

    class Meta:
        verbose_name = 'تسوية مخزون'
        verbose_name_plural = 'تسويات المخزون'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.adjustment_number}: {self.product.name} ({self.reason})'

    def generate_adjustment_number(self):
        """Generate a unique adjustment number: ADJ-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_adj = StockAdjustment.objects.filter(
            adjustment_number__startswith=f'ADJ-{today}'
        ).order_by('-adjustment_number').first()

        if last_adj:
            try:
                seq = int(last_adj.adjustment_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'ADJ-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            self.adjustment_number = self.generate_adjustment_number()
        super().save(*args, **kwargs)

    @property
    def difference(self):
        """Difference between new and previous quantity."""
        return self.new_quantity - self.previous_quantity


class StockCount(models.Model):
    """Stock count / inventory audit record."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('adjusted', 'تم التسوية'),
    )

    count_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الجرد',
        db_index=True,
        editable=False,
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='counts',
        verbose_name='المستودع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    counted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='جرده بواسطة',
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت البدء',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الإكمال',
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
        verbose_name = 'جرد مخزون'
        verbose_name_plural = 'جرد المخزون'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.count_number} - {self.warehouse.name} ({self.get_status_display()})'

    def generate_count_number(self):
        """Generate a unique count number: CNT-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_cnt = StockCount.objects.filter(
            count_number__startswith=f'CNT-{today}'
        ).order_by('-count_number').first()

        if last_cnt:
            try:
                seq = int(last_cnt.count_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'CNT-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.count_number:
            self.count_number = self.generate_count_number()
        super().save(*args, **kwargs)


class StockCountItem(models.Model):
    """Line item for a stock count — system vs. counted quantity."""

    count = models.ForeignKey(
        StockCount,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الجرد',
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج',
    )
    system_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية في النظام',
    )
    counted_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الكمية الفعلية',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )

    class Meta:
        verbose_name = 'بند جرد'
        verbose_name_plural = 'بنود الجرد'

    def __str__(self):
        return f'{self.product.name}: نظام={self.system_quantity}, فعلي={self.counted_quantity}'

    @property
    def difference(self):
        """Difference between counted and system quantity."""
        return self.counted_quantity - self.system_quantity
