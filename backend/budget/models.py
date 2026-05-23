"""
Budget Management Models for ERP System.
Manages Budgets, BudgetCategories, BudgetItems, BudgetTransfers, and BudgetExpenses.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class Budget(models.Model):
    """الميزانية - Budget for a fiscal year and optional department."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('approved', 'معتمدة'),
        ('active', 'نشطة'),
        ('closed', 'مغلقة'),
    )

    name = models.CharField(
        max_length=200,
        verbose_name='الاسم',
    )
    fiscal_year = models.IntegerField(
        verbose_name='السنة المالية',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='القسم',
    )
    total_budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='إجمالي الميزانية',
    )
    utilized_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المستخدم',
    )
    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المتبقي',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
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
        ordering = ['-fiscal_year', 'name']
        verbose_name = 'ميزانية'
        verbose_name_plural = 'الميزانيات'

    def __str__(self):
        return self.name


class BudgetCategory(models.Model):
    """فئة الميزانية - Category within a budget."""

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='الميزانية',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='الاسم',
    )
    allocated_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ المخصص',
    )
    utilized_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المستخدم',
    )
    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المتبقي',
    )
    account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الحساب',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'فئة الميزانية'
        verbose_name_plural = 'فئات الميزانية'

    def __str__(self):
        return f'{self.name} - {self.budget.name}'


class BudgetItem(models.Model):
    """بند الميزانية - Individual item within a budget category."""

    STATUS_CHOICES = (
        ('under_budget', 'أقل من الميزانية'),
        ('on_track', 'على المسار'),
        ('over_budget', 'أكثر من الميزانية'),
    )

    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الفئة',
    )
    description = models.CharField(
        max_length=500,
        verbose_name='الوصف',
    )
    planned_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ المخطط',
    )
    actual_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ الفعلي',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='on_track',
        verbose_name='الحالة',
        db_index=True,
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
        ordering = ['description']
        verbose_name = 'بند الميزانية'
        verbose_name_plural = 'بنود الميزانية'

    def __str__(self):
        return self.description

    @property
    def variance(self):
        """الفرق بين المبلغ المخطط والفعلي"""
        return self.planned_amount - self.actual_amount


class BudgetTransfer(models.Model):
    """تحويل ميزانية - Transfer budget amounts between budgets."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('rejected', 'مرفوضة'),
    )

    from_budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='transfers_out',
        verbose_name='من ميزانية',
    )
    to_budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='transfers_in',
        verbose_name='إلى ميزانية',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    reason = models.TextField(
        verbose_name='السبب',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='وافق بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تحويل ميزانية'
        verbose_name_plural = 'تحويلات الميزانية'

    def __str__(self):
        return f'{self.from_budget.name} ← {self.to_budget.name} - {self.amount}'


class BudgetExpense(models.Model):
    """مصروف الميزانية - Expense recorded against a budget."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('rejected', 'مرفوضة'),
    )

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='الميزانية',
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name='الفئة',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    description = models.CharField(
        max_length=500,
        verbose_name='الوصف',
    )
    expense_date = models.DateField(
        verbose_name='تاريخ المصروف',
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='رقم المرجع',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='وافق بواسطة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مصروف الميزانية'
        verbose_name_plural = 'مصروفات الميزانية'

    def __str__(self):
        return f'{self.description} - {self.amount}'
