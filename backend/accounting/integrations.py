"""
التكامل التلقائي المحاسبي - Automatic Accounting Integration.
Provides automatic journal entry creation for Payroll and Fixed Assets modules.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Account, AccountType, JournalEntry, Transaction


# =============================================
# Helper Functions
# =============================================

def get_or_create_account(code, name, name_en, account_type, description=''):
    """
    Get or create an account by code.
    Returns the Account instance.
    """
    account, created = Account.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'name_en': name_en,
            'account_type': account_type,
            'description': description,
        },
    )
    return account


def get_payroll_accounts():
    """
    Returns a dict of all payroll-related accounts.
    Creates accounts with default settings if they do not exist.
    """
    salary_expense = get_or_create_account(
        code='5100',
        name='المرتبات والأجور',
        name_en='Salaries & Wages',
        account_type=AccountType.EXPENSE,
        description='مصروف الرواتب والأجور الأساسية',
    )
    social_insurance_expense = get_or_create_account(
        code='5200',
        name='مصروف التأمينات الاجتماعية',
        name_en='Social Insurance Expense',
        account_type=AccountType.EXPENSE,
        description='حصة صاحب العمل في التأمينات الاجتماعية',
    )
    gosi_expense = get_or_create_account(
        code='5210',
        name='مصروف التأمينات الاجتماعية (GOSI)',
        name_en='GOSI Expense',
        account_type=AccountType.EXPENSE,
        description='مصروف مساهمة صاحب العمل في GOSI',
    )
    cash_bank = get_or_create_account(
        code='1001',
        name='النقدية والبنوك',
        name_en='Cash & Banks',
        account_type=AccountType.ASSET,
        description='حساب النقدية والبنوك الافتراضي',
    )
    gosi_payable = get_or_create_account(
        code='2100',
        name='التأمينات الاجتماعية مستحقة الدفع',
        name_en='GOSI Payable',
        account_type=AccountType.LIABILITY,
        description='مبالغ مستحقة الدفع للتأمينات الاجتماعية (GOSI)',
    )
    income_tax_payable = get_or_create_account(
        code='2200',
        name='ضريبة الدخل مستحقة الدفع',
        name_en='Income Tax Payable',
        account_type=AccountType.LIABILITY,
        description='ضرائب الدخل المخصومة المستحقة الدفع',
    )
    social_insurance_payable = get_or_create_account(
        code='2300',
        name='التأمينات الاجتماعية مستحقة (حصة صاحب العمل)',
        name_en='Social Insurance Payable (Employer)',
        account_type=AccountType.LIABILITY,
        description='حصة صاحب العمل في التأمينات الاجتماعية المستحقة',
    )
    employee_loans_receivable = get_or_create_account(
        code='1150',
        name='سلف ومقدمات الموظفين',
        name_en='Employee Advances & Loans Receivable',
        account_type=AccountType.ASSET,
        description='سلف ومقدمات الموظفين المسددة من الرواتب',
    )
    other_deductions_payable = get_or_create_account(
        code='2400',
        name='خصومات أخرى مستحقة الدفع',
        name_en='Other Deductions Payable',
        account_type=AccountType.LIABILITY,
        description='خصومات أخرى من رواتب الموظفين',
    )

    return {
        'salary_expense': salary_expense,
        'social_insurance_expense': social_insurance_expense,
        'gosi_expense': gosi_expense,
        'cash_bank': cash_bank,
        'gosi_payable': gosi_payable,
        'income_tax_payable': income_tax_payable,
        'social_insurance_payable': social_insurance_payable,
        'employee_loans_receivable': employee_loans_receivable,
        'other_deductions_payable': other_deductions_payable,
    }


def get_asset_accounts():
    """
    Returns a dict of all asset-related accounts.
    Creates accounts with default settings if they do not exist.
    """
    fixed_asset = get_or_create_account(
        code='1500',
        name='الأصول الثابتة',
        name_en='Fixed Assets',
        account_type=AccountType.ASSET,
        description='حساب الأصول الثابتة الرئيسي',
    )
    accumulated_depreciation = get_or_create_account(
        code='1300',
        name='مجمع الإهلاك',
        name_en='Accumulated Depreciation',
        account_type=AccountType.ASSET,
        description='مجمع إهلاك الأصول الثابتة (حساب مقوّم سلبي)',
    )
    depreciation_expense = get_or_create_account(
        code='5300',
        name='مصروف الإهلاك',
        name_en='Depreciation Expense',
        account_type=AccountType.EXPENSE,
        description='مصروف إهلاك الأصول الثابتة',
    )
    cash_bank = get_or_create_account(
        code='1001',
        name='النقدية والبنوك',
        name_en='Cash & Banks',
        account_type=AccountType.ASSET,
        description='حساب النقدية والبنوك الافتراضي',
    )
    accounts_payable = get_or_create_account(
        code='2000',
        name='الدائنون (المورّدون)',
        name_en='Accounts Payable',
        account_type=AccountType.LIABILITY,
        description='مبالغ مستحقة للمورّدين',
    )
    gain_on_disposal = get_or_create_account(
        code='6100',
        name='أرباح بيع الأصول الثابتة',
        name_en='Gain on Disposal of Fixed Assets',
        account_type=AccountType.INCOME,
        description='أرباح محققة من بيع أو تخريد الأصول الثابتة',
    )
    loss_on_disposal = get_or_create_account(
        code='5400',
        name='خسائر بيع الأصول الثابتة',
        name_en='Loss on Disposal of Fixed Assets',
        account_type=AccountType.EXPENSE,
        description='خسائر محققة من بيع أو تخريد الأصول الثابتة',
    )

    return {
        'fixed_asset': fixed_asset,
        'accumulated_depreciation': accumulated_depreciation,
        'depreciation_expense': depreciation_expense,
        'cash_bank': cash_bank,
        'accounts_payable': accounts_payable,
        'gain_on_disposal': gain_on_disposal,
        'loss_on_disposal': loss_on_disposal,
    }


# =============================================
# Payroll Integration
# =============================================

@db_transaction.atomic
def create_payroll_journal_entry(payroll_period, user):
    """
    Create a journal entry when payroll is processed.

    Automatically called when a payroll period is confirmed/paid.

    Debit:
        - Salary Expense (5100): total gross earnings
        - GOSI Expense (5210): employer GOSI contribution
    Credit:
        - Cash/Bank (1001): net payable to employees
        - GOSI Payable (2100): employee GOSI + employer GOSI contributions
        - Income Tax Payable (2200): tax withheld from employees
        - Employee Loans Receivable (1150): loan deductions from employees
        - Other Deductions Payable (2400): other deductions (absence, etc.)

    Returns:
        JournalEntry: The created and posted journal entry.

    Raises:
        ValueError: If payroll period has no records or all amounts are zero.
    """
    from payroll.models import PayrollRecord

    records = payroll_period.records.select_related('employee').all()

    if not records.exists():
        raise ValueError('لا توجد سجلات رواتب في فترة الرواتب المحددة')

    # Aggregate amounts from payroll records
    total_earnings = Decimal('0')
    employee_gosi = Decimal('0')
    employee_tax = Decimal('0')
    employee_loans = Decimal('0')
    other_deductions = Decimal('0')
    total_net = Decimal('0')

    for record in records:
        total_earnings += record.total_earnings
        employee_gosi += record.deductions_gosi
        employee_tax += record.deductions_tax
        employee_loans += record.deductions_loan
        other_deductions += record.deductions_absence + record.deductions_other
        total_net += record.net_salary

    # Check for zero amounts
    if total_earnings == 0 and total_net == 0:
        raise ValueError('مبالغ الرواتب صفرية، لا يمكن إنشاء قيد محاسبي')

    # Calculate employer GOSI contribution (11.75% of basic salary)
    total_basic_salary = sum(r.basic_salary for r in records)
    employer_gosi_rate = Decimal('0.1175')
    employer_gosi = (total_basic_salary * employer_gosi_rate).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    # Get accounts
    accounts = get_payroll_accounts()

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='payment',
        description=(
            f'صرف رواتب {payroll_period.name} - '
            f'عدد الموظفين: {payroll_period.total_employees}'
        ),
        reference=f'PAY-{payroll_period.year}-{payroll_period.month:02d}',
        entry_date=payroll_period.end_date,
        created_by=user,
    )

    # Debit: Salary Expense (total gross earnings)
    if total_earnings > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['salary_expense'],
            transaction_type='debit',
            amount=total_earnings,
            description=f'مصروف الرواتب - {payroll_period.name}',
        )

    # Debit: GOSI Expense (employer GOSI contribution)
    if employer_gosi > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['gosi_expense'],
            transaction_type='debit',
            amount=employer_gosi,
            description=f'مصروف حصة صاحب العمل في GOSI - {payroll_period.name}',
        )

    # Credit: Cash/Bank (net payable to employees)
    if total_net > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['cash_bank'],
            transaction_type='credit',
            amount=total_net,
            description=f'صافي الرواتب المستحقة للموظفين - {payroll_period.name}',
        )

    # Credit: GOSI Payable (employee GOSI + employer GOSI)
    total_gosi = employee_gosi + employer_gosi
    if total_gosi > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['gosi_payable'],
            transaction_type='credit',
            amount=total_gosi,
            description=(
                f'GOSI مستحقة الدفع '
                f'(موظف: {employee_gosi:,.2f}، صاحب عمل: {employer_gosi:,.2f}) - '
                f'{payroll_period.name}'
            ),
        )

    # Credit: Income Tax Payable (tax withheld from employees)
    if employee_tax > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['income_tax_payable'],
            transaction_type='credit',
            amount=employee_tax,
            description=f'ضريبة الدخل المخصومة - {payroll_period.name}',
        )

    # Credit: Employee Loans Receivable (loan deductions recovered)
    if employee_loans > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['employee_loans_receivable'],
            transaction_type='credit',
            amount=employee_loans,
            description=f'خصم سلف وقروض الموظفين - {payroll_period.name}',
        )

    # Credit: Other Deductions Payable (absence, other deductions)
    if other_deductions > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['other_deductions_payable'],
            transaction_type='credit',
            amount=other_deductions,
            description=f'خصومات أخرى (غياب وغيرها) - {payroll_period.name}',
        )

    # Auto-post the entry
    entry.post_entry()

    return entry


def reverse_payroll_journal_entry(payroll_period):
    """
    Reverse the journal entry linked to a payroll period.
    Called when payroll is cancelled or reversed.

    Finds the linked journal entry by reference, reverses it,
    and marks its description as cancelled.

    Returns:
        bool: True if reversed successfully, False if no entry found.

    Raises:
        ValueError: If the entry reversal fails.
    """
    reference = f'PAY-{payroll_period.year}-{payroll_period.month:02d}'

    entry = JournalEntry.objects.filter(
        reference=reference,
        is_posted=True,
    ).last()

    if not entry:
        return False

    entry.reverse_entry()
    entry.description = f'[ملغى] {entry.description}'
    entry.save(update_fields=['description', 'updated_at'])

    return True


# =============================================
# Fixed Assets Integration
# =============================================

@db_transaction.atomic
def create_depreciation_journal_entry(asset, user, period_date=None):
    """
    Create a monthly depreciation journal entry for a fixed asset.

    Only creates an entry if the asset is active and not fully depreciated.

    Debit:
        - Depreciation Expense (5300): monthly depreciation amount
    Credit:
        - Accumulated Depreciation (1300): same amount

    Args:
        asset: FixedAsset instance.
        user: User instance creating the entry.
        period_date: Date for the entry. Defaults to today.

    Returns:
        JournalEntry: The created and posted journal entry.

    Raises:
        ValueError: If asset is inactive, fully depreciated, or amount is zero.
    """
    # Validate asset state
    if not asset.is_active:
        raise ValueError(f'الأصل "{asset.name}" غير نشط، لا يمكن احتساب الإهلاك')

    if asset.status not in ('active', 'in_maintenance'):
        raise ValueError(
            f'حالة الأصل "{asset.name}" هي "{asset.get_status_display()}"، '
            f'لا يمكن احتساب الإهلاك'
        )

    # Calculate depreciation amount
    depreciation_amount = asset.calculate_depreciation()

    if depreciation_amount <= 0:
        raise ValueError(
            f'مبلغ الإهلاك للأصل "{asset.name}" صفر أو سالب، '
            f'قد يكون الأصل مُهلك بالكامل'
        )

    # Ensure we don't depreciate beyond the depreciable amount
    depreciable_limit = asset.purchase_price - asset.salvage_value - asset.accumulated_depreciation
    if depreciable_limit <= 0:
        raise ValueError(
            f'الأصل "{asset.name}" مُهلك بالكامل (مجمع الإهلاك بلغ الحد الأقصى)'
        )

    # Cap depreciation at the remaining depreciable amount
    actual_depreciation = min(depreciation_amount, depreciable_limit)
    actual_depreciation = actual_depreciation.quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    if actual_depreciation <= 0:
        raise ValueError(
            f'مبلغ الإهلاك الفعلي للأصل "{asset.name}" صفر بعد التقريب'
        )

    # Get accounts
    accounts = get_asset_accounts()

    # Default to today if no period_date provided
    entry_date = period_date or timezone.now().date()

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='adjustment',
        description=(
            f'إهلاك شهري - {asset.name} ({asset.asset_number}) - '
            f'القيمة الدفترية: {asset.current_value:,.2f} ر.س'
        ),
        reference=f'DEP-{asset.asset_number}',
        entry_date=entry_date,
        created_by=user,
    )

    # Debit: Depreciation Expense
    Transaction.objects.create(
        journal_entry=entry,
        account=accounts['depreciation_expense'],
        transaction_type='debit',
        amount=actual_depreciation,
        description=f'مصروف إهلاك - {asset.name} ({asset.asset_number})',
    )

    # Credit: Accumulated Depreciation
    Transaction.objects.create(
        journal_entry=entry,
        account=accounts['accumulated_depreciation'],
        transaction_type='credit',
        amount=actual_depreciation,
        description=f'مجمع إهلاك - {asset.name} ({asset.asset_number})',
    )

    # Auto-post the entry
    entry.post_entry()

    # Update asset's accumulated depreciation
    asset.accumulated_depreciation += actual_depreciation
    asset.save(update_fields=['accumulated_depreciation', 'updated_at'])

    return entry


@db_transaction.atomic
def create_asset_purchase_journal_entry(asset, user):
    """
    Create a journal entry when a fixed asset is purchased.

    Debit:
        - Fixed Asset (1500): purchase cost
    Credit:
        - Cash/Bank (1001): purchase cost

    Returns:
        JournalEntry: The created and posted journal entry.

    Raises:
        ValueError: If purchase price is zero or negative.
    """
    if asset.purchase_price <= 0:
        raise ValueError(
            f'سعر شراء الأصل "{asset.name}" غير صالح: {asset.purchase_price}'
        )

    # Get accounts
    accounts = get_asset_accounts()

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='payment',
        description=(
            f'شراء أصل ثابت - {asset.name} ({asset.asset_number}) - '
            f'بمبلغ {asset.purchase_price:,.2f} ر.س'
        ),
        reference=f'PUR-{asset.asset_number}',
        entry_date=asset.purchase_date,
        created_by=user,
    )

    # Debit: Fixed Asset Account
    Transaction.objects.create(
        journal_entry=entry,
        account=accounts['fixed_asset'],
        transaction_type='debit',
        amount=asset.purchase_price,
        description=(
            f'شراء أصل ثابت - {asset.name} '
            f'(الرقم التسلسلي: {asset.serial_number or "غير محدد"})'
        ),
    )

    # Credit: Cash/Bank Account
    Transaction.objects.create(
        journal_entry=entry,
        account=accounts['cash_bank'],
        transaction_type='credit',
        amount=asset.purchase_price,
        description=f'دفع ثمن الأصل الثابت - {asset.name} ({asset.asset_number})',
    )

    # Auto-post the entry
    entry.post_entry()

    return entry


@db_transaction.atomic
def create_asset_disposal_journal_entry(asset, user, disposal_amount, disposal_type='sale'):
    """
    Create a journal entry when a fixed asset is disposed of (sold or scrapped).

    If sale:
        Debit:
            - Cash/Bank (1001): disposal amount (proceeds from sale)
            - Accumulated Depreciation (1300): total accumulated depreciation
            - Loss on Disposal (5400): if loss (optional, only if applicable)
        Credit:
            - Fixed Asset (1500): original cost
            - Gain on Disposal (6100): if gain (optional, only if applicable)

    Args:
        asset: FixedAsset instance being disposed.
        user: User instance creating the entry.
        disposal_amount: Amount received from disposal (0 for scrap/donation).
        disposal_type: Type of disposal ('sale', 'scrap', etc.).

    Returns:
        JournalEntry: The created and posted journal entry.

    Raises:
        ValueError: If asset has zero cost or other validation failure.
    """
    if asset.purchase_price <= 0:
        raise ValueError(
            f'سعر شراء الأصل "{asset.name}" غير صالح: {asset.purchase_price}'
        )

    disposal_amount = Decimal(str(disposal_amount))

    if disposal_amount < 0:
        raise ValueError('مبلغ التخريد لا يمكن أن يكون سالباً')

    # Get accounts
    accounts = get_asset_accounts()

    # Calculate gain or loss
    book_value = asset.current_value  # purchase_price - accumulated_depreciation
    gain_loss = disposal_amount - book_value

    # Determine disposal type label in Arabic
    disposal_type_labels = {
        'sale': 'بيع',
        'scrap': 'تخريد',
        'donation': 'تبرع',
        'loss': 'فقدان',
    }
    disposal_label = disposal_type_labels.get(disposal_type, disposal_type)

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='adjustment',
        description=(
            f'{disposal_label} أصل ثابت - {asset.name} ({asset.asset_number}) - '
            f'بمبلغ {disposal_amount:,.2f} ر.س '
            f'(القيمة الدفترية: {book_value:,.2f} ر.س)'
        ),
        reference=f'DISP-{asset.asset_number}',
        entry_date=timezone.now().date(),
        created_by=user,
    )

    # Debit: Cash/Bank (proceeds from disposal)
    if disposal_amount > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['cash_bank'],
            transaction_type='debit',
            amount=disposal_amount,
            description=f'حصيلة {disposal_label} - {asset.name} ({asset.asset_number})',
        )

    # Debit: Accumulated Depreciation (remove accumulated depreciation)
    if asset.accumulated_depreciation > 0:
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['accumulated_depreciation'],
            transaction_type='debit',
            amount=asset.accumulated_depreciation,
            description=(
                f'إزالة مجمع الإهلاك - {asset.name} ({asset.asset_number})'
            ),
        )

    # Credit: Fixed Asset Account (remove original cost)
    Transaction.objects.create(
        journal_entry=entry,
        account=accounts['fixed_asset'],
        transaction_type='credit',
        amount=asset.purchase_price,
        description=f'إزالة الأصل الثابت - {asset.name} ({asset.asset_number})',
    )

    # Handle gain or loss on disposal
    if gain_loss > 0:
        # Gain: credit Gain on Disposal
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['gain_on_disposal'],
            transaction_type='credit',
            amount=gain_loss,
            description=(
                f'ربح من {disposal_label} الأصل - {asset.name} '
                f'(مبلغ الربح: {gain_loss:,.2f} ر.س)'
            ),
        )
    elif gain_loss < 0:
        # Loss: debit Loss on Disposal
        loss_amount = abs(gain_loss)
        Transaction.objects.create(
            journal_entry=entry,
            account=accounts['loss_on_disposal'],
            transaction_type='debit',
            amount=loss_amount,
            description=(
                f'خسارة من {disposal_label} الأصل - {asset.name} '
                f'(مبلغ الخسارة: {loss_amount:,.2f} ر.س)'
            ),
        )

    # Auto-post the entry
    entry.post_entry()

    return entry
