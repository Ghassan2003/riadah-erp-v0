"""
نظام الإغلاق المحاسبي الدوري - نظام ERP.
يوفر إدارة السنوات المالية والفترات المحاسبية وإجراءات الإقفال
مع إنشاء قيود الإقفال التلقائية ونقل صافي الربح إلى الأرباح المحتجزة.
"""

from django.db import models, transaction
from django.utils import timezone
from decimal import Decimal
import json

from accounting.models import Account, AccountType, JournalEntry, Transaction


# =============================================
# Choice Enums
# =============================================

class PeriodType(models.TextChoices):
    MONTHLY = 'monthly', 'شهري'
    QUARTERLY = 'quarterly', 'ربع سنوي'
    YEARLY = 'yearly', 'سنوي'


class PeriodStatus(models.TextChoices):
    OPEN = 'open', 'مفتوح'
    CLOSING = 'closing', 'قيد الإقفال'
    CLOSED = 'closed', 'مقفل'


class FiscalYearStatus(models.TextChoices):
    OPEN = 'open', 'مفتوح'
    CLOSED = 'closed', 'مقفل'


class ClosureEntryType(models.TextChoices):
    INCOME_CLOSURE = 'income_closure', 'إقفال الإيرادات'
    EXPENSE_CLOSURE = 'expense_closure', 'إقفال المصروفات'
    NET_PROFIT_TRANSFER = 'net_profit_transfer', 'تحويل صافي الربح'


# =============================================
# Fiscal Year Model
# =============================================

class FiscalYear(models.Model):
    """
    السنة المالية - تمثل السنة المالية الكاملة للشركة.
    تحتوي على تواريخ البداية والنهاية وحالة السنة.
    """

    year = models.IntegerField(
        unique=True,
        verbose_name='السنة',
        help_text='السنة المالية (مثال: 2024)',
        db_index=True,
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name='اسم الشركة',
    )
    status = models.CharField(
        max_length=20,
        choices=FiscalYearStatus.choices,
        default=FiscalYearStatus.OPEN,
        verbose_name='الحالة',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_fiscal_years',
        verbose_name='أنشئ بواسطة',
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
        verbose_name = 'سنة مالية'
        verbose_name_plural = 'السنوات المالية'
        ordering = ['-year']

    def __str__(self):
        return f'{self.year} - {self.company_name}'

    def is_closed(self):
        """هل السنة المالية مقفلة."""
        return self.status == FiscalYearStatus.CLOSED


# =============================================
# Fiscal Period Model
# =============================================

class FiscalPeriod(models.Model):
    """
    الفترة المحاسبية - تمثل فترة محاسبية داخل السنة المالية.
    يمكن أن تكون شهرية أو ربع سنوية أو سنوية.
    """

    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='periods',
        verbose_name='السنة المالية',
    )
    year = models.IntegerField(
        verbose_name='السنة',
        help_text='السنة المالية (مثال: 2024)',
        db_index=True,
    )
    period_type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        verbose_name='نوع الفترة',
        db_index=True,
    )
    period_number = models.IntegerField(
        verbose_name='رقم الفترة',
        help_text='رقم الفترة (1-12 للشهري، 1-4 للربع سنوي، 1 للسنوي)',
    )
    period_start = models.DateField(
        verbose_name='بداية الفترة',
        db_index=True,
    )
    period_end = models.DateField(
        verbose_name='نهاية الفترة',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=PeriodStatus.choices,
        default=PeriodStatus.OPEN,
        verbose_name='الحالة',
        db_index=True,
    )
    closed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_periods',
        verbose_name='أُقفل بواسطة',
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإقفال',
    )
    opening_balances = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='أرصدة الافتتاح',
        help_text='أرصدة الحسابات عند بداية الفترة (JSON)',
    )
    closing_balances = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='أرصدة الإقفال',
        help_text='أرصدة الحسابات عند نهاية الفترة (JSON)',
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
        verbose_name = 'فترة محاسبية'
        verbose_name_plural = 'الفترات المحاسبية'
        ordering = ['year', 'period_number']
        unique_together = ['fiscal_year', 'period_number']

    def __str__(self):
        type_display = self.get_period_type_display()
        return f'{self.year} - {type_display} - فترة {self.period_number}'

    def is_closed(self):
        """هل الفترة مقفلة."""
        return self.status == PeriodStatus.CLOSED

    def get_period_label(self):
        """الحصول على تسمية الفترة."""
        if self.period_type == PeriodType.MONTHLY:
            months_ar = [
                'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
            ]
            return months_ar[self.period_number - 1] if 1 <= self.period_number <= 12 else str(self.period_number)
        elif self.period_type == PeriodType.QUARTERLY:
            return f'الربع {self.period_number}'
        return f'السنة {self.year}'


# =============================================
# Closure Entry Model
# =============================================

class ClosureEntry(models.Model):
    """
    قيد الإقفال - يسجّل ما حدث أثناء عملية إقفال الفترة المحاسبية.
    يرتبط بقيد اليومية الذي تم إنشاؤه أثناء الإقفال.
    """

    fiscal_period = models.ForeignKey(
        FiscalPeriod,
        on_delete=models.CASCADE,
        related_name='closure_entries',
        verbose_name='الفترة المحاسبية',
    )
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name='closure_records',
        verbose_name='قيد اليومية',
    )
    entry_type = models.CharField(
        max_length=30,
        choices=ClosureEntryType.choices,
        verbose_name='نوع قيد الإقفال',
        db_index=True,
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    total_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي المبلغ',
        help_text='الإجمالي بالريال السعودي',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'قيد إقفال'
        verbose_name_plural = 'قيود الإقفال'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_entry_type_display()} - {self.fiscal_period}'


# =============================================
# Helper Functions
# =============================================

def _snapshot_balances():
    """
    أخذ لقطة لأرصدة جميع الحسابات النشطة.
    يُرجع قاموس JSON يحتوي على رمز الحساب والرصيد الحالي.
    """
    accounts = Account.objects.filter(is_active=True)
    balances = {}
    for account in accounts:
        balances[str(account.code)] = str(account.current_balance)
    return balances


def _get_retained_earnings_account():
    """
    الحصول على حساب الأرباح المحتجزة (رمز 3200).
    يُنشئ الحساب إذا لم يكن موجوداً.
    """
    account, created = Account.objects.get_or_create(
        code='3200',
        defaults={
            'name': 'الأرباح المحتجزة',
            'name_en': 'Retained Earnings',
            'account_type': AccountType.EQUITY,
            'description': 'الأرباح المحتجزة - يُستخدم في إقفال الفترات المحاسبية',
        },
    )
    return account


# =============================================
# Core Functions
# =============================================

@transaction.atomic
def open_fiscal_year(year, company_name, user):
    """
    فتح سنة مالية جديدة وإنشاء 12 فترة شهرية.

    المعاملات:
        year (int): السنة المالية (مثال: 2024).
        company_name (str): اسم الشركة.
        user (User): المستخدم الذي يقوم بإنشاء السنة المالية.

    العائد:
        FiscalYear: كائن السنة المالية المُنشأة.

    الاستثناءات:
        ValueError: إذا كانت السنة المالية موجودة مسبقاً.
    """
    if FiscalYear.objects.filter(year=year).exists():
        raise ValueError(f'السنة المالية {year} موجودة مسبقاً')

    fiscal_year = FiscalYear.objects.create(
        year=year,
        company_name=company_name,
        start_date=_get_fiscal_year_start(year),
        end_date=_get_fiscal_year_end(year),
        created_by=user,
        notes=f'تم فتح السنة المالية بواسطة {user.get_full_name() or user.username}',
    )

    # إنشاء 12 فترة شهرية
    for month in range(1, 13):
        period_start = _get_month_start(year, month)
        period_end = _get_month_end(year, month)

        FiscalPeriod.objects.create(
            fiscal_year=fiscal_year,
            year=year,
            period_type=PeriodType.MONTHLY,
            period_number=month,
            period_start=period_start,
            period_end=period_end,
            status=PeriodStatus.OPEN,
            opening_balances=_snapshot_balances(),
        )

    return fiscal_year


def _get_fiscal_year_start(year):
    """الحصول على تاريخ بداية السنة المالية (1 يناير)."""
    from datetime import date
    return date(year, 1, 1)


def _get_fiscal_year_end(year):
    """الحصول على تاريخ نهاية السنة المالية (31 ديسمبر)."""
    from datetime import date
    return date(year, 12, 31)


def _get_month_start(year, month):
    """الحصول على تاريخ بداية الشهر."""
    from datetime import date
    return date(year, month, 1)


def _get_month_end(year, month):
    """الحصول على تاريخ نهاية الشهر."""
    from datetime import date
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def validate_period_closable(period):
    """
    التحقق من إمكانية إقفال الفترة المحاسبية.

    المعاملات:
        period (FiscalPeriod): الفترة المحاسبية المراد التحقق منها.

    العائد:
        dict: يحتوي على نتيجة التحقق ('valid': bool, 'errors': list).

    يتحقق مما يلي:
        - الفترة ليست مقفلة مسبقاً.
        - لا توجد قيود يومية غير مرحّلة خلال الفترة.
    """
    errors = []

    # التحقق من أن الفترة ليست مقفلة مسبقاً
    if period.is_closed():
        errors.append(f'الفترة "{period.get_period_label()}" مقفلة مسبقاً')
        return {'valid': False, 'errors': errors}

    # التحقق من وجود قيود غير مرحّلة
    unposted_entries = JournalEntry.objects.filter(
        entry_date__gte=period.period_start,
        entry_date__lte=period.period_end,
        is_posted=False,
    )

    if unposted_entries.exists():
        entry_numbers = list(
            unposted_entries.values_list('entry_number', flat=True)[:10]
        )
        errors.append(
            f'يوجد {unposted_entries.count()} قيد يومية غير مرحّل: {", ".join(entry_numbers)}'
        )

    return {'valid': len(errors) == 0, 'errors': errors}


def get_period_balances(period):
    """
    الحصول على أرصدة جميع الحسابات خلال فترة محاسبية محددة.

    المعاملات:
        period (FiscalPeriod): الفترة المحاسبية.

    العائد:
        dict: يحتوي على أرصدة الحسابات مصنّفة حسب النوع:
            - income: أرصدة حسابات الإيرادات.
            - expense: أرصدة حسابات المصروفات.
            - asset: أرصدة حسابات الأصول.
            - liability: أرصدة حسابات الخصوم.
            - equity: أرصدة حسابات حقوق الملكية.
    """
    accounts = Account.objects.filter(is_active=True)
    balances = {
        'income': [],
        'expense': [],
        'asset': [],
        'liability': [],
        'equity': [],
    }

    for account in accounts:
        balance_entry = {
            'code': account.code,
            'name': account.name,
            'balance': str(account.current_balance),
        }

        if account.account_type == AccountType.INCOME:
            balances['income'].append(balance_entry)
        elif account.account_type == AccountType.EXPENSE:
            balances['expense'].append(balance_entry)
        elif account.account_type == AccountType.ASSET:
            balances['asset'].append(balance_entry)
        elif account.account_type == AccountType.LIABILITY:
            balances['liability'].append(balance_entry)
        elif account.account_type == AccountType.EQUITY:
            balances['equity'].append(balance_entry)

    return balances


@transaction.atomic
def close_period(period_id, user):
    """
    إقفال فترة محاسبية.

    يقوم بما يلي:
        1. التحقق من إمكانية الإقفال (لا توجد قيود غير مرحّلة).
        2. إنشاء قيد إقفال لحسابات الإيرادات (إقفال الأرصدة إلى الصفر).
        3. إنشاء قيد إقفال لحسابات المصروفات (إقفال الأرصدة إلى الصفر).
        4. نقل صافي الربح/الخسارة إلى حساب الأرباح المحتجزة.
        5. تخزين أرصدة الإقفال كـ JSON.
        6. تحديث حالة الفترة إلى 'مقفل'.

    المعاملات:
        period_id (int): معرّف الفترة المحاسبية.
        user (User): المستخدم الذي يقوم بالإقفال.

    العائد:
        tuple: (FiscalPeriod, list[ClosureEntry]) الفترة المقفلة وقيود الإقفال.

    الاستثناءات:
        ValueError: إذا لم تكن الفترة قابلة للإقفال.
    """
    try:
        period = FiscalPeriod.objects.select_for_update().get(pk=period_id)
    except FiscalPeriod.DoesNotExist:
        raise ValueError(f'الفترة المحاسبية ذات المعرّف {period_id} غير موجودة')

    # التحقق من إمكانية الإقفال
    validation = validate_period_closable(period)
    if not validation['valid']:
        raise ValueError(
            f'لا يمكن إقفال الفترة: {"; ".join(validation["errors"])}'
        )

    # تحديث حالة الفترة إلى قيد الإقفال
    period.status = PeriodStatus.CLOSING
    period.save(update_fields=['status', 'updated_at'])

    # الحصول على حساب الأرباح المحتجزة
    retained_earnings = _get_retained_earnings_account()

    # حساب أرصدة الإيرادات والمصروفات
    income_accounts = Account.objects.filter(
        is_active=True,
        account_type=AccountType.INCOME,
    ).exclude(current_balance=0)

    expense_accounts = Account.objects.filter(
        is_active=True,
        account_type=AccountType.EXPENSE,
    ).exclude(current_balance=0)

    total_income = sum(
        acc.current_balance for acc in income_accounts
    )
    total_expenses = sum(
        acc.current_balance for acc in expense_accounts
    )
    net_profit = total_income - total_expenses

    closure_entries_list = []

    # ─── إقفال حسابات الإيرادات ───
    if income_accounts.exists():
        income_closure_je = JournalEntry(
            entry_type='adjustment',
            description=f'إقفال الإيرادات - {period.get_period_label()} {period.year}',
            entry_date=period.period_end,
            created_by=user,
        )
        income_closure_je.save()

        for account in income_accounts:
            # إقفال الإيرادات: يُدَّان حساب الأرباح المحتجزة ويُقْرَض حساب الإيراد
            Transaction.objects.create(
                journal_entry=income_closure_je,
                account=retained_earnings,
                transaction_type='debit',
                amount=account.current_balance,
                description=f'إقفال إيراد: {account.name}',
            )
            Transaction.objects.create(
                journal_entry=income_closure_je,
                account=account,
                transaction_type='credit',
                amount=account.current_balance,
                description=f'إقفال إيراد: {account.name}',
            )

        # ترحيل قيد الإقفال
        income_closure_je.post_entry()

        # تسجيل قيد الإقفال
        closure_entries_list.append(
            ClosureEntry.objects.create(
                fiscal_period=period,
                journal_entry=income_closure_je,
                entry_type=ClosureEntryType.INCOME_CLOSURE,
                description=f'إقفال حسابات الإيرادات لفترة {period.get_period_label()} {period.year}',
                total_amount=total_income,
            )
        )

    # ─── إقفال حسابات المصروفات ───
    if expense_accounts.exists():
        expense_closure_je = JournalEntry(
            entry_type='adjustment',
            description=f'إقفال المصروفات - {period.get_period_label()} {period.year}',
            entry_date=period.period_end,
            created_by=user,
        )
        expense_closure_je.save()

        for account in expense_accounts:
            # إقفال المصروفات: يُدَّان حساب المصروف ويُقْرَض حساب الأرباح المحتجزة
            Transaction.objects.create(
                journal_entry=expense_closure_je,
                account=account,
                transaction_type='debit',
                amount=account.current_balance,
                description=f'إقفال مصروف: {account.name}',
            )
            Transaction.objects.create(
                journal_entry=expense_closure_je,
                account=retained_earnings,
                transaction_type='credit',
                amount=account.current_balance,
                description=f'إقفال مصروف: {account.name}',
            )

        # ترحيل قيد الإقفال
        expense_closure_je.post_entry()

        # تسجيل قيد الإقفال
        closure_entries_list.append(
            ClosureEntry.objects.create(
                fiscal_period=period,
                journal_entry=expense_closure_je,
                entry_type=ClosureEntryType.EXPENSE_CLOSURE,
                description=f'إقفال حسابات المصروفات لفترة {period.get_period_label()} {period.year}',
                total_amount=total_expenses,
            )
        )

    # ─── تحويل صافي الربح/الخسارة ───
    if net_profit != Decimal('0.00'):
        profit_transfer_je = JournalEntry(
            entry_type='adjustment',
            description=(
                f'تحويل {"صافي ربح" if net_profit > 0 else "صافي خسارة"} '
                f'- {period.get_period_label()} {period.year}'
            ),
            entry_date=period.period_end,
            created_by=user,
        )
        profit_transfer_je.save()

        if net_profit > 0:
            # ربح: يُقْرَض الأرباح المحتجزة (زيادة) ويُدَّان الدخل المجمع (تخفيض إن وُجد)
            Transaction.objects.create(
                journal_entry=profit_transfer_je,
                account=retained_earnings,
                transaction_type='credit',
                amount=abs(net_profit),
                description=f'تحويل صافي الربح: {period.get_period_label()} {period.year}',
            )
        else:
            # خسارة: يُدَّان الأرباح المحتجزة (تخفيض)
            Transaction.objects.create(
                journal_entry=profit_transfer_je,
                account=retained_earnings,
                transaction_type='debit',
                amount=abs(net_profit),
                description=f'تحويل صافي الخسارة: {period.get_period_label()} {period.year}',
            )

        # ترحيل قيد التحويل
        profit_transfer_je.post_entry()

        # تسجيل قيد التحويل
        closure_entries_list.append(
            ClosureEntry.objects.create(
                fiscal_period=period,
                journal_entry=profit_transfer_je,
                entry_type=ClosureEntryType.NET_PROFIT_TRANSFER,
                description=(
                    f'تحويل {"صافي ربح" if net_profit > 0 else "صافي خسارة"} '
                    f'بمبلغ {abs(net_profit):,.2f} ر.س إلى الأرباح المحتجزة'
                ),
                total_amount=abs(net_profit),
            )
        )

    # ─── تخزين أرصدة الإقفال وتحديث حالة الفترة ───
    period.closing_balances = _snapshot_balances()
    period.status = PeriodStatus.CLOSED
    period.closed_by = user
    period.closed_at = timezone.now()
    period.save(
        update_fields=[
            'closing_balances', 'status', 'closed_by', 'closed_at', 'updated_at',
        ]
    )

    return period, closure_entries_list


@transaction.atomic
def reopen_period(period_id, user):
    """
    إعادة فتح فترة محاسبية مقفلة.

    يقوم بما يلي:
        1. عكس (إلغاء ترحيل) جميع قيود الإقفال المرتبطة بالفترة.
        2. حذف سجلات قيود الإقفال.
        3. حذف قيود اليومية الخاصة بالإقفال.
        4. إعادة تعيين حالة الفترة إلى 'مفتوح'.
        5. مسح أرصدة الإقفال المخزّنة.

    المعاملات:
        period_id (int): معرّف الفترة المحاسبية.
        user (User): المستخدم الذي يقوم بإعادة الفتح.

    العائد:
        FiscalPeriod: الفترة المُعاد فتحها.

    الاستثناءات:
        ValueError: إذا كانت الفترة غير مقفلة أو غير موجودة.
    """
    try:
        period = FiscalPeriod.objects.select_for_update().get(pk=period_id)
    except FiscalPeriod.DoesNotExist:
        raise ValueError(f'الفترة المحاسبية ذات المعرّف {period_id} غير موجودة')

    if not period.is_closed():
        raise ValueError(f'الفترة "{period.get_period_label()}" ليست مقفلة')

    # الحصول على جميع قيود الإقفال للفترة
    closure_entries = ClosureEntry.objects.filter(
        fiscal_period=period,
    ).select_related('journal_entry')

    for closure_entry in closure_entries:
        je = closure_entry.journal_entry
        # عكس ترحيل قيد اليومية
        if je.is_posted:
            je.reverse_entry()
        # حذف قيد اليومية (يحذف الحركات المرتبطة تلقائياً عبر CASCADE)
        je.delete()

    # حذف سجلات الإقفال
    closure_entries.delete()

    # إعادة تعيين حالة الفترة
    period.status = PeriodStatus.OPEN
    period.closed_by = None
    period.closed_at = None
    period.closing_balances = {}
    period.save(
        update_fields=[
            'status', 'closed_by', 'closed_at', 'closing_balances', 'updated_at',
        ]
    )

    return period


@transaction.atomic
def close_fiscal_year(year_id, user):
    """
    إقفال السنة المالية بالكامل.

    يقوم بما يلي:
        1. إقفال جميع الفترات المفتوحة المتبقية.
        2. تحديث حالة السنة المالية إلى 'مقفل'.

    المعاملات:
        year_id (int): معرّف السنة المالية.
        user (User): المستخدم الذي يقوم بالإقفال.

    العائد:
        FiscalYear: السنة المالية المقفلة.

    الاستثناءات:
        ValueError: إذا كانت السنة المالية مقفلة مسبقاً أو غير موجودة.
    """
    try:
        fiscal_year = FiscalYear.objects.select_for_update().get(pk=year_id)
    except FiscalYear.DoesNotExist:
        raise ValueError(f'السنة المالية ذات المعرّف {year_id} غير موجودة')

    if fiscal_year.is_closed():
        raise ValueError(f'السنة المالية {fiscal_year.year} مقفلة مسبقاً')

    # إقفال جميع الفترات المفتوحة المتبقية بالترتيب
    open_periods = fiscal_year.periods.filter(
        status__in=[PeriodStatus.OPEN, PeriodStatus.CLOSING],
    ).order_by('period_number')

    closed_periods_count = 0
    errors = []

    for period in open_periods:
        validation = validate_period_closable(period)
        if validation['valid']:
            close_period(period.pk, user)
            closed_periods_count += 1
        else:
            errors.append(
                f'الفترة {period.get_period_label()}: {"; ".join(validation["errors"])}'
            )

    if errors:
        raise ValueError(
            f'فشل إقفال بعض الفترات: {"; ".join(errors)}'
        )

    # تحديث حالة السنة المالية
    fiscal_year.status = FiscalYearStatus.CLOSED
    fiscal_year.notes = (
        f'{fiscal_year.notes}\n'
        f'تم إقفال السنة المالية بواسطة {user.get_full_name() or user.username} '
        f'في {timezone.now().strftime("%Y-%m-%d %H:%M")} - '
        f'تم إقفال {closed_periods_count} فترة.'
    ).strip()
    fiscal_year.save(update_fields=['status', 'notes', 'updated_at'])

    return fiscal_year
