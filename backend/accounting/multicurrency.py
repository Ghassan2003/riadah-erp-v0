"""
Multi-Branch and Multi-Currency support for the Accounting module.
Provides Branch management, Currency definitions, historical Exchange Rates,
and extension models for tagging Journal Entries and Transactions to branches/currencies.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from accounting.models import JournalEntry, Transaction


def _today():
    return timezone.now().date()


# =============================================
# Branch Model
# =============================================

class Branch(models.Model):
    """
    Branch / الفرع - represents a company branch or subsidiary.
    Each branch can have its own default currency and manager.
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز الفرع',
        db_index=True,
        help_text='رمز فريد للفرع (مثال: HQ، BR-001)',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم الفرع',
        help_text='اسم الفرع باللغة العربية',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الفرع (إنجليزي)',
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
    country = models.CharField(
        max_length=100,
        default='السعودية',
        verbose_name='الدولة',
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='رقم الهاتف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    is_headquarters = models.BooleanField(
        default=False,
        verbose_name='المقر الرئيسي',
        help_text='يُشير إلى أن هذا الفرع هو المقر الرئيسي للشركة',
    )
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches',
        verbose_name='مدير الفرع',
        help_text='المستخدم المسؤول عن إدارة الفرع',
    )
    default_currency = models.ForeignKey(
        'accounting.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branches',
        verbose_name='العملة الافتراضية',
        help_text='العملة الافتراضية المستخدمة في هذا الفرع',
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
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    def clean(self):
        """Validate branch constraints."""
        if self.is_headquarters:
            existing_hq = Branch.objects.filter(
                is_headquarters=True,
            ).exclude(pk=self.pk if self.pk else None)
            if existing_hq.exists():
                raise ValidationError(
                    'يوجد بالفعل مقر رئيسي محدد. لا يمكن تعيين أكثر من فرع كمقر رئيسي.'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# =============================================
# Currency Model
# =============================================

class Currency(models.Model):
    """
    Currency / العملة - stores currency definitions with current exchange rates.
    Only one currency can be marked as default (base currency, typically SAR).
    """

    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name='رمز العملة',
        db_index=True,
        help_text='رمز العملة وفق معيار ISO 4217 (مثال: SAR, USD, EUR)',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='اسم العملة',
        help_text='اسم العملة باللغة العربية',
    )
    name_en = models.CharField(
        max_length=100,
        verbose_name='اسم العملة (إنجليزي)',
    )
    symbol = models.CharField(
        max_length=5,
        verbose_name='رمز العملة المختصر',
        help_text='رمز العملة المختصر (مثال: ر.س، $، €)',
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='العملة الأساسية',
        help_text='العملة الأساسية للنظام (يُسمح بعملة أساسية واحدة فقط)',
    )
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal('1.000000'),
        verbose_name='سعر الصرف',
        help_text='سعر الصرف بالنسبة للعملة الأساسية',
    )
    rate_date = models.DateField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث لسعر الصرف',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة',
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
        verbose_name = 'عملة'
        verbose_name_plural = 'العملات'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name} ({self.symbol})'

    def clean(self):
        """Validate that only one currency can be the default."""
        if self.is_default:
            existing_default = Currency.objects.filter(
                is_default=True,
            ).exclude(pk=self.pk if self.pk else None)
            if existing_default.exists():
                raise ValidationError(
                    'يوجد بالفعل عملة أساسية محددة. لا يمكن تعيين أكثر من عملة كعملة أساسية.'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# =============================================
# Exchange Rate History
# =============================================

class ExchangeRate(models.Model):
    """
    ExchangeRate / سجل أسعار الصرف - stores historical exchange rates
    for tracking rate changes over time.
    """

    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='exchange_rates',
        verbose_name='العملة',
    )
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        verbose_name='سعر الصرف',
        help_text='سعر الصرف بالنسبة للعملة الأساسية',
    )
    date = models.DateField(
        verbose_name='تاريخ السريان',
        db_index=True,
        help_text='التاريخ الذي يُسري فيه هذا السعر',
    )
    source = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='مصدر السعر',
        help_text='مصدر سعر الصرف (مثال: SAMA، يدوي)',
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
        verbose_name = 'سجل سعر صرف'
        verbose_name_plural = 'سجل أسعار الصرف'
        ordering = ['-date', '-created_at']
        unique_together = ('currency', 'date')
        indexes = [
            models.Index(fields=['currency', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f'{self.currency.code} - {self.rate} ({self.date})'


# =============================================
# Journal Entry Branch Extension
# =============================================

class JournalEntryBranch(models.Model):
    """
    JournalEntryBranch / فرع القيد - links a JournalEntry to a Branch
    without modifying the original accounting.models.JournalEntry.
    """

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='branch_info',
        verbose_name='قيد اليومية',
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries',
        verbose_name='الفرع',
        help_text='الفرع المرتبط بقيد اليومية',
    )

    class Meta:
        verbose_name = 'فرع القيد'
        verbose_name_plural = 'فروع القيود'
        ordering = ['id']

    def __str__(self):
        branch_name = self.branch.name if self.branch else 'غير محدد'
        return f'{self.journal_entry.entry_number} - {branch_name}'


# =============================================
# Transaction Currency Extension
# =============================================

class TransactionCurrency(models.Model):
    """
    TransactionCurrency / عملة الحركة - extends Transaction with multi-currency
    support, storing the original currency amount and conversion details.
    """

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='currency_info',
        verbose_name='الحركة المالية',
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='currency_transactions',
        verbose_name='العملة',
        help_text='العملة الأصلية للحركة',
    )
    original_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ الأصلي',
        help_text='المبلغ بالعملة الأصلية',
    )
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal('1.000000'),
        verbose_name='سعر الصرف المُستخدم',
        help_text='سعر الصرف المُستخدم للتحويل إلى العملة الأساسية',
    )
    converted_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ المحوّل',
        help_text='المبلغ بالعملة الأساسية (ريال سعودي)',
    )

    class Meta:
        verbose_name = 'عملة الحركة'
        verbose_name_plural = 'عملات الحركات'
        ordering = ['id']

    def __str__(self):
        currency_code = self.currency.code if self.currency else '---'
        return (
            f'{self.transaction} | {currency_code} '
            f'{self.original_amount} → {self.converted_amount} ر.س'
        )


# =============================================
# Utility Functions
# =============================================

def convert_currency(amount, from_currency_code, to_currency_code, date=None):
    """
    Convert an amount from one currency to another using historical exchange rates.

    Args:
        amount: The amount to convert (Decimal or numeric).
        from_currency_code: Source currency ISO code (e.g., 'USD').
        to_currency_code: Target currency ISO code (e.g., 'SAR').
        date: The date to use for the exchange rate. Defaults to today.

    Returns:
        Decimal: The converted amount rounded to 2 decimal places.

    Raises:
        ValueError: If either currency code is not found or inactive.
    """
    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('المبلغ المُدخل غير صالح')

    if from_currency_code == to_currency_code:
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if date is None:
        date = _today()

    from_rate = get_exchange_rate(from_currency_code, date)
    to_rate = get_exchange_rate(to_currency_code, date)

    # Convert: amount in from_currency → base currency → to_currency
    base_amount = amount * from_rate
    converted = base_amount / to_rate if to_rate != 0 else Decimal('0')

    return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_exchange_rate(currency_code, date=None):
    """
    Get the exchange rate for a specific currency and date.

    Looks up the historical ExchangeRate record for the given date first.
    If no historical record exists, falls back to the currency's current rate.

    Args:
        currency_code: ISO 4217 currency code (e.g., 'SAR', 'USD').
        date: The date to look up. Defaults to today.

    Returns:
        Decimal: Exchange rate relative to the base currency.

    Raises:
        ValueError: If the currency code is not found or inactive.
    """
    try:
        currency = Currency.objects.get(code=currency_code, is_active=True)
    except Currency.DoesNotExist:
        raise ValueError(f'العملة "{currency_code}" غير موجودة أو غير نشطة')

    # Base currency always has a rate of 1
    if currency.is_default:
        return Decimal('1.000000')

    if date is None:
        date = _today()

    # Try to find historical rate for the exact date
    try:
        historical = ExchangeRate.objects.filter(
            currency=currency,
            date=date,
        ).latest('created_at')
        return historical.rate
    except ExchangeRate.DoesNotExist:
        pass

    # Fall back to the currency's current stored rate
    return currency.exchange_rate


def update_exchange_rate(currency_code, rate, source='manual'):
    """
    Update the exchange rate for a currency and create a history record.

    Args:
        currency_code: ISO 4217 currency code.
        rate: New exchange rate (numeric or Decimal).
        source: Source of the rate (e.g., 'SAMA', 'manual').

    Returns:
        tuple: (Currency instance, ExchangeRate instance)

    Raises:
        ValueError: If the currency is not found, inactive, or is the default currency.
    """
    try:
        rate = Decimal(str(rate))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('سعر الصرف المُدخل غير صالح')

    if rate <= 0:
        raise ValueError('سعر الصرف يجب أن يكون أكبر من صفر')

    try:
        currency = Currency.objects.get(code=currency_code, is_active=True)
    except Currency.DoesNotExist:
        raise ValueError(f'العملة "{currency_code}" غير موجودة أو غير نشطة')

    if currency.is_default:
        raise ValueError('لا يمكن تحديث سعر صرف العملة الأساسية (دائماً 1.0)')

    today = _today()

    # Create or update historical record
    history, created = ExchangeRate.objects.update_or_create(
        currency=currency,
        date=today,
        defaults={
            'rate': rate,
            'source': source,
        },
    )

    # Update the currency's current rate
    currency.exchange_rate = rate
    currency.save(update_fields=['exchange_rate', 'updated_at'])

    return currency, history


def get_branch_accounts(branch_id):
    """
    Get all accounts that have transactions associated with a specific branch.

    This looks up all journal entries tagged to the given branch and returns
    the distinct set of accounts that have been used in those entries.

    Args:
        branch_id: Primary key of the Branch.

    Returns:
        QuerySet: Distinct Account instances used by the branch.

    Raises:
        ValueError: If the branch does not exist.
    """
    from accounting.models import Account

    try:
        branch = Branch.objects.get(pk=branch_id)
    except Branch.DoesNotExist:
        raise ValueError(f'الفرع برقم معرّف {branch_id} غير موجود')

    journal_entry_ids = JournalEntryBranch.objects.filter(
        branch=branch,
    ).values_list('journal_entry_id', flat=True)

    account_ids = Transaction.objects.filter(
        journal_entry_id__in=journal_entry_ids,
    ).values_list('account_id', flat=True).distinct()

    return Account.objects.filter(pk__in=account_ids)


def create_branch_journal_entry(branch, data, user):
    """
    Create a journal entry tagged to a specific branch.

    Creates a new JournalEntry with its associated Transactions,
    links it to the branch via JournalEntryBranch, and optionally
    records multi-currency information on each Transaction.

    Args:
        branch: Branch instance to associate the entry with.
        data: dict with keys:
            - description (str): Entry description.
            - entry_type (str): One of 'manual', 'sale', 'payment', 'adjustment'.
            - entry_date (date, optional): Date for the entry.
            - reference (str, optional): External reference.
            - lines (list of dict): Each dict has:
                - account_id (int): Account primary key.
                - transaction_type (str): 'debit' or 'credit'.
                - amount (Decimal): Amount in base currency.
                - description (str, optional): Transaction line description.
                - currency_code (str, optional): ISO code if in a foreign currency.
            - currency_code (str, optional): Default currency for all lines.
        user: User instance creating the entry (set as created_by).

    Returns:
        JournalEntry: The newly created (but unposted) journal entry.

    Raises:
        ValueError: If data is invalid or currencies are not found.
    """
    from accounting.models import Account

    if not branch or not branch.is_active:
        raise ValueError('الفرع غير محدد أو غير نشط')

    description = data.get('description', '').strip()
    if not description:
        raise ValueError('وصف القيد مطلوب')

    entry_type = data.get('entry_type', 'manual')
    entry_date = data.get('entry_date', _today())
    reference = data.get('reference', '')
    lines = data.get('lines', [])

    if not lines:
        raise ValueError('يجب أن يحتوي القيد على حركة واحدة على الأقل')

    # Validate lines balance
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    for line in lines:
        account_id = line.get('account_id')
        txn_type = line.get('transaction_type')
        amount = line.get('amount')

        if not account_id:
            raise ValueError('كل حركة يجب أن تحتوي على حساب')
        if txn_type not in ('debit', 'credit'):
            raise ValueError('نوع الحركة يجب أن يكون "مدين" أو "دائن"')
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f'المبلغ غير صالح في الحركة: {line}')

        if amount <= 0:
            raise ValueError('المبلغ يجب أن يكون أكبر من صفر')

        if txn_type == 'debit':
            total_debit += amount
        else:
            total_credit += amount

    if total_debit != total_credit:
        raise ValueError(
            f'المجاميع غير متساوية: المدين = {total_debit}، الدائن = {total_credit}'
        )

    default_currency_code = data.get('currency_code')

    with transaction.atomic():
        # Create the journal entry
        je = JournalEntry(
            description=description,
            entry_type=entry_type,
            entry_date=entry_date,
            reference=reference,
            created_by=user,
        )
        je.save()

        # Create transaction lines
        for line in lines:
            txn = Transaction(
                journal_entry=je,
                account_id=line['account_id'],
                transaction_type=line['transaction_type'],
                amount=Decimal(str(line['amount'])),
                description=line.get('description', ''),
            )
            txn.save()

            # Handle multi-currency if specified
            line_currency_code = line.get('currency_code') or default_currency_code
            if line_currency_code:
                try:
                    original_amount = Decimal(str(line['amount']))
                    rate = get_exchange_rate(line_currency_code, entry_date)
                    currency = Currency.objects.get(
                        code=line_currency_code,
                        is_active=True,
                    )

                    # If the currency is not the base currency, recalculate
                    if not currency.is_default and rate != Decimal('1'):
                        # original_amount is in the foreign currency;
                        # the amount stored in Transaction is the base-currency amount.
                        # Derive original from base: original = base / rate
                        txn_currency_info = TransactionCurrency(
                            transaction=txn,
                            currency=currency,
                            original_amount=(original_amount / rate).quantize(
                                Decimal('0.01'), rounding=ROUND_HALF_UP
                            ),
                            exchange_rate=rate,
                            converted_amount=original_amount,
                        )
                    else:
                        txn_currency_info = TransactionCurrency(
                            transaction=txn,
                            currency=currency,
                            original_amount=original_amount,
                            exchange_rate=Decimal('1.000000'),
                            converted_amount=original_amount,
                        )
                    txn_currency_info.save()

                except Currency.DoesNotExist:
                    # Non-critical: just skip currency tagging
                    pass

        # Link to branch
        JournalEntryBranch.objects.create(
            journal_entry=je,
            branch=branch,
        )

    return je
