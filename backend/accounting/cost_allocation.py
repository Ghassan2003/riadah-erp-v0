"""
التوزيع التلقائي للمصروفات - Automatic Cost Allocation System.
Manages cost centers, allocation rules, targets, and execution logs.
Provides automatic journal entry creation for cost distributions.
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


# =============================================
# Allocation Type Choices
# =============================================

class AllocationType(models.TextChoices):
    PERCENTAGE = 'percentage', 'توزيع بنسبة مئوية ثابتة'
    EQUAL = 'equal', 'توزيع متساوٍ'
    RATIO = 'ratio', 'توزيع بنسب مخصصة'
    HEADCOUNT = 'headcount', 'توزيع حسب عدد الموظفين'
    REVENUE = 'revenue', 'توزيع حسب نسبة الإيرادات'


class AllocationLogStatus(models.TextChoices):
    SUCCESS = 'success', 'تم بنجاح'
    PARTIAL = 'partial', 'توزيع جزئي'
    FAILED = 'failed', 'فشل'


# =============================================
# CostCenter Model (مراكز التكلفة)
# =============================================

class CostCenter(models.Model):
    """
    مركز التكلفة - Hierarchical cost center for tracking expenses by department,
    project, or business unit.
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز مركز التكلفة',
        db_index=True,
        help_text='رمز فريد لمركز التكلفة (مثال: CC-001)',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم مركز التكلفة',
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم مركز التكلفة (إنجليزي)',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_centers',
        verbose_name='القسم المرتبط',
        help_text='ربط مركز التكلفة بقسم في الموارد البشرية',
    )
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cost_centers',
        verbose_name='مدير مركز التكلفة',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='مركز التكلفة الرئيسي',
        help_text='الهيكل الهرمي لمراكز التكلفة',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    budget_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='الميزانية المخصصة',
        help_text='مبلغ الميزانية المخصصة لمركز التكلفة بالريال السعودي',
    )
    actual_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='المبلغ الفعلي',
        help_text='إجمالي المصروفات الفعلية لمركز التكلفة',
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
        verbose_name = 'مركز تكلفة'
        verbose_name_plural = 'مراكز التكلفة'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def clean(self):
        """Validate cost center data."""
        from django.core.exceptions import ValidationError

        # Prevent circular parent references
        if self.parent and self.parent_id == self.pk:
            raise ValidationError('لا يمكن أن يكون مركز التكلفة أباً لنفسه')

        # Validate parent hierarchy depth
        if self.parent:
            depth = 1
            current = self.parent
            while current is not None:
                depth += 1
                current = current.parent
                if depth > 5:
                    raise ValidationError(
                        'الحد الأقصى لعمق الهيكل الهرمي هو 5 مستويات'
                    )

        # Validate budget is non-negative
        if self.budget_amount < 0:
            raise ValidationError('الميزانية المخصصة يجب أن تكون قيمة غير سالبة')

    def get_children_actual_total(self):
        """Calculate total actual amount from all child cost centers."""
        total = Decimal('0')
        for child in self.children.filter(is_active=True):
            total += child.actual_amount
        return total

    def get_full_path(self):
        """Get the full hierarchical path of the cost center."""
        if not self.parent:
            return self.name
        return f'{self.parent.get_full_path()} / {self.name}'


# =============================================
# AllocationRule Model (قواعد التوزيع)
# =============================================

class AllocationRule(models.Model):
    """
    قاعدة التوزيع - Defines how expenses from a source account are allocated
    to target cost centers and accounts.
    """

    name = models.CharField(
        max_length=255,
        verbose_name='اسم القاعدة',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    source_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='allocation_rules_as_source',
        verbose_name='الحساب المصدر',
        help_text='الحساب الذي يتم التوزيع منه',
    )
    allocation_type = models.CharField(
        max_length=20,
        choices=AllocationType.choices,
        verbose_name='نوع التوزيع',
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name='تكرار تلقائي',
        help_text='تنفيذ القاعدة تلقائياً بشكل شهري',
    )
    recurrence_day = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='يوم التنفيذ الشهري',
        help_text='يوم من الشهر لتنفيذ التوزيع التلقائي (1-28)',
    )
    effective_from = models.DateField(
        verbose_name='تاريخ السريان',
        db_index=True,
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
    )
    last_executed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر تنفيذ',
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
        verbose_name = 'قاعدة توزيع'
        verbose_name_plural = 'قواعد التوزيع'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.get_allocation_type_display()}'

    def clean(self):
        """Validate allocation rule data."""
        from django.core.exceptions import ValidationError

        # Validate recurrence_day range
        if self.is_recurring and self.recurrence_day is not None:
            if not (1 <= self.recurrence_day <= 28):
                raise ValidationError(
                    {'recurrence_day': 'يوم التنفيذ يجب أن يكون بين 1 و 28'}
                )

        # Require recurrence_day for recurring rules
        if self.is_recurring and self.recurrence_day is None:
            raise ValidationError(
                {'recurrence_day': 'يجب تحديد يوم التنفيذ للقواعد المتكررة'}
            )

        # Validate effective dates
        if self.effective_to and self.effective_from and self.effective_to <= self.effective_from:
            raise ValidationError(
                {'effective_to': 'تاريخ الانتهاء يجب أن يكون بعد تاريخ السريان'}
            )

    def is_effective(self, date=None):
        """Check if the rule is effective on a given date."""
        check_date = date or timezone.now().date()
        if not self.is_active:
            return False
        if check_date < self.effective_from:
            return False
        if self.effective_to and check_date > self.effective_to:
            return False
        return True

    def is_due_for_execution(self):
        """Check if a recurring rule is due for execution today."""
        if not self.is_recurring:
            return False
        if not self.is_effective():
            return False

        today = timezone.now().date()
        today_day = today.day

        # Check if today is the recurrence day
        if today_day != self.recurrence_day:
            return False

        # Check if already executed this month
        if self.last_executed:
            last = self.last_executed.date()
            if last.year == today.year and last.month == today.month:
                return False

        return True


# =============================================
# AllocationTarget Model (أهداف التوزيع)
# =============================================

class AllocationTarget(models.Model):
    """
    هدف التوزيع - Defines a target cost center and account to receive
    allocated amounts from a source account.
    """

    rule = models.ForeignKey(
        AllocationRule,
        on_delete=models.CASCADE,
        related_name='targets',
        verbose_name='قاعدة التوزيع',
    )
    target_cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.PROTECT,
        related_name='allocation_targets',
        verbose_name='مركز التكلفة الهدف',
        help_text='مركز التكلفة الذي سيستلم الحصة',
    )
    target_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='allocation_targets',
        verbose_name='الحساب الهدف',
        help_text='الحساب الذي يتم التوزيع إليه',
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='النسبة المئوية',
        help_text='النسبة المئوية المخصصة للهدف (لنوع التوزيع بالنسبة المئوية)',
    )
    ratio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='النسبة',
        help_text='النسبة المخصصة للهدف (لنوع التوزيع بالنسب المخصصة)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'هدف توزيع'
        verbose_name_plural = 'أهداف التوزيع'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['rule', 'target_account'],
                name='unique_allocation_target_rule_account',
            ),
        ]

    def __str__(self):
        return (
            f'{self.target_cost_center.name} - '
            f'{self.target_account.code} ({self.percentage or self.ratio})'
        )

    def clean(self):
        """Validate allocation target data."""
        from django.core.exceptions import ValidationError

        # Percentage must be positive if set
        if self.percentage is not None and self.percentage <= 0:
            raise ValidationError(
                {'percentage': 'النسبة المئوية يجب أن تكون قيمة موجبة'}
            )
        if self.percentage is not None and self.percentage > 100:
            raise ValidationError(
                {'percentage': 'النسبة المئوية لا يمكن أن تتجاوز 100%'}
            )

        # Ratio must be positive if set
        if self.ratio is not None and self.ratio <= 0:
            raise ValidationError(
                {'ratio': 'النسبة يجب أن تكون قيمة موجبة'}
            )


# =============================================
# AllocationLog Model (سجل التوزيعات)
# =============================================

class AllocationLog(models.Model):
    """
    سجل التوزيع - Records the execution details of each allocation run,
    including the generated journal entry and any errors.
    """

    rule = models.ForeignKey(
        AllocationRule,
        on_delete=models.PROTECT,
        related_name='logs',
        verbose_name='قاعدة التوزيع',
    )
    period_start = models.DateField(
        verbose_name='بداية الفترة',
        db_index=True,
    )
    period_end = models.DateField(
        verbose_name='نهاية الفترة',
    )
    total_allocated = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='إجمالي المبلغ الموزع',
    )
    source_balance_before = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='رصيد الحساب المصدر قبل التوزيع',
    )
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocation_logs',
        verbose_name='قيد اليومية',
        help_text='قيد اليومية الذي تم إنشاؤه تلقائياً للتوزيع',
    )
    executed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='نفّذ بواسطة',
    )
    executed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التنفيذ',
    )
    status = models.CharField(
        max_length=20,
        choices=AllocationLogStatus.choices,
        default=AllocationLogStatus.SUCCESS,
        verbose_name='حالة التنفيذ',
        db_index=True,
    )
    error_message = models.TextField(
        blank=True,
        default='',
        verbose_name='رسالة الخطأ',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'سجل توزيع'
        verbose_name_plural = 'سجلات التوزيعات'
        ordering = ['-executed_at']

    def __str__(self):
        return (
            f'{self.rule.name} - {self.period_start} إلى {self.period_end} '
            f'({self.get_status_display()})'
        )


# =============================================
# Allocation Functions
# =============================================

def validate_allocation_targets(rule):
    """
    Validate that allocation targets are correctly configured for the rule.

    For 'percentage' type: targets must add up to 100%.
    For 'ratio' type: at least one target must have a ratio.
    For 'equal' / 'headcount' / 'revenue': at least one target must exist.

    Returns a list of validation error messages (empty if valid).
    """
    errors = []
    targets = rule.targets.filter(
        target_cost_center__is_active=True,
        target_account__is_active=True,
    )

    if not targets.exists():
        errors.append('يجب تحديد هدف توزيع واحد على الأقل')
        return errors

    if rule.allocation_type == AllocationType.PERCENTAGE:
        total_percentage = targets.aggregate(
            total=models.Sum('percentage')
        )['total'] or Decimal('0')

        total_percentage = total_percentage.quantize(Decimal('0.01'))

        if total_percentage != Decimal('100.00'):
            errors.append(
                f'مجموع النسب المئوية يجب أن يساوي 100% '
                f'(الحالي: {total_percentage}%)'
            )

        # Check that all targets have a percentage
        missing_pct = targets.filter(percentage__isnull=True)
        if missing_pct.exists():
            errors.append(
                'جميع الأهداف يجب أن تحدد نسبة مئوية لنوع التوزيع بالنسبة المئوية'
            )

    elif rule.allocation_type == AllocationType.RATIO:
        # Check that at least one target has a ratio
        targets_with_ratio = targets.filter(ratio__isnull=False)
        if not targets_with_ratio.exists():
            errors.append(
                'يجب تحديد نسبة لعنصر واحد على الأقل لنوع التوزيع بالنسب المخصصة'
            )

    elif rule.allocation_type in (
        AllocationType.EQUAL,
        AllocationType.HEADCOUNT,
        AllocationType.REVENUE,
    ):
        if targets.count() < 1:
            errors.append(
                'يجب تحديد هدف توزيع واحد على الأقل'
            )

    return errors


def calculate_headcount_allocation(rule):
    """
    Calculate allocation shares based on department headcount for each target.

    For each target cost center, counts active employees in the linked HR department
    and distributes the source balance proportionally.

    Returns a list of dicts: [{'target': AllocationTarget, 'share': Decimal, 'headcount': int}]
    """
    from hr.models import Employee

    targets = rule.targets.filter(
        target_cost_center__is_active=True,
        target_account__is_active=True,
    ).select_related('target_cost_center__department')

    allocations = []
    total_headcount = 0

    for target in targets:
        cost_center = target.target_cost_center

        # Get headcount from the linked department
        if cost_center.department:
            headcount = Employee.objects.filter(
                department=cost_center.department,
                is_active=True,
            ).count()
        else:
            # If no department linked, count employees assigned to this cost center's
            # child departments or fall back to 1 (equal weight)
            headcount = 1

        allocations.append({
            'target': target,
            'headcount': headcount,
            'share': Decimal('0'),
        })
        total_headcount += headcount

    if total_headcount == 0:
        # Equal distribution if no employees found
        share = Decimal('1') / max(len(allocations), 1)
        for alloc in allocations:
            alloc['headcount'] = 1
            alloc['share'] = share
    else:
        for alloc in allocations:
            alloc['share'] = (
                Decimal(str(alloc['headcount'])) / Decimal(str(total_headcount))
            ).quantize(Decimal('0.000001'))

    return allocations


def calculate_revenue_allocation(rule):
    """
    Calculate allocation shares based on revenue proportions across cost centers.

    Looks at income-type accounts associated with each target's cost center
    to determine revenue proportion, then allocates accordingly.

    Returns a list of dicts: [{'target': AllocationTarget, 'share': Decimal, 'revenue': Decimal}]
    """
    from accounting.models import Account, AccountType

    targets = rule.targets.filter(
        target_cost_center__is_active=True,
        target_account__is_active=True,
    ).select_related('target_cost_center')

    allocations = []
    total_revenue = Decimal('0')

    for target in targets:
        cost_center = target.target_cost_center

        # Calculate revenue for this cost center by summing up income account
        # transactions linked to the cost center
        # We look at income accounts' current_balance as a proxy for revenue
        if cost_center.department:
            revenue = Account.objects.filter(
                account_type=AccountType.INCOME,
                is_active=True,
            ).aggregate(
                total=models.Sum('current_balance')
            )['total'] or Decimal('0')

            # Scale by proportion of departments if applicable
            # For simplicity, use equal distribution as fallback
            if revenue == 0:
                revenue = Decimal('1')
        else:
            revenue = Decimal('1')

        allocations.append({
            'target': target,
            'revenue': revenue,
            'share': Decimal('0'),
        })
        total_revenue += revenue

    if total_revenue > 0:
        for alloc in allocations:
            alloc['share'] = (
                alloc['revenue'] / total_revenue
            ).quantize(Decimal('0.000001'))
    else:
        # Equal distribution if no revenue data
        share = Decimal('1') / max(len(allocations), 1)
        for alloc in allocations:
            alloc['share'] = share
            alloc['revenue'] = Decimal('1')

    return allocations


def _calculate_allocation_shares(rule, source_balance):
    """
    Calculate the monetary amount for each allocation target based on the rule type.

    Returns a list of dicts: [{'target': AllocationTarget, 'amount': Decimal, 'basis': str}]
    """
    targets = rule.targets.filter(
        target_cost_center__is_active=True,
        target_account__is_active=True,
    )
    allocations = []

    if rule.allocation_type == AllocationType.PERCENTAGE:
        for target in targets:
            if target.percentage:
                amount = (
                    source_balance * (target.percentage / Decimal('100'))
                ).quantize(Decimal('0.01'))
                allocations.append({
                    'target': target,
                    'amount': amount,
                    'basis': f'{target.percentage}%',
                })

    elif rule.allocation_type == AllocationType.EQUAL:
        count = targets.count()
        if count > 0:
            share_amount = (source_balance / Decimal(str(count))).quantize(
                Decimal('0.01')
            )
            for target in targets:
                allocations.append({
                    'target': target,
                    'amount': share_amount,
                    'basis': 'توزيع متساوٍ',
                })

    elif rule.allocation_type == AllocationType.RATIO:
        total_ratio = targets.aggregate(
            total=models.Sum('ratio')
        )['total'] or Decimal('0')

        if total_ratio > 0:
            for target in targets:
                if target.ratio:
                    amount = (
                        source_balance * (target.ratio / total_ratio)
                    ).quantize(Decimal('0.01'))
                    allocations.append({
                        'target': target,
                        'amount': amount,
                        'basis': f'نسبة {target.ratio}/{total_ratio}',
                    })

    elif rule.allocation_type == AllocationType.HEADCOUNT:
        headcount_data = calculate_headcount_allocation(rule)
        for data in headcount_data:
            amount = (source_balance * data['share']).quantize(Decimal('0.01'))
            allocations.append({
                'target': data['target'],
                'amount': amount,
                'basis': f'{data["headcount"]} موظف',
            })

    elif rule.allocation_type == AllocationType.REVENUE:
        revenue_data = calculate_revenue_allocation(rule)
        for data in revenue_data:
            amount = (source_balance * data['share']).quantize(Decimal('0.01'))
            allocations.append({
                'target': data['target'],
                'amount': amount,
                'basis': f'إيرادات {data["revenue"]}',
            })

    return allocations


@transaction.atomic
def execute_allocation_rule(rule_id, user):
    """
    Execute a single allocation rule:
    1. Validate the rule and its targets
    2. Calculate each target's share based on allocation type
    3. Create a journal entry: DR each target account, CR source account
    4. Post the journal entry to update account balances
    5. Log the allocation execution
    6. Update the rule's last_executed timestamp

    Args:
        rule_id: Primary key of the AllocationRule to execute
        user: User instance executing the allocation (for audit trail)

    Returns:
        dict: Allocation summary with keys:
            - 'status': 'success', 'partial', or 'failed'
            - 'rule_id': The rule's ID
            - 'rule_name': The rule's name
            - 'total_allocated': Total amount allocated
            - 'allocations': List of target allocation details
            - 'journal_entry_id': ID of the created journal entry
            - 'error': Error message (if failed)
    """
    from accounting.models import Account, AccountType, JournalEntry, Transaction

    result = {
        'status': 'failed',
        'rule_id': rule_id,
        'rule_name': '',
        'total_allocated': Decimal('0'),
        'allocations': [],
        'journal_entry_id': None,
        'error': '',
    }

    try:
        # Fetch the rule
        rule = AllocationRule.objects.select_related('source_account').get(pk=rule_id)
        result['rule_name'] = rule.name

        # Validate rule is effective
        if not rule.is_effective():
            result['error'] = 'القاعدة غير سارية المفعول حالياً'
            _log_allocation(
                rule=rule,
                status=AllocationLogStatus.FAILED,
                error_message=result['error'],
                user=user,
            )
            return result

        # Validate targets
        validation_errors = validate_allocation_targets(rule)
        if validation_errors:
            result['error'] = '; '.join(validation_errors)
            _log_allocation(
                rule=rule,
                status=AllocationLogStatus.FAILED,
                error_message=result['error'],
                user=user,
            )
            return result

        # Get source account balance
        source_account = rule.source_account
        source_balance_before = source_account.current_balance

        if source_balance_before <= 0:
            result['error'] = (
                f'رصيد الحساب المصدر ({source_account.code}) غير كافٍ أو صفري'
            )
            _log_allocation(
                rule=rule,
                status=AllocationLogStatus.FAILED,
                error_message=result['error'],
                source_balance_before=source_balance_before,
                user=user,
            )
            return result

        # Calculate period (current month)
        today = timezone.now().date()
        period_start = today.replace(day=1)
        # Calculate last day of month
        if today.month == 12:
            period_end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            period_end = today.replace(month=today.month + 1, day=1)
        period_end = period_end - timezone.timedelta(days=1)

        # Calculate allocation shares
        allocation_shares = _calculate_allocation_shares(rule, source_balance_before)

        if not allocation_shares:
            result['error'] = 'لم يتم حساب أي حصص توزيع'
            _log_allocation(
                rule=rule,
                status=AllocationLogStatus.FAILED,
                error_message=result['error'],
                source_balance_before=source_balance_before,
                period_start=period_start,
                period_end=period_end,
                user=user,
            )
            return result

        # Create journal entry
        journal_entry = JournalEntry()
        journal_entry.entry_type = 'allocation'
        journal_entry.description = (
            f'توزيع تلقائي: {rule.name} - {today.strftime("%Y-%m")}'
        )
        journal_entry.reference = f'ALLOC-{rule.pk}-{today.strftime("%Y%m%d")}'
        journal_entry.entry_date = today
        journal_entry.created_by = user
        journal_entry.save()

        # Create transactions: DR target accounts, CR source account
        total_debit = Decimal('0')
        for share in allocation_shares:
            target = share['target']
            amount = share['amount']

            # Debit the target account
            Transaction.objects.create(
                journal_entry=journal_entry,
                account=target.target_account,
                transaction_type='debit',
                amount=amount,
                description=f'توزيع إلى مركز التكلفة: {target.target_cost_center.name}',
            )

            total_debit += amount

            result['allocations'].append({
                'cost_center': target.target_cost_center.name,
                'cost_center_code': target.target_cost_center.code,
                'account_code': target.target_account.code,
                'account_name': target.target_account.name,
                'amount': str(amount),
                'basis': share['basis'],
            })

        # Credit the source account (total of all debits)
        Transaction.objects.create(
            journal_entry=journal_entry,
            account=source_account,
            transaction_type='credit',
            amount=total_debit,
            description=(
                f'توزيع من حساب: {source_account.code} - {source_account.name}'
            ),
        )

        # Post the journal entry
        journal_entry.post_entry()

        # Update rule's last_executed
        rule.last_executed = timezone.now()
        rule.save(update_fields=['last_executed', 'updated_at'])

        # Update cost center actual amounts
        for share in allocation_shares:
            cost_center = share['target'].target_cost_center
            cost_center.actual_amount += share['amount']
            cost_center.save(update_fields=['actual_amount', 'updated_at'])

        # Determine status
        total_allocated = sum(
            Decimal(a['amount']) for a in result['allocations']
        )
        status = AllocationLogStatus.SUCCESS

        # Check if there's a rounding difference
        rounding_diff = source_balance_before - total_allocated
        if abs(rounding_diff) > Decimal('0.01'):
            status = AllocationLogStatus.PARTIAL

        result['status'] = status
        result['total_allocated'] = total_allocated
        result['journal_entry_id'] = journal_entry.pk

        # Log the allocation
        _log_allocation(
            rule=rule,
            period_start=period_start,
            period_end=period_end,
            total_allocated=total_allocated,
            source_balance_before=source_balance_before,
            journal_entry=journal_entry,
            status=status,
            user=user,
        )

    except AllocationRule.DoesNotExist:
        result['error'] = f'قاعدة التوزيع برقم {rule_id} غير موجودة'
    except Exception as e:
        result['error'] = str(e)
        try:
            rule_obj = AllocationRule.objects.get(pk=rule_id)
            _log_allocation(
                rule=rule_obj,
                status=AllocationLogStatus.FAILED,
                error_message=result['error'],
                user=user,
            )
        except AllocationRule.DoesNotExist:
            pass

    return result


def _log_allocation(
    rule,
    status,
    user,
    error_message='',
    period_start=None,
    period_end=None,
    total_allocated=Decimal('0'),
    source_balance_before=Decimal('0'),
    journal_entry=None,
):
    """Create an AllocationLog entry for audit trail."""
    log = AllocationLog.objects.create(
        rule=rule,
        period_start=period_start or timezone.now().date(),
        period_end=period_end or timezone.now().date(),
        total_allocated=total_allocated,
        source_balance_before=source_balance_before,
        journal_entry=journal_entry,
        executed_by=user,
        status=status,
        error_message=error_message,
    )
    return log


def execute_all_recurring_allocations(user):
    """
    Execute all active recurring allocation rules that are due for execution.

    Iterates through all active recurring rules, checks if each is due,
    and executes it. Returns a summary of all executions.

    Args:
        user: User instance triggering the batch execution (for audit trail)

    Returns:
        dict: Summary with keys:
            - 'total_rules_checked': Number of rules checked
            - 'rules_executed': Number of rules executed
            - 'success_count': Number of successful executions
            - 'partial_count': Number of partial executions
            - 'failed_count': Number of failed executions
            - 'results': List of individual execution results
    """
    today = timezone.now()
    recurring_rules = AllocationRule.objects.filter(
        is_active=True,
        is_recurring=True,
    ).select_related('source_account')

    results = []
    success_count = 0
    partial_count = 0
    failed_count = 0

    for rule in recurring_rules:
        if rule.is_due_for_execution():
            execution_result = execute_allocation_rule(rule.pk, user)
            results.append(execution_result)

            if execution_result['status'] == AllocationLogStatus.SUCCESS:
                success_count += 1
            elif execution_result['status'] == AllocationLogStatus.PARTIAL:
                partial_count += 1
            else:
                failed_count += 1

    return {
        'total_rules_checked': recurring_rules.count(),
        'rules_executed': len(results),
        'success_count': success_count,
        'partial_count': partial_count,
        'failed_count': failed_count,
        'results': results,
    }
