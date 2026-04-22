"""
Payment Models for ERP System.
Manages Payment Accounts, Financial Transactions, Cheques, and Reconciliations.
"""

from django.db import models
from django.utils import timezone


# =============================================
# PaymentAccount Model
# =============================================

class PaymentAccount(models.Model):
    """Financial account model for managing bank accounts, cash boxes, and mobile wallets."""

    ACCOUNT_TYPE_CHOICES = (
        ('bank_account', 'حساب بنكي'),
        ('cash_box', 'صندوق نقدي'),
        ('mobile_wallet', 'محفظة موبايل'),
    )

    account_name = models.CharField(
        max_length=200,
        verbose_name='اسم الحساب',
        db_index=True,
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        verbose_name='نوع الحساب',
        db_index=True,
    )
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='اسم البنك',
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='رقم الحساب',
    )
    iban = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='الآيبان',
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name='العملة',
    )
    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الرصيد الحالي',
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='افتراضي',
        db_index=True,
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
        verbose_name = 'حساب مالي'
        verbose_name_plural = 'الحسابات المالية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.account_name} ({self.get_account_type_display()})'

    def save(self, *args, **kwargs):
        if self.is_default:
            PaymentAccount.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


# =============================================
# FinancialTransaction Model
# =============================================

class FinancialTransaction(models.Model):
    """Financial transaction model for receipts, payments, transfers, and adjustments."""

    TRANSACTION_TYPE_CHOICES = (
        ('receipt', 'إيصال قبض'),
        ('payment', 'دفع'),
        ('transfer', 'تحويل'),
        ('adjustment', 'تسوية يدوية'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدي'),
        ('cheque', 'شيك'),
        ('card', 'بطاقة'),
        ('mobile', 'موبايل'),
    )

    STATUS_CHOICES = (
        ('completed', 'مكتمل'),
        ('pending', 'قيد الانتظار'),
        ('cancelled', 'ملغي'),
    )

    REFERENCE_TYPE_CHOICES = (
        ('invoice', 'فاتورة'),
        ('salary', 'راتب'),
        ('loan', 'قرض'),
        ('purchase', 'مشتريات'),
        ('sale', 'مبيعات'),
        ('other', 'أخرى'),
    )

    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم العملية',
        db_index=True,
        editable=False,
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='نوع العملية',
        db_index=True,
    )
    account = models.ForeignKey(
        PaymentAccount,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name='الحساب',
    )
    to_account = models.ForeignKey(
        PaymentAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transfers',
        verbose_name='حساب المستلم',
        help_text='يُستخدم عند التحويل بين الحسابات',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name='العملة',
    )
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        default='',
        choices=REFERENCE_TYPE_CHOICES,
        verbose_name='نوع المرجع',
    )
    reference_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='رقم المرجع',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='العميل',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='المورد',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    transaction_date = models.DateField(
        verbose_name='تاريخ العملية',
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='طريقة الدفع',
    )
    cheque_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='رقم الشيك',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='الحالة',
        db_index=True,
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
        verbose_name = 'عملية مالية'
        verbose_name_plural = 'العمليات المالية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_number} - {self.get_transaction_type_display()} - {self.amount}'

    def generate_transaction_number(self):
        """Generate a unique transaction number: TRX-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_trx = FinancialTransaction.objects.filter(
            transaction_number__startswith=f'TRX-{today}'
        ).order_by('-transaction_number').first()

        if last_trx:
            try:
                seq = int(last_trx.transaction_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'TRX-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)


# =============================================
# Cheque Model
# =============================================

class Cheque(models.Model):
    """Cheque model for managing incoming and outgoing cheques."""

    CHEQUE_TYPE_CHOICES = (
        ('incoming', 'شيك وارد'),
        ('outgoing', 'شيك صادر'),
    )

    STATUS_CHOICES = (
        ('received', 'مستلم'),
        ('deposited', 'مودع'),
        ('cleared', 'مصروف'),
        ('bounced', 'مرتجع'),
        ('cancelled', 'ملغي'),
    )

    cheque_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الشيك',
        db_index=True,
    )
    bank_name = models.CharField(
        max_length=200,
        verbose_name='اسم البنك',
    )
    branch_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='اسم الفرع',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
        db_index=True,
    )
    payer_name = models.CharField(
        max_length=200,
        verbose_name='اسم المحرر',
    )
    payee_name = models.CharField(
        max_length=200,
        verbose_name='اسم المستفيد',
    )
    cheque_type = models.CharField(
        max_length=20,
        choices=CHEQUE_TYPE_CHOICES,
        verbose_name='نوع الشيك',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='received',
        verbose_name='الحالة',
        db_index=True,
    )
    transaction = models.ForeignKey(
        FinancialTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cheques',
        verbose_name='العملية المالية',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cheques',
        verbose_name='العميل',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cheques',
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
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'شيك'
        verbose_name_plural = 'الشيكات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cheque_number} - {self.payer_name} - {self.amount}'


# =============================================
# Reconciliation Model
# =============================================

class Reconciliation(models.Model):
    """Account reconciliation model for balancing system and actual balances."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('reconciled', 'متوازن'),
        ('discrepancy', 'فارق'),
    )

    reconciliation_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم التسوية',
        db_index=True,
        editable=False,
    )
    account = models.ForeignKey(
        PaymentAccount,
        on_delete=models.CASCADE,
        related_name='reconciliations',
        verbose_name='الحساب',
    )
    period_start = models.DateField(
        verbose_name='بداية الفترة',
    )
    period_end = models.DateField(
        verbose_name='نهاية الفترة',
    )
    system_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='رصيد النظام',
    )
    actual_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الرصيد الفعلي',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    reconciled_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='بواسطة',
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
        verbose_name = 'تسوية'
        verbose_name_plural = 'التسويات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reconciliation_number} - {self.account.account_name}'

    def generate_reconciliation_number(self):
        """Generate a unique reconciliation number: REC-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_rec = Reconciliation.objects.filter(
            reconciliation_number__startswith=f'REC-{today}'
        ).order_by('-reconciliation_number').first()

        if last_rec:
            try:
                seq = int(last_rec.reconciliation_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'REC-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.reconciliation_number:
            self.reconciliation_number = self.generate_reconciliation_number()
        if self.system_balance == self.actual_balance:
            self.status = 'reconciled'
        elif self.status == 'reconciled' and self.system_balance != self.actual_balance:
            self.status = 'discrepancy'
        super().save(*args, **kwargs)

    @property
    def difference(self):
        return self.actual_balance - self.system_balance
