from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
import datetime


class POSShift(models.Model):
    """نموذج الوردية - Cashier Shift"""
    STATUS_CHOICES = [
        ('open', 'مفتوحة'),
        ('closed', 'مغلقة'),
    ]

    shift_number = models.CharField(
        max_length=50, unique=True, verbose_name='رقم الوردية'
    )
    cashier = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='pos_shifts', verbose_name='الكاشير'
    )
    start_time = models.DateTimeField(
        auto_now_add=True, verbose_name='وقت البدء'
    )
    end_time = models.DateTimeField(
        null=True, blank=True, verbose_name='وقت الانتهاء'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='open', verbose_name='الحالة'
    )
    opening_cash = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المبلغ الافتتاحي'
    )
    closing_cash = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المبلغ النهائي'
    )
    expected_cash = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المبلغ المتوقع',
        help_text='المبلغ الافتتاحي + مبيعات نقدية - المردودات النقدية'
    )
    difference = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='الفرق',
        help_text='المبلغ النهائي - المبلغ المتوقع'
    )
    total_sales = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='إجمالي المبيعات'
    )
    total_transactions = models.IntegerField(
        default=0, verbose_name='عدد العمليات'
    )
    total_refunds = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='إجمالي المردودات'
    )
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'وردية'
        verbose_name_plural = 'الورديات'

    def __str__(self):
        return f"{self.shift_number} - {self.cashier.get_full_name() or self.cashier.username}"

    def compute_expected_cash(self):
        """حساب المبلغ المتوقع في الصندوق"""
        cash_sales = self.sales.filter(
            payment_method='cash', status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        cash_refunds = self.refunds.filter(
            refund_method='cash'
        ).aggregate(total=Sum('refund_amount'))['total'] or 0

        return self.opening_cash + cash_sales - cash_refunds

    def close_shift(self, closing_cash, notes=''):
        """إغلاق الوردية وحساب الفرق"""
        self.end_time = timezone.now()
        self.status = 'closed'
        self.closing_cash = closing_cash
        self.expected_cash = self.compute_expected_cash()
        self.difference = self.closing_cash - self.expected_cash
        self.notes = notes
        self.save()


class POSSale(models.Model):
    """نموذج عملية البيع - Sale Transaction"""
    RECEIPT_STATUS_CHOICES = [
        ('completed', 'مكتملة'),
        ('voided', 'ملغاة'),
        ('refunded', 'مستردة'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقدي'),
        ('card', 'بطاقة'),
        ('online', 'إلكتروني'),
        ('mixed', 'مختلط'),
    ]

    receipt_number = models.CharField(
        max_length=50, unique=True, verbose_name='رقم الإيصال'
    )
    shift = models.ForeignKey(
        POSShift, on_delete=models.CASCADE,
        related_name='sales', verbose_name='الوردية'
    )
    customer = models.ForeignKey(
        'sales.Customer', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pos_sales', verbose_name='العميل'
    )
    items = models.JSONField(
        default=list, verbose_name='العناصر',
        help_text='[{product_id, name, quantity, unit_price, discount, vat, total}]'
    )
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المجموع الفرعي'
    )
    discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='مبلغ الخصم'
    )
    vat_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='ضريبة القيمة المضافة (15%)'
    )
    total_amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name='الإجمالي'
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES,
        default='cash', verbose_name='طريقة الدفع'
    )
    cash_received = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المبلغ المستلم'
    )
    change_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='الباقي'
    )
    card_last_four = models.CharField(
        max_length=4, blank=True, verbose_name='آخر 4 أرقام البطاقة'
    )
    status = models.CharField(
        max_length=20, choices=RECEIPT_STATUS_CHOICES,
        default='completed', verbose_name='الحالة'
    )
    void_reason = models.CharField(
        max_length=500, blank=True, verbose_name='سبب الإلغاء'
    )
    voided_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='ألغى بواسطة'
    )
    voided_at = models.DateTimeField(
        null=True, blank=True, verbose_name='وقت الإلغاء'
    )
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عملية بيع'
        verbose_name_plural = 'عمليات البيع'

    def __str__(self):
        return f"{self.receipt_number} - {self.total_amount}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()

        # حساب ضريبة القيمة المضافة (15%)
        if not self.vat_amount or kwargs.pop('_skip_vat', False):
            taxable = self.subtotal - self.discount_amount
            self.vat_amount = round(taxable * 0.15, 2)

        super().save(*args, **kwargs)

    def _generate_receipt_number(self):
        """توليد رقم إيصال فريد - RCP-XXXXXXX (7 أرقام)"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = 'RCP'
        last_sale = POSSale.objects.filter(
            receipt_number__startswith=f'{prefix}-{today}'
        ).order_by('-receipt_number').first()

        if last_sale:
            # Extract the sequence number
            try:
                last_seq = int(last_sale.receipt_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1

        return f'{prefix}-{str(new_seq).zfill(7)}'

    def void_sale(self, voided_by, reason=''):
        """إلغاء عملية البيع"""
        self.status = 'voided'
        self.void_reason = reason
        self.voided_by = voided_by
        self.voided_at = timezone.now()
        self.save()


class POSRefund(models.Model):
    """نموذج الإرجاع/الاسترداد - Refund"""
    REFUND_METHOD_CHOICES = [
        ('cash', 'نقدي'),
        ('card', 'بطاقة'),
        ('original', 'طريقة الدفع الأصلية'),
    ]

    refund_number = models.CharField(
        max_length=50, unique=True, verbose_name='رقم الإرجاع'
    )
    sale = models.ForeignKey(
        POSSale, on_delete=models.CASCADE,
        related_name='refunds', verbose_name='عملية البيع'
    )
    shift = models.ForeignKey(
        POSShift, on_delete=models.CASCADE,
        related_name='refunds', verbose_name='الوردية'
    )
    items = models.JSONField(
        default=list, verbose_name='العناصر المستردة'
    )
    refund_amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name='مبلغ الإرجاع'
    )
    refund_method = models.CharField(
        max_length=20, choices=REFUND_METHOD_CHOICES,
        default='original', verbose_name='طريقة الإرجاع'
    )
    reason = models.CharField(
        max_length=500, verbose_name='سبب الإرجاع'
    )
    processed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, verbose_name='تم بواسطة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إرجاع'
        verbose_name_plural = 'الإرجاعات'

    def __str__(self):
        return f"{self.refund_number} - {self.refund_amount}"

    def save(self, *args, **kwargs):
        if not self.refund_number:
            self.refund_number = self._generate_refund_number()
        super().save(*args, **kwargs)

    def _generate_refund_number(self):
        """توليد رقم إرجاع فريد - REF-YYYYMMDD-XXXX"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = 'REF'
        last_refund = POSRefund.objects.filter(
            refund_number__startswith=f'{prefix}-{today}'
        ).order_by('-refund_number').first()

        if last_refund:
            try:
                last_seq = int(last_refund.refund_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1

        return f'{prefix}-{today}-{str(new_seq).zfill(4)}'


class POSHoldOrder(models.Model):
    """نموذج الطلب المعلق - Hold Order"""

    hold_number = models.CharField(
        max_length=50, unique=True, verbose_name='رقم التعليق'
    )
    shift = models.ForeignKey(
        POSShift, on_delete=models.CASCADE,
        related_name='holds', verbose_name='الوردية'
    )
    customer_name = models.CharField(
        max_length=200, blank=True, verbose_name='اسم العميل'
    )
    items = models.JSONField(
        default=list, verbose_name='العناصر'
    )
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='المجموع الفرعي'
    )
    discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='مبلغ الخصم'
    )
    vat_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='ضريبة القيمة المضافة'
    )
    total_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='الإجمالي'
    )
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    is_recovered = models.BooleanField(
        default=False, verbose_name='تم الاسترجاع'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'طلب معلق'
        verbose_name_plural = 'الطلبات المعلقة'

    def __str__(self):
        return f"{self.hold_number} - {self.customer_name or 'بدون اسم'}"

    def save(self, *args, **kwargs):
        if not self.hold_number:
            self.hold_number = self._generate_hold_number()
        super().save(*args, **kwargs)

    def _generate_hold_number(self):
        """توليد رقم تعليق فريد - HOLD-XXXX"""
        prefix = 'HOLD'
        last_hold = POSHoldOrder.objects.filter(
            hold_number__startswith=f'{prefix}-'
        ).order_by('-hold_number').first()

        if last_hold:
            try:
                last_seq = int(last_hold.hold_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1

        return f'{prefix}-{str(new_seq).zfill(4)}'


class CashDrawerTransaction(models.Model):
    """نموذج حركة الصندوق - Cash Drawer Transaction"""
    TRANSACTION_TYPE_CHOICES = [
        ('opening', 'فتح'),
        ('closing', 'إغلاق'),
        ('cash_in', 'إيداع نقدي'),
        ('cash_out', 'سحب نقدي'),
        ('paid_in', 'دفع داخلي'),
        ('paid_out', 'دفع خارجي'),
    ]

    shift = models.ForeignKey(
        POSShift, on_delete=models.CASCADE,
        related_name='drawer_transactions', verbose_name='الوردية'
    )
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='نوع الحركة'
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name='المبلغ'
    )
    description = models.CharField(
        max_length=500, verbose_name='الوصف'
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, verbose_name='بواسطة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'حركة صندوق'
        verbose_name_plural = 'حركات الصندوق'

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"
