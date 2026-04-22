from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone

from sales.models import SalesOrder, Customer
from purchases.models import Supplier
from inventory.models import Product
from users.models import User


class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('sales', 'فاتورة مبيعات'),
        ('purchase', 'فاتورة مشتريات'),
        ('credit_note', 'إشعار دائن'),
        ('debit_note', 'إشعار مدين'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'غير مدفوعة'),
        ('partially_paid', 'مدفوعة جزئياً'),
        ('paid', 'مدفوعة'),
        ('overdue', 'متأخرة'),
        ('cancelled', 'ملغاة'),
    ]

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('sent', 'مرسلة'),
        ('accepted', 'مقبولة'),
        ('partially_paid', 'مدفوعة جزئياً'),
        ('paid', 'مدفوعة'),
        ('cancelled', 'ملغاة'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الفاتورة')
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, verbose_name='نوع الفاتورة')
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices', verbose_name='أمر البيع'
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices', verbose_name='العميل'
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices', verbose_name='المورد'
    )
    issue_date = models.DateField(verbose_name='تاريخ الإصدار')
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='المجموع الفرعي')

    discount_type = models.CharField(max_length=20, choices=[('percentage', 'نسبة مئوية'), ('fixed', 'مبلغ ثابت')], default='percentage', verbose_name='نوع الخصم')
    discount_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='قيمة الخصم')
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='مبلغ الخصم')

    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), verbose_name='نسبة ضريبة القيمة المضافة')
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='مبلغ الضريبة')

    total_after_discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='الإجمالي بعد الخصم')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='الإجمالي النهائي')

    currency = models.CharField(max_length=3, default='SAR', verbose_name='العملة')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid', verbose_name='حالة الدفع')
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='المبلغ المدفوع')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')

    tax_number = models.CharField(max_length=30, blank=True, verbose_name='الرقم الضريبي (العميل/المورد)')
    company_tax_number = models.CharField(max_length=30, default='300000000000003', verbose_name='الرقم الضريبي للشركة')

    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    terms_conditions = models.TextField(blank=True, verbose_name='الشروط والأحكام')

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_invoices', verbose_name='أنشئ بواسطة'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'

    def __str__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        # Auto-generate invoice number if blank
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()

        # Compute discount amount
        if self.discount_type == 'percentage' and self.discount_value:
            self.discount_amount = (self.subtotal * self.discount_value / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        elif self.discount_type == 'fixed':
            self.discount_amount = self.discount_value
        else:
            self.discount_amount = Decimal('0')

        # Compute total after discount
        self.total_after_discount = (self.subtotal - self.discount_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Compute VAT amount
        self.vat_amount = (self.total_after_discount * self.vat_rate / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Compute total amount
        self.total_amount = (self.total_after_discount + self.vat_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        return (self.total_amount - self.paid_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    def _generate_invoice_number(self):
        today = timezone.now().strftime('%Y%m%d')
        prefix = 'INV'
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'{prefix}-{today}'
        ).order_by('-invoice_number').first()

        if last_invoice:
            try:
                last_seq = int(last_invoice.invoice_number.split('-')[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f'{prefix}-{today}-{new_seq:04d}'

    def recalculate_totals(self):
        """Recalculate subtotal from items and then compute all totals."""
        from django.db.models import Sum, F

        items_subtotal = self.items.aggregate(
            total=Sum(F('total'))
        )['total'] or Decimal('0')

        self.subtotal = items_subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.save()


class InvoiceItem(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'نسبة مئوية'),
        ('fixed', 'مبلغ ثابت'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='items', verbose_name='الفاتورة'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='المنتج'
    )
    description = models.CharField(max_length=500, verbose_name='الوصف')
    quantity = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='الكمية')
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='سعر الوحدة')
    unit = models.CharField(max_length=20, default='piece', verbose_name='الوحدة')

    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage', verbose_name='نوع الخصم')
    discount_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), verbose_name='قيمة الخصم')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), verbose_name='نسبة الضريبة')

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='المجموع الفرعي')
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='مبلغ الضريبة')
    total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='الإجمالي')

    class Meta:
        verbose_name = 'بند فاتورة'
        verbose_name_plural = 'بنود الفاتورة'

    def __str__(self):
        return f'{self.description} - {self.invoice.invoice_number}'

    def save(self, *args, **kwargs):
        # Ensure decimal types
        qty = Decimal(str(self.quantity))
        price = Decimal(str(self.unit_price))
        # Line subtotal before discount
        line_subtotal = (qty * price).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Compute line discount
        if self.discount_type == 'percentage' and self.discount_value:
            line_discount = (line_subtotal * self.discount_value / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        elif self.discount_type == 'fixed':
            line_discount = self.discount_value
        else:
            line_discount = Decimal('0')

        # Subtotal after discount
        self.subtotal = (line_subtotal - line_discount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # VAT amount on this line
        self.vat_amount = (self.subtotal * self.vat_rate / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Total for this line
        self.total = (self.subtotal + self.vat_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        super().save(*args, **kwargs)

        # Recalculate parent invoice totals
        if self.invoice:
            self.invoice.recalculate_totals()


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدي'),
        ('cheque', 'شيك'),
        ('card', 'بطاقة'),
        ('online', 'دفع إلكتروني'),
    ]

    payment_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الدفعة')
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='payments', verbose_name='الفاتورة'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='طريقة الدفع')
    payment_date = models.DateField(verbose_name='تاريخ الدفع')
    reference_number = models.CharField(max_length=100, blank=True, verbose_name='رقم المرجع')
    bank_name = models.CharField(max_length=100, blank=True, verbose_name='اسم البنك')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_payments', verbose_name='أنشئ بواسطة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'دفعة'
        verbose_name_plural = 'المدفوعات'

    def __str__(self):
        return self.payment_number

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = self._generate_payment_number()
        super().save(*args, **kwargs)

        # Update invoice paid amount and payment status
        self._update_invoice_payment()

    def delete(self, *args, **kwargs):
        # Reduce invoice paid amount before deleting
        invoice = self.invoice
        super().delete(*args, **kwargs)
        self._reduce_invoice_payment(invoice)

    def _generate_payment_number(self):
        today = timezone.now().strftime('%Y%m%d')
        prefix = 'PAY'
        last_payment = Payment.objects.filter(
            payment_number__startswith=f'{prefix}-{today}'
        ).order_by('-payment_number').first()

        if last_payment:
            try:
                last_seq = int(last_payment.payment_number.split('-')[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f'{prefix}-{today}-{new_seq:04d}'

    def _update_invoice_payment(self):
        """Update invoice paid_amount and payment_status after a payment is created."""
        invoice = self.invoice
        from django.db.models import Sum
        total_paid = invoice.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        invoice.paid_amount = total_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = 'paid'
            if invoice.status not in ('cancelled',):
                invoice.status = 'paid'
        elif invoice.paid_amount > Decimal('0'):
            invoice.payment_status = 'partially_paid'
            if invoice.status not in ('cancelled',):
                invoice.status = 'partially_paid'
        else:
            invoice.payment_status = 'unpaid'

        invoice.save(update_fields=['paid_amount', 'payment_status', 'status', 'updated_at'])

    def _reduce_invoice_payment(self, invoice):
        """Reduce invoice paid_amount after a payment is deleted."""
        from django.db.models import Sum
        total_paid = invoice.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        invoice.paid_amount = total_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = 'paid'
            invoice.status = 'paid'
        elif invoice.paid_amount > Decimal('0'):
            invoice.payment_status = 'partially_paid'
            invoice.status = 'partially_paid'
        else:
            invoice.payment_status = 'unpaid'
            if invoice.status in ('paid', 'partially_paid'):
                invoice.status = 'sent'

        invoice.save(update_fields=['paid_amount', 'payment_status', 'status', 'updated_at'])


class PaymentReminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('first', 'تذكير أول'),
        ('second', 'تذكير ثاني'),
        ('final', 'تذكير نهائي'),
        ('legal', 'إجراء قانوني'),
    ]

    SENT_VIA_CHOICES = [
        ('email', 'بريد إلكتروني'),
        ('sms', 'رسالة نصية'),
        ('whatsapp', 'واتساب'),
        ('manual', 'يدوي'),
    ]

    STATUS_CHOICES = [
        ('sent', 'تم الإرسال'),
        ('pending', 'قيد الانتظار'),
        ('failed', 'فشل'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='reminders', verbose_name='الفاتورة'
    )
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES, verbose_name='نوع التذكير')
    message = models.TextField(verbose_name='الرسالة')
    sent_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')
    sent_via = models.CharField(max_length=20, choices=SENT_VIA_CHOICES, verbose_name='طريقة الإرسال')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'تذكير دفع'
        verbose_name_plural = 'تذكيرات الدفع'

    def __str__(self):
        return f'تذكير - {self.invoice.invoice_number} ({self.get_reminder_type_display()})'
