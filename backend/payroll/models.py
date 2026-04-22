"""
Payroll Models for ERP System.
Manages PayrollPeriods, PayrollRecords, SalaryAdvances, EmployeeLoans, and EndOfServiceBenefits.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class PayrollPeriod(models.Model):
    """Payroll period representing a specific month/year for salary processing."""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('processing', 'قيد المعالجة'),
        ('paid', 'مدفوع'),
        ('closed', 'مغلق'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name='الاسم',
        help_text='مثال: يناير 2025',
    )
    month = models.IntegerField(
        verbose_name='الشهر',
        help_text='رقم الشهر (1-12)',
    )
    year = models.IntegerField(
        verbose_name='السنة',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    total_employees = models.IntegerField(
        default=0,
        verbose_name='إجمالي الموظفين',
    )
    total_salaries = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الرواتب',
    )
    total_deductions = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الخصومات',
    )
    total_net = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='صافي الإجمالي',
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
        ordering = ['-year', '-month']
        verbose_name = 'فترة الرواتب'
        verbose_name_plural = 'فترات الرواتب'

    def __str__(self):
        return self.name


class PayrollRecord(models.Model):
    """Individual payslip record for an employee within a payroll period."""

    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'تحويل بنكي'),
        ('cash', 'نقدي'),
        ('cheque', 'شيك'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('paid', 'مدفوع'),
        ('partially_paid', 'مدفوع جزئياً'),
    )

    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='الفترة',
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_records',
        verbose_name='الموظف',
    )

    # Earnings
    basic_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='الراتب الأساسي',
    )
    housing_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='بدل السكن',
    )
    transport_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='بدل النقل',
    )
    food_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='بدل الطعام',
    )
    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='ساعات الإضافي',
    )
    overtime_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ الإضافي',
    )
    bonus = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المكافأة',
    )
    commission = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='العمولة',
    )

    # Deductions
    deductions_gosi = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='خصم التأمينات الاجتماعية (GOSI)',
    )
    deductions_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='خصم الضريبة',
    )
    deductions_absence = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='خصم الغياب',
    )
    deductions_loan = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='خصم القروض',
    )
    deductions_other = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='خصومات أخرى',
    )
    deductions_other_description = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='وصف الخصومات الأخرى',
    )

    # Totals
    total_earnings = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الاستحقاقات',
    )
    total_deductions_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الخصومات',
    )
    net_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='صافي الراتب',
    )

    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer',
        verbose_name='طريقة الدفع',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الدفع',
        db_index=True,
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    bank_reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المرجع البنكي',
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
        related_name='payroll_records_created',
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
        unique_together = ('period', 'employee')
        verbose_name = 'سجل الراتب'
        verbose_name_plural = 'سجلات الرواتب'
        ordering = ['employee__first_name']

    def __str__(self):
        return f'{self.employee_name} - {self.period.name}'

    @property
    def computed_total_earnings(self):
        """Calculate total earnings from all earning components."""
        return (
            self.basic_salary
            + self.housing_allowance
            + self.transport_allowance
            + self.food_allowance
            + self.overtime_amount
            + self.bonus
            + self.commission
        )

    @property
    def computed_total_deductions(self):
        """Calculate total deductions from all deduction components."""
        return (
            self.deductions_gosi
            + self.deductions_tax
            + self.deductions_absence
            + self.deductions_loan
            + self.deductions_other
        )

    @property
    def computed_net_salary(self):
        """Calculate net salary = total earnings - total deductions."""
        return self.computed_total_earnings - self.computed_total_deductions

    @property
    def employee_name(self):
        return self.employee.full_name if self.employee else ''

    @property
    def employee_number(self):
        return self.employee.employee_number if self.employee else ''

    @property
    def department_name(self):
        return self.employee.department.name if self.employee and self.employee.department else ''

    def recalculate(self):
        """Recalculate totals and save."""
        self.total_earnings = self.computed_total_earnings
        self.total_deductions_amount = self.computed_total_deductions
        self.net_salary = self.computed_net_salary
        self.save(update_fields=[
            'total_earnings', 'total_deductions_amount', 'net_salary', 'updated_at'
        ])


class SalaryAdvance(models.Model):
    """Salary advance (سلفة) request for employees."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('rejected', 'مرفوضة'),
        ('paid', 'مدفوعة'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='advances',
        verbose_name='الموظف',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    purpose = models.CharField(
        max_length=200,
        verbose_name='الغرض',
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
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    monthly_deduction = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الخصم الشهري',
    )
    months_remaining = models.IntegerField(
        default=0,
        verbose_name='الأشهر المتبقية',
    )
    advance_date = models.DateField(
        verbose_name='تاريخ السلفة',
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
        verbose_name = 'سلفة'
        verbose_name_plural = 'السلف'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.amount} ريال ({self.get_status_display()})'


class EmployeeLoan(models.Model):
    """Employee loan (قرض) with installment tracking."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
        ('defaulted', 'متعثر'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='الموظف',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='مبلغ القرض',
    )
    monthly_installment = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='القسط الشهري',
    )
    months = models.IntegerField(
        verbose_name='عدد الأشهر',
    )
    months_remaining = models.IntegerField(
        verbose_name='الأشهر المتبقية',
    )
    purpose = models.CharField(
        max_length=200,
        verbose_name='الغرض',
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
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
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
        verbose_name = 'قرض'
        verbose_name_plural = 'القروض'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.amount} ريال ({self.get_status_display()})'


class EndOfServiceBenefit(models.Model):
    """End of service benefit (مكافأة نهاية الخدمة) calculation and tracking."""

    STATUS_CHOICES = (
        ('calculated', 'محسوبة'),
        ('paid', 'مدفوعة'),
        ('partial', 'مدفوعة جزئياً'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='end_of_service',
        verbose_name='الموظف',
    )
    years_of_service = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='سنوات الخدمة',
    )
    total_service_days = models.IntegerField(
        verbose_name='إجمالي أيام الخدمة',
    )
    last_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='آخر راتب',
    )
    total_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='إجمالي المكافأة',
    )
    deduction_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ الخصم',
    )
    net_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='صافي المكافأة',
    )
    calculation_date = models.DateField(
        verbose_name='تاريخ الحساب',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='calculated',
        verbose_name='الحالة',
        db_index=True,
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
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
        verbose_name = 'مكافأة نهاية خدمة'
        verbose_name_plural = 'مكافآت نهاية الخدمة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee_name} - {self.net_benefit} ريال ({self.get_status_display()})'

    @property
    def employee_name(self):
        return self.employee.full_name if self.employee else ''
