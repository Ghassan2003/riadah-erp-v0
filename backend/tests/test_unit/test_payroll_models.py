"""
اختبارات الوحدات البرمجية لنماذج نظام الرواتب.
Unit Tests for Payroll Models.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestPayrollPeriodModel:
    """اختبارات نموذج فترة الرواتب."""

    def test_create_payroll_period(self, db):
        """اختبار إنشاء فترة رواتب."""
        from payroll.models import PayrollPeriod
        period = PayrollPeriod.objects.create(
            name='يناير 2025',
            month=1,
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert period.name == 'يناير 2025'
        assert period.status == 'draft'
        assert period.total_employees == 0

    def test_payroll_period_str(self, db):
        """اختبار التمثيل النصي لفترة الرواتب."""
        from payroll.models import PayrollPeriod
        period = PayrollPeriod.objects.create(
            name='فبراير 2025',
            month=2,
            year=2025,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
        )
        assert str(period) == 'فبراير 2025'

    def test_payroll_period_ordering(self, db):
        """اختبار ترتيب فترات الرواتب (الأحدث أولاً)."""
        from payroll.models import PayrollPeriod
        p1 = PayrollPeriod.objects.create(name='يناير', month=1, year=2025, start_date=date(2025,1,1), end_date=date(2025,1,31))
        p2 = PayrollPeriod.objects.create(name='مارس', month=3, year=2025, start_date=date(2025,3,1), end_date=date(2025,3,31))
        periods = list(PayrollPeriod.objects.all())
        assert periods[0].month == 3  # مارس أولاً
        assert periods[1].month == 1

    def test_payroll_period_all_statuses(self, db):
        """اختبار جميع حالات فترة الرواتب."""
        from payroll.models import PayrollPeriod
        statuses = ['draft', 'processing', 'paid', 'closed']
        for st in statuses:
            PayrollPeriod.objects.create(
                name=f'فترة {st}',
                month=1, year=2025,
                start_date=date(2025,1,1), end_date=date(2025,1,31),
                status=st
            )
        assert PayrollPeriod.objects.filter(status='draft').count() == 1
        assert PayrollPeriod.objects.filter(status='closed').count() == 1


class TestPayrollRecordModel:
    """اختبارات نموذج سجل الراتب."""

    def _create_test_prerequisites(self, db):
        """إنشاء المتطلبات الأساسية للاختبار."""
        from payroll.models import PayrollPeriod
        from hr.models import Employee
        from users.models import User
        user = User.objects.create_user(username='emp_pay', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=8000)
        period = PayrollPeriod.objects.create(
            name='مارس 2025', month=3, year=2025,
            start_date=date(2025,3,1), end_date=date(2025,3,31)
        )
        return emp, period

    def test_create_payroll_record(self, db):
        """اختبار إنشاء سجل راتب."""
        from payroll.models import PayrollRecord
        emp, period = self._create_test_prerequisites(db)
        record = PayrollRecord.objects.create(
            period=period,
            employee=emp,
            basic_salary=Decimal('8000'),
            housing_allowance=Decimal('1500'),
            transport_allowance=Decimal('500'),
        )
        assert record.payment_status == 'pending'
        assert record.payment_method == 'bank_transfer'

    def test_computed_total_earnings(self, db):
        """اختبار حساب إجمالي الاستحقاقات."""
        from payroll.models import PayrollRecord
        emp, period = self._create_test_prerequisites(db)
        record = PayrollRecord.objects.create(
            period=period, employee=emp,
            basic_salary=Decimal('8000'),
            housing_allowance=Decimal('1500'),
            transport_allowance=Decimal('500'),
            food_allowance=Decimal('300'),
            overtime_amount=Decimal('500'),
            bonus=Decimal('1000'),
            commission=Decimal('200'),
        )
        assert record.computed_total_earnings == Decimal('12000')

    def test_computed_total_deductions(self, db):
        """اختبار حساب إجمالي الخصومات."""
        from payroll.models import PayrollRecord
        emp, period = self._create_test_prerequisites(db)
        record = PayrollRecord.objects.create(
            period=period, employee=emp,
            basic_salary=Decimal('8000'),
            deductions_gosi=Decimal('400'),
            deductions_tax=Decimal('100'),
            deductions_absence=Decimal('200'),
            deductions_loan=Decimal('500'),
            deductions_other=Decimal('100'),
        )
        assert record.computed_total_deductions == Decimal('1300')

    def test_computed_net_salary(self, db):
        """اختبار حساب صافي الراتب."""
        from payroll.models import PayrollRecord
        emp, period = self._create_test_prerequisites(db)
        record = PayrollRecord.objects.create(
            period=period, employee=emp,
            basic_salary=Decimal('8000'),
            housing_allowance=Decimal('1500'),
            deductions_gosi=Decimal('500'),
        )
        assert record.computed_net_salary == Decimal('9000')

    def test_recalculate_method(self, db):
        """اختبار طريقة إعادة الحساب."""
        from payroll.models import PayrollRecord
        emp, period = self._create_test_prerequisites(db)
        record = PayrollRecord.objects.create(
            period=period, employee=emp,
            basic_salary=Decimal('7000'),
            housing_allowance=Decimal('1000'),
            deductions_gosi=Decimal('400'),
        )
        record.recalculate()
        assert record.total_earnings == Decimal('8000')
        assert record.total_deductions_amount == Decimal('400')
        assert record.net_salary == Decimal('7600')

    def test_unique_period_employee(self, db):
        """اختبار عدم تكرار سجل نفس الموظف في نفس الفترة."""
        from payroll.models import PayrollRecord
        from django.db import IntegrityError
        emp, period = self._create_test_prerequisites(db)
        PayrollRecord.objects.create(
            period=period, employee=emp, basic_salary=Decimal('8000')
        )
        with pytest.raises(IntegrityError):
            PayrollRecord.objects.create(
                period=period, employee=emp, basic_salary=Decimal('8000')
            )

    def test_employee_name_property(self, db):
        """اختبار خاصية اسم الموظف."""
        from payroll.models import PayrollRecord
        from users.models import User
        from hr.models import Employee
        from payroll.models import PayrollPeriod
        user = User.objects.create_user(username='emp_name_t', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, first_name='أحمد', last_name='علي', hire_date=date.today(), salary=8000)
        period = PayrollPeriod.objects.create(name='اختبار اسم', month=1, year=2025, start_date=date(2025,1,1), end_date=date(2025,1,31))
        record = PayrollRecord.objects.create(
            period=period, employee=emp, basic_salary=Decimal('8000')
        )
        assert record.employee_name == 'أحمد علي'

    def test_record_str(self, db):
        """اختبار التمثيل النصي لسجل الراتب."""
        from payroll.models import PayrollRecord, PayrollPeriod
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='emp_str', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, first_name='أحمد', last_name='علي', hire_date=date.today(), salary=8000)
        period = PayrollPeriod.objects.create(name='أبريل 2025', month=4, year=2025, start_date=date(2025,4,1), end_date=date(2025,4,30))
        record = PayrollRecord.objects.create(period=period, employee=emp, basic_salary=Decimal('8000'))
        assert 'أحمد علي' in str(record)
        assert 'أبريل 2025' in str(record)


class TestSalaryAdvanceModel:
    """اختبارات نموذج السلف."""

    def test_create_salary_advance(self, db):
        """اختبار إنشاء سلفة."""
        from payroll.models import SalaryAdvance
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='adv_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=8000)
        advance = SalaryAdvance.objects.create(
            employee=emp,
            amount=Decimal('3000'),
            purpose='ظرف طارئ',
            advance_date=date.today(),
        )
        assert advance.status == 'pending'
        assert advance.months_remaining == 0

    def test_advance_str(self, db):
        """اختبار التمثيل النصي للسلفة."""
        from payroll.models import SalaryAdvance
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='adv_str', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, first_name='محمد', last_name='سالم', hire_date=date.today(), salary=8000)
        advance = SalaryAdvance.objects.create(
            employee=emp, amount=Decimal('5000'), purpose='سلفة', advance_date=date.today()
        )
        assert 'محمد سالم' in str(advance)
        assert '5000' in str(advance)

    def test_advance_status_choices(self, db):
        """اختبار حالات السلفة."""
        from payroll.models import SalaryAdvance
        statuses = ['pending', 'approved', 'rejected', 'paid']
        assert len(SalaryAdvance.STATUS_CHOICES) == len(statuses)


class TestEmployeeLoanModel:
    """اختبارات نموذج القروض."""

    def test_create_employee_loan(self, db):
        """اختبار إنشاء قرض."""
        from payroll.models import EmployeeLoan
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='loan_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=8000)
        loan = EmployeeLoan.objects.create(
            employee=emp,
            amount=Decimal('50000'),
            monthly_installment=Decimal('2500'),
            months=20,
            months_remaining=20,
            purpose='شراء سيارة',
            start_date=date.today(),
        )
        assert loan.status == 'pending'
        assert loan.months_remaining == 20

    def test_loan_str(self, db):
        """اختبار التمثيل النصي للقرض."""
        from payroll.models import EmployeeLoan
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='loan_str', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, first_name='خالد', last_name='عمري', hire_date=date.today(), salary=8000)
        loan = EmployeeLoan.objects.create(
            employee=emp, amount=Decimal('20000'), monthly_installment=Decimal('1000'),
            months=20, months_remaining=20, purpose='قرض', start_date=date.today()
        )
        assert 'خالد عمري' in str(loan)

    def test_loan_status_choices(self, db):
        """اختبار حالات القرض."""
        from payroll.models import EmployeeLoan
        expected = ['pending', 'approved', 'rejected', 'active', 'completed', 'defaulted']
        actual = [c[0] for c in EmployeeLoan.STATUS_CHOICES]
        assert actual == expected


class TestEndOfServiceBenefitModel:
    """اختبارات نموذج مكافأة نهاية الخدمة."""

    def test_create_end_of_service(self, db):
        """اختبار إنشاء مكافأة نهاية خدمة."""
        from payroll.models import EndOfServiceBenefit
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='eos_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=8000)
        eos = EndOfServiceBenefit.objects.create(
            employee=emp,
            years_of_service=Decimal('5.00'),
            total_service_days=1825,
            last_salary=Decimal('10000'),
            total_benefit=Decimal('50000'),
            net_benefit=Decimal('45000'),
            deduction_amount=Decimal('5000'),
            calculation_date=date.today(),
        )
        assert eos.status == 'calculated'
        assert eos.net_benefit == Decimal('45000')

    def test_employee_name_property(self, db):
        """اختبار خاصية اسم الموظف في مكافأة نهاية الخدمة."""
        from payroll.models import EndOfServiceBenefit
        from users.models import User
        from hr.models import Employee
        user = User.objects.create_user(username='eos_name', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, first_name='سعد', last_name='حسين', hire_date=date.today(), salary=8000)
        eos = EndOfServiceBenefit.objects.create(
            employee=emp, years_of_service=Decimal('3.00'), total_service_days=1095,
            last_salary=Decimal('8000'), total_benefit=Decimal('20000'),
            net_benefit=Decimal('20000'), calculation_date=date.today()
        )
        assert eos.employee_name == 'سعد حسين'
