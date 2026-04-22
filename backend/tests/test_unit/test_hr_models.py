"""
اختبارات الوحدات البرمجية لنماذج الموارد البشرية.
Unit Tests for HR Models.
"""

import pytest
from datetime import date, time, timedelta


class TestDepartmentModel:
    """اختبارات نموذج القسم."""

    def test_create_department(self, department):
        """اختبار إنشاء قسم."""
        assert department.name == 'قسم التقنية'
        assert department.name_en == 'IT Department'
        assert department.is_active is True

    def test_department_str(self, department):
        """اختبار التمثيل النصي."""
        assert department.name == str(department)

    def test_employees_count(self, db):
        """اختبار عداد الموظفين."""
        from hr.models import Department, Employee
        from users.models import User
        dept = Department.objects.create(name='قسم الاختبار', name_en='Test Dept')
        user1 = User.objects.create_user(username='emp1', password='Emp@1234!', role='sales')
        user2 = User.objects.create_user(username='emp2', password='Emp@1234!', role='sales')
        Employee.objects.create(user=user1, department=dept, hire_date=date.today(), salary=5000)
        Employee.objects.create(user=user2, department=dept, hire_date=date.today(), salary=6000)
        assert dept.employees_count == 2


class TestEmployeeModel:
    """اختبارات نموذج الموظف."""

    def test_create_employee(self, db):
        """اختبار إنشاء موظف."""
        from hr.models import Employee
        from users.models import User
        user = User.objects.create_user(username='emp_test', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(
            user=user,
            first_name='أحمد',
            last_name='محمد',
            email='ahmed@test.com',
            phone='0501234567',
            department=None,
            hire_date=date.today(),
            salary=8000,
        )
        assert emp.full_name == 'أحمد محمد'
        assert emp.total_salary == 8000

    def test_employee_number_auto(self, db):
        """اختبار التوليد التلقائي لرقم الموظف."""
        from hr.models import Employee
        from users.models import User
        user = User.objects.create_user(username='auto_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(
            user=user, hire_date=date.today(), salary=5000,
        )
        assert emp.employee_number.startswith('EMP-')

    def test_total_salary_with_allowances(self, db):
        """اختبار الراتب الإجمالي مع البدلات."""
        from hr.models import Employee
        from users.models import User
        user = User.objects.create_user(username='allow_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(
            user=user,
            hire_date=date.today(),
            salary=7000,
            housing_allowance=1500,
            transport_allowance=500,
        )
        assert emp.total_salary == 9000


class TestAttendanceModel:
    """اختبارات نموذج الحضور."""

    def test_create_attendance(self, db):
        """اختبار تسجيل حضور."""
        from hr.models import Attendance, Employee
        from users.models import User
        user = User.objects.create_user(username='att_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=5000)
        att = Attendance.objects.create(
            employee=emp,
            date=date.today(),
            check_in=time(8, 0),
            check_out=time(17, 0),
            status='present',
        )
        assert att.hours_worked == 9.0

    def test_unique_employee_date(self, db):
        """اختبار عدم تكرار الحضور لنفس الموظف في نفس اليوم."""
        from hr.models import Attendance, Employee
        from users.models import User
        user = User.objects.create_user(username='dup_att', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=5000)
        Attendance.objects.create(
            employee=emp, date=date.today(),
            check_in=time(8, 0), check_out=time(17, 0), status='present',
        )
        with pytest.raises(Exception):
            Attendance.objects.create(
                employee=emp, date=date.today(),
                check_in=time(9, 0), status='present',
            )

    def test_absent_hours_worked(self, db):
        """اختبار ساعات العمل للحالة غائب."""
        from hr.models import Attendance, Employee
        from users.models import User
        user = User.objects.create_user(username='abs_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=5000)
        att = Attendance.objects.create(
            employee=emp, date=date.today(), status='absent',
        )
        assert att.hours_worked == 0


class TestLeaveRequestModel:
    """اختبارات نموذج طلبات الإجازة."""

    def test_create_leave_request(self, db):
        """اختبار إنشاء طلب إجازة."""
        from hr.models import LeaveRequest, Employee
        from users.models import User
        user = User.objects.create_user(username='leave_emp', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=5000)
        leave = LeaveRequest.objects.create(
            employee=emp,
            leave_type='annual',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            reason='إجازة سنوية',
        )
        assert leave.approval_status == 'pending'
        assert leave.days == 5

    def test_leave_days_calculation(self, db):
        """اختبار حساب عدد أيام الإجازة."""
        from hr.models import LeaveRequest, Employee
        from users.models import User
        user = User.objects.create_user(username='leave_calc', password='Emp@1234!', role='sales')
        emp = Employee.objects.create(user=user, hire_date=date.today(), salary=5000)
        leave = LeaveRequest.objects.create(
            employee=emp,
            leave_type='sick',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason='مراجعة طبية',
        )
        assert leave.days == 3  # inclusive
