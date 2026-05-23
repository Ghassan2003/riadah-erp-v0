"""
Accounting models for ERP System - Phase 4.
Provides Chart of Accounts, Journal Entries, and Transactions with
automatic integration with the Sales module.
"""

from django.db import models, transaction
from django.utils import timezone


def _today():
    return timezone.now().date()


# =============================================
# Account Type Choices
# =============================================

class AccountType(models.TextChoices):
    ASSET = 'asset', 'أصول'
    LIABILITY = 'liability', 'خصوم'
    EQUITY = 'equity', 'حقوق ملكية'
    INCOME = 'income', 'إيرادات'
    EXPENSE = 'expense', 'مصروفات'


class Account(models.Model):
    """
    Chart of Accounts - represents each financial account.
    Uses a hierarchical code system (e.g., 1000 for Assets, 1100 for Current Assets).
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز الحساب',
        db_index=True,
        help_text='رمز فريد للحساب (مثال: 1000)',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم الحساب',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الحساب (إنجليزي)',
    )
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        verbose_name='نوع الحساب',
        db_index=True,
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='الحساب الرئيسي',
        help_text='الحساب الأب في الهيكل الهرمي',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    current_balance = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='الرصيد الحالي',
        help_text='الرصيد الحالي للحساب (يُحدّث تلقائياً)',
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
        verbose_name = 'حساب'
        verbose_name_plural = 'الدليل المحاسبي'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def recalculate_balance(self):
        """Recalculate the current balance from all transactions."""
        total_debit = self.transactions.filter(
            transaction_type='debit'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        total_credit = self.transactions.filter(
            transaction_type='credit'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        # For assets and expenses: balance = debit - credit
        # For liabilities, equity, and income: balance = credit - debit
        if self.account_type in (AccountType.ASSET, AccountType.EXPENSE):
            self.current_balance = total_debit - total_credit
        else:
            self.current_balance = total_credit - total_debit

        self.save(update_fields=['current_balance', 'updated_at'])
        return self.current_balance

    def get_children_balances(self):
        """Get total balance from all child accounts."""
        total = 0
        for child in self.children.filter(is_active=True):
            total += child.current_balance
        return total


class JournalEntry(models.Model):
    """
    Journal Entry - represents a complete accounting transaction.
    Every journal entry must have at least two transactions (double-entry).
    The total debits must always equal the total credits.
    """

    ENTRY_TYPE_CHOICES = (
        ('manual', 'يدوي'),
        ('sale', 'عملية بيع'),
        ('payment', 'عملية دفع'),
        ('adjustment', 'تسوية'),
    )

    entry_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم القيد',
        db_index=True,
        editable=False,
    )
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES,
        default='manual',
        verbose_name='نوع القيد',
        db_index=True,
    )
    description = models.CharField(
        max_length=500,
        verbose_name='الوصف',
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المرجع',
        help_text='رقم مرجعي (مثال: رقم أمر البيع)',
    )
    entry_date = models.DateField(
        default=_today,
        verbose_name='تاريخ القيد',
        db_index=True,
    )
    is_posted = models.BooleanField(
        default=False,
        verbose_name='مرحّل',
        help_text='هل تم ترحيل القيد إلى الحسابات',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أنشئ بواسطة',
    )
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries',
        verbose_name='أمر البيع المرتبط',
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
        verbose_name = 'قيد يومية'
        verbose_name_plural = 'قيود اليومية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.entry_number} - {self.description}'

    def generate_entry_number(self):
        """Generate a unique entry number: JE-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_entry = JournalEntry.objects.filter(
            entry_number__startswith=f'JE-{today}'
        ).order_by('-entry_number').first()

        if last_entry:
            try:
                seq = int(last_entry.entry_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'JE-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        """Auto-generate entry number if not set."""
        if not self.entry_number:
            self.entry_number = self.generate_entry_number()
        super().save(*args, **kwargs)

    def validate_balance(self):
        """Ensure total debits equal total credits."""
        transactions = self.transactions.all()
        if not transactions.exists():
            raise ValueError('يجب أن يحتوي القيد على حركة واحدة على الأقل')

        total_debit = sum(t.amount for t in transactions if t.transaction_type == 'debit')
        total_credit = sum(t.amount for t in transactions if t.transaction_type == 'credit')

        if total_debit == 0 and total_credit == 0:
            raise ValueError('يجب أن يكون هناك مبلغ على الأقل')

        if total_debit != total_credit:
            raise ValueError(
                f'المجاميع غير متساوية: المدين = {total_debit}، الدائن = {total_credit}'
            )

    @transaction.atomic
    def post_entry(self):
        """Post the journal entry to update account balances."""
        if self.is_posted:
            raise ValueError('تم ترحيل هذا القيد مسبقاً')

        self.validate_balance()

        # Update account balances
        for txn in self.transactions.all():
            account = txn.account
            if txn.transaction_type == 'debit':
                if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                    account.current_balance += txn.amount
                else:
                    account.current_balance -= txn.amount
            else:  # credit
                if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                    account.current_balance -= txn.amount
                else:
                    account.current_balance += txn.amount
            account.save(update_fields=['current_balance', 'updated_at'])

        self.is_posted = True
        self.save(update_fields=['is_posted', 'updated_at'])

    @transaction.atomic
    def reverse_entry(self):
        """Reverse (cancel) a posted journal entry."""
        if not self.is_posted:
            raise ValueError('لا يمكن إلغاء قيد لم يتم ترحيله')

        # Reverse the balance updates
        for txn in self.transactions.all():
            account = txn.account
            if txn.transaction_type == 'debit':
                if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                    account.current_balance -= txn.amount
                else:
                    account.current_balance += txn.amount
            else:  # credit
                if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                    account.current_balance += txn.amount
                else:
                    account.current_balance -= txn.amount
            account.save(update_fields=['current_balance', 'updated_at'])

        self.is_posted = False
        self.save(update_fields=['is_posted', 'updated_at'])


class Transaction(models.Model):
    """
    Individual debit or credit line within a journal entry.
    Each transaction affects exactly one account.
    """

    TRANSACTION_TYPE_CHOICES = (
        ('debit', 'مدين'),
        ('credit', 'دائن'),
    )

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='قيد اليومية',
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='الحساب',
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='نوع الحركة',
    )
    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ',
        help_text='المبلغ بالريال السعودي',
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='الوصف',
    )

    class Meta:
        verbose_name = 'حركة مالية'
        verbose_name_plural = 'الحركات المالية'
        ordering = ['id']

    def __str__(self):
        return f'{self.journal_entry.entry_number} | {self.account.code} | {self.get_transaction_type_display()} | {self.amount}'

    def clean(self):
        """Validate transaction amount."""
        from django.core.exceptions import ValidationError
        if self.amount <= 0:
            raise ValidationError('المبلغ يجب أن يكون أكبر من صفر')
