"""
Employee Finance Models for ERP System.
Manages Loans (القروض), Salary Advances (السلف), and Overtime Requests (طلبات الأجور الإضافية).
Includes installment tracking, auto-calculated deductions, and overtime rate computation.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


# =============================================
# Helper Functions
# =============================================

def generate_loan_number():
    """Generate a unique loan number: LOAN-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'LOAN-{today}-'

    from hr.models import Loan
    last_loan = Loan.objects.filter(
        loan_number__startswith=prefix,
    ).order_by('-loan_number').first()

    if last_loan:
        try:
            seq = int(last_loan.loan_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def generate_advance_number():
    """Generate a unique salary advance number: ADV-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'ADV-{today}-'

    from hr.models import SalaryAdvance
    last_advance = SalaryAdvance.objects.filter(
        advance_number__startswith=prefix,
    ).order_by('-advance_number').first()

    if last_advance:
        try:
            seq = int(last_advance.advance_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def calculate_monthly_installment(amount, months, interest_rate):
    """
    Calculate Equated Monthly Installment (EMI) using the reducing balance formula.

    EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)

    Where:
        P = principal loan amount
        r = monthly interest rate (annual rate / 12 / 100)
        n = number of repayment months

    If interest_rate is 0, returns simple division: amount / months.
    """
    amount = Decimal(str(amount))
    months = int(months)
    interest_rate = Decimal(str(interest_rate))

    if months <= 0:
        return Decimal('0')

    if interest_rate <= 0:
        return (amount / months).quantize(Decimal('0.01'))

    monthly_rate = interest_rate / Decimal('100') / Decimal('12')
    power = (Decimal('1') + monthly_rate) ** months

    emi = amount * monthly_rate * power / (power - Decimal('1'))
    return emi.quantize(Decimal('0.01'))


def calculate_overtime_rate(employee, overtime_type):
    """
    Calculate hourly overtime rate based on employee salary and overtime type.

    Base hourly rate = total_salary / 30 days / 8 hours

    Rate multipliers by overtime type:
        - regular:  1.5x
        - holiday:  2.0x
        - weekend:  1.5x
        - night:    1.25x

    Returns a tuple of (hourly_rate, rate_multiplier).
    """
    from hr.models import Employee

    if not isinstance(employee, Employee) and isinstance(employee, int):
        employee = Employee.objects.get(pk=employee)

    total_salary = employee.total_salary  # basic + housing + transport
    base_hourly_rate = total_salary / Decimal('30') / Decimal('8')

    rate_multipliers = {
        'regular': Decimal('1.5'),
        'holiday': Decimal('2.0'),
        'weekend': Decimal('1.5'),
        'night': Decimal('1.25'),
    }

    multiplier = rate_multipliers.get(overtime_type, Decimal('1.5'))
    hourly_rate = (base_hourly_rate * multiplier).quantize(Decimal('0.01'))

    return hourly_rate, multiplier


# =============================================
# Loan Model (قرض)
# =============================================

class Loan(models.Model):
    """Employee loan with installment tracking and guarantor support."""

    LOAN_TYPE_CHOICES = (
        ('personal', 'شخصي'),
        ('emergency', 'طارئ'),
        ('housing', 'سكن'),
        ('education', 'تعليم'),
        ('car', 'سيارة'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
        ('defaulted', 'متعثر'),
        ('cancelled', 'ملغي'),
    )

    loan_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم القرض',
        db_index=True,
        editable=False,
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='hr_loans',
        verbose_name='الموظف',
    )
    loan_type = models.CharField(
        max_length=20,
        choices=LOAN_TYPE_CHOICES,
        verbose_name='نوع القرض',
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مبلغ القرض',
        help_text='مبلغ القرض الإجمالي بالريال السعودي',
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة الفائدة',
        help_text='النسبة السنوية للفائدة (مثال: 5.00 يعني 5%)',
    )
    repayment_period_months = models.IntegerField(
        verbose_name='فترة السداد (بالأشهر)',
        help_text='عدد الأشهر لسداد القرض',
    )
    monthly_installment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='القسط الشهري',
        help_text='يُحسب تلقائياً من المبلغ والفائدة وفترة السداد',
    )
    total_remaining = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='المتبقي الإجمالي',
        help_text='يُتتبع تلقائياً بناءً على الأقساط المدفوعة',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
        db_index=True,
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    purpose = models.TextField(
        blank=True,
        default='',
        verbose_name='الغرض من القرض',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loans_approved',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    guarantor = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الكفيل',
        help_text='اسم الكفيل إذا كان من خارج الشركة',
    )
    guarantor_employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guaranteed_loans',
        verbose_name='موظف كفيل',
        help_text='الكفيل إذا كان موظفاً في الشركة',
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
        return f'{self.loan_number} - {self.employee.full_name} - {self.amount} ريال ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.loan_number:
            self.loan_number = generate_loan_number()

        # Auto-calculate monthly installment
        if self.amount and self.repayment_period_months:
            self.monthly_installment = calculate_monthly_installment(
                self.amount,
                self.repayment_period_months,
                self.interest_rate,
            )

        # Initialize total_remaining on first save if not set
        if not kwargs.get('update_fields') and self.total_remaining == 0 and self.amount:
            self.total_remaining = self.amount

        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        """Calculate total amount paid through installment payments."""
        return self.payments.filter(status='paid').aggregate(
            total=models.Sum('paid_amount'),
        )['total'] or Decimal('0')

    @property
    def progress_percentage(self):
        """Calculate loan repayment progress as a percentage."""
        if self.amount <= 0:
            return 0
        paid = self.total_paid
        return min(round(float(paid / self.amount * 100), 1), 100)

    @property
    def installments_paid_count(self):
        """Count of fully paid installments."""
        return self.payments.filter(status='paid').count()

    @property
    def installments_overdue_count(self):
        """Count of overdue installments."""
        return self.payments.filter(status='overdue').count()


# =============================================
# Loan Payment Model (قسط قرض)
# =============================================

class LoanPayment(models.Model):
    """Individual installment payment for a loan."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('paid', 'مدفوع'),
        ('overdue', 'متأخر'),
        ('partial', 'مدفوع جزئياً'),
    )

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='القرض',
    )
    payment_number = models.IntegerField(
        verbose_name='رقم القسط',
        help_text='الترتيب التسلسلي للقسط ضمن القرض',
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مبلغ القسط',
        help_text='المبلغ المطلوب سداده في هذا القسط',
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المدفوع',
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    payslip = models.ForeignKey(
        'hr.Payslip',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_payments',
        verbose_name='قسيمة الراتب',
        help_text='قسيمة الراتب التي تم خصم القسط منها',
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
        verbose_name = 'قسط قرض'
        verbose_name_plural = 'أقساط القروض'
        constraints = [
            models.UniqueConstraint(
                fields=['loan', 'payment_number'],
                name='unique_loan_payment_number',
            ),
        ]
        ordering = ['loan', 'payment_number']

    def __str__(self):
        return f'{self.loan.loan_number} - قسط #{self.payment_number} - {self.amount} ريال ({self.get_status_display()})'

    @property
    def remaining_amount(self):
        """Calculate remaining amount for this installment."""
        return self.amount - self.paid_amount

    def save(self, *args, **kwargs):
        # Auto-update status based on paid_amount
        if self.paid_amount <= 0:
            self.status = 'pending'
        elif self.paid_amount >= self.amount:
            self.status = 'paid'
            if not self.payment_date:
                self.payment_date = timezone.now().date()
        else:
            self.status = 'partial'

        # Check if overdue
        if self.status == 'pending' and self.due_date < timezone.now().date():
            self.status = 'overdue'

        super().save(*args, **kwargs)

        # Update loan total_remaining after saving
        self._update_loan_remaining()

    def _update_loan_remaining(self):
        """Recalculate the loan's total_remaining after a payment change."""
        from django.db.models import Sum

        total_paid = self.loan.payments.filter(status='paid').aggregate(
            total=Sum('paid_amount'),
        )['total'] or Decimal('0')

        remaining = self.loan.amount - total_paid
        if remaining < 0:
            remaining = Decimal('0')

        Loan.objects.filter(pk=self.loan.pk).update(
            total_remaining=remaining,
        )

        # Auto-complete loan if fully paid
        if remaining <= 0 and self.loan.status == 'active':
            Loan.objects.filter(pk=self.loan.pk).update(status='completed')


# =============================================
# Salary Advance Model (سلفة)
# =============================================

class SalaryAdvance(models.Model):
    """Employee salary advance request with repayment tracking."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('partially_deducted', 'مخصوص جزئياً'),
        ('fully_deducted', 'مخصوص بالكامل'),
        ('rejected', 'مرفوضة'),
    )

    advance_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم السلفة',
        db_index=True,
        editable=False,
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='hr_salary_advances',
        verbose_name='الموظف',
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='مبلغ السلفة',
        help_text='مبلغ السلفة المطلوب بالريال السعودي',
    )
    reason = models.TextField(
        verbose_name='السبب',
        help_text='سبب طلب السلفة',
    )
    repayment_months = models.IntegerField(
        default=1,
        verbose_name='عدد أشهر السداد',
        help_text='على كم شهر سيتم توزيع الخصم',
    )
    monthly_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='الخصم الشهري',
        help_text='يُحسب تلقائياً: المبلغ / عدد الأشهر',
    )
    total_deducted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي المخصوص',
        help_text='يُتتبع تلقائياً من قسائم الرواتب',
    )
    total_remaining = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='المتبقي',
        help_text='يُحسب تلقائياً: المبلغ - المخصوص',
    )
    request_date = models.DateField(
        verbose_name='تاريخ الطلب',
        db_index=True,
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
        related_name='salary_advances_approved',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
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
        return f'{self.advance_number} - {self.employee.full_name} - {self.amount} ريال ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.advance_number:
            self.advance_number = generate_advance_number()

        # Auto-calculate monthly deduction
        if self.amount and self.repayment_months and self.repayment_months > 0:
            self.monthly_deduction = (self.amount / self.repayment_months).quantize(Decimal('0.01'))

        # Auto-calculate total_remaining
        self.total_remaining = self.amount - self.total_deducted
        if self.total_remaining < 0:
            self.total_remaining = Decimal('0')

        # Auto-update status based on deduction progress
        if self.total_deducted >= self.amount and self.amount > 0:
            self.status = 'fully_deducted'
        elif self.total_deducted > 0:
            self.status = 'partially_deducted'

        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        """Calculate advance repayment progress as a percentage."""
        if self.amount <= 0:
            return 0
        return min(round(float(self.total_deducted / self.amount * 100), 1), 100)

    @property
    def months_remaining(self):
        """Calculate remaining repayment months."""
        if self.monthly_deduction <= 0:
            return 0
        remaining = self.total_remaining / self.monthly_deduction
        import math
        return math.ceil(float(remaining))


# =============================================
# Overtime Request Model (طلب أجور إضافية)
# =============================================

class OvertimeRequest(models.Model):
    """Employee overtime request with rate calculation and payslip integration."""

    OVERTIME_TYPE_CHOICES = (
        ('regular', 'عادي'),
        ('holiday', 'إجازة رسمية'),
        ('weekend', 'عطلة نهاية الأسبوع'),
        ('night', 'ليلي'),
    )

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('paid', 'مدفوع'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='overtime_requests',
        verbose_name='الموظف',
    )
    date = models.DateField(
        verbose_name='التاريخ',
        db_index=True,
    )
    start_time = models.TimeField(
        verbose_name='وقت البداية',
    )
    end_time = models.TimeField(
        verbose_name='وقت النهاية',
    )
    hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='عدد الساعات',
        help_text='يُحسب تلقائياً من وقت البداية والنهاية',
    )
    overtime_type = models.CharField(
        max_length=20,
        choices=OVERTIME_TYPE_CHOICES,
        default='regular',
        verbose_name='نوع العمل الإضافي',
        db_index=True,
    )
    rate_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal('1.5'),
        verbose_name='معامل المضاعفة',
        help_text='معدل مضاعفة الأجر: 1.0x, 1.5x, 2.0x',
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='معدل الأجر الساعي',
        help_text='يُحسب تلقائياً من راتب الموظف ونوع العمل الإضافي',
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='المبلغ الإجمالي',
        help_text='يُحسب تلقائياً: الساعات × معدل الأجر الساعي',
    )
    reason = models.TextField(
        blank=True,
        default='',
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
        related_name='overtime_approved',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    paid_in_payslip = models.BooleanField(
        default=False,
        verbose_name='مدفوع في قسيمة الراتب',
        db_index=True,
    )
    payslip = models.ForeignKey(
        'hr.Payslip',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overtime_entries',
        verbose_name='قسيمة الراتب',
        help_text='قسيمة الراتب التي تم صرف الأجر الإضافي فيها',
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
        verbose_name = 'طلب أجور إضافية'
        verbose_name_plural = 'طلبات الأجور الإضافية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.date} - {self.hours} ساعة ({self.get_overtime_type_display()}) - {self.get_status_display()}'

    def save(self, *args, **kwargs):
        # Auto-calculate hours from start_time and end_time
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta, time as dt_time

            dt_start = datetime.combine(self.date, self.start_time)
            dt_end = datetime.combine(self.date, self.end_time)

            # Handle overnight overtime (end time before start time)
            if dt_end <= dt_start:
                dt_end += timedelta(days=1)

            total_seconds = (dt_end - dt_start).total_seconds()
            calculated_hours = total_seconds / 3600
            self.hours = Decimal(str(round(calculated_hours, 2)))

        # Auto-calculate hourly rate and total amount if employee is set
        if self.employee and self.overtime_type:
            hourly_rate, multiplier = calculate_overtime_rate(
                self.employee, self.overtime_type,
            )
            self.hourly_rate = hourly_rate
            self.rate_multiplier = multiplier

        # Calculate total amount
        if self.hours and self.hourly_rate:
            self.total_amount = (self.hours * self.hourly_rate).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        """Human-readable overtime duration string."""
        return f'{self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")}'

    @property
    def rate_display(self):
        """Formatted rate multiplier string."""
        return f'{float(self.rate_multiplier):.1f}x'
