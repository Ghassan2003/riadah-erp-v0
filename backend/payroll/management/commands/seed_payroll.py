"""
Management command to seed sample Payroll data.
Creates PayrollPeriod, SalaryAdvances, EmployeeLoans, and EndOfServiceBenefits
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum

from payroll.models import (
    PayrollPeriod,
    PayrollRecord,
    SalaryAdvance,
    EmployeeLoan,
    EndOfServiceBenefit,
)


class Command(BaseCommand):
    help = 'Seed sample payroll data for the ERP system'

    def handle(self, *args, **options):
        from hr.models import Employee
        from users.models import User

        self.stdout.write('Creating sample Payroll data...')

        # Ensure employees exist
        employees = list(Employee.objects.filter(is_active=True)[:8])
        if not employees:
            self.stdout.write(self.style.ERROR('  No active employees found. Run seed_hr first.'))
            return

        # Get an admin user for created_by fields
        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. Create PayrollPeriod for current month
        # =============================================
        now = timezone.now()
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر',
        }

        period_name = f'{month_names.get(now.month, str(now.month))} {now.year}'
        period, period_created = PayrollPeriod.objects.get_or_create(
            month=now.month,
            year=now.year,
            defaults={
                'name': period_name,
                'start_date': now.date().replace(day=1),
                'end_date': now.date().replace(day=28),
                'status': 'draft',
                'created_by': admin_user,
            },
        )
        if period_created:
            self.stdout.write(self.style.SUCCESS(f'  Created payroll period: {period.name}'))
        else:
            self.stdout.write(f'  Skipped (exists): {period.name}')

        # =============================================
        # 2. Create SalaryAdvances (8 records)
        # =============================================
        advances_data = [
            {'employee_idx': 0, 'amount': 3000, 'purpose': 'علاج أسنان', 'status': 'approved', 'monthly_deduction': 500, 'months_remaining': 6},
            {'employee_idx': 1, 'amount': 5000, 'purpose': 'رسوم جامعية', 'status': 'approved', 'monthly_deduction': 500, 'months_remaining': 10},
            {'employee_idx': 2, 'amount': 2000, 'purpose': 'إصلاح سيارة', 'status': 'paid', 'monthly_deduction': 1000, 'months_remaining': 0},
            {'employee_idx': 3, 'amount': 1500, 'purpose': 'مصاريف انتقال', 'status': 'pending', 'monthly_deduction': 0, 'months_remaining': 0},
            {'employee_idx': 4, 'amount': 4000, 'purpose': 'سداد ديون', 'status': 'approved', 'monthly_deduction': 800, 'months_remaining': 3},
            {'employee_idx': 5, 'amount': 2500, 'purpose': 'مصاريف زواج', 'status': 'pending', 'monthly_deduction': 0, 'months_remaining': 0},
            {'employee_idx': 6, 'amount': 1000, 'purpose': 'شراء جهاز', 'status': 'approved', 'monthly_deduction': 500, 'months_remaining': 1},
            {'employee_idx': 7, 'amount': 3500, 'purpose': 'مصاريف علاج', 'status': 'rejected', 'monthly_deduction': 0, 'months_remaining': 0},
        ]

        advance_count = 0
        for i, data in enumerate(advances_data):
            idx = data['employee_idx']
            if idx >= len(employees):
                continue
            emp = employees[idx]

            advance, created = SalaryAdvance.objects.get_or_create(
                employee=emp,
                purpose=data['purpose'],
                defaults={
                    'amount': Decimal(str(data['amount'])),
                    'status': data['status'],
                    'monthly_deduction': Decimal(str(data['monthly_deduction'])),
                    'months_remaining': data['months_remaining'],
                    'advance_date': now.date(),
                    'approved_by': admin_user if data['status'] in ('approved', 'rejected', 'paid') else None,
                    'approved_at': now if data['status'] in ('approved', 'rejected', 'paid') else None,
                },
            )
            if created:
                advance_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created advance: {advance.employee.full_name} - {advance.amount} ريال ({advance.get_status_display()})'))
            else:
                self.stdout.write(f'  Skipped (exists): {advance.employee.full_name} - {advance.purpose}')

        # =============================================
        # 3. Create EmployeeLoans (3 records)
        # =============================================
        loans_data = [
            {'employee_idx': 0, 'amount': 30000, 'monthly_installment': 2500, 'months': 12, 'purpose': 'بناء منزل', 'status': 'active', 'months_remaining': 8},
            {'employee_idx': 2, 'amount': 20000, 'monthly_installment': 2000, 'months': 10, 'purpose': 'شراء سيارة', 'status': 'active', 'months_remaining': 5},
            {'employee_idx': 4, 'amount': 15000, 'monthly_installment': 1500, 'months': 10, 'purpose': 'توسعة سكن', 'status': 'pending', 'months_remaining': 10},
        ]

        loan_count = 0
        for data in loans_data:
            idx = data['employee_idx']
            if idx >= len(employees):
                continue
            emp = employees[idx]

            from dateutil.relativedelta import relativedelta

            loan, created = EmployeeLoan.objects.get_or_create(
                employee=emp,
                purpose=data['purpose'],
                defaults={
                    'amount': Decimal(str(data['amount'])),
                    'monthly_installment': Decimal(str(data['monthly_installment'])),
                    'months': data['months'],
                    'months_remaining': data['months_remaining'],
                    'status': data['status'],
                    'start_date': now.date() - relativedelta(months=data['months'] - data['months_remaining']),
                    'end_date': now.date() + relativedelta(months=data['months_remaining']),
                    'approved_by': admin_user if data['status'] == 'active' else None,
                    'approved_at': now if data['status'] == 'active' else None,
                },
            )
            if created:
                loan_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created loan: {loan.employee.full_name} - {loan.amount} ريال ({loan.get_status_display()})'))
            else:
                self.stdout.write(f'  Skipped (exists): {loan.employee.full_name} - {loan.purpose}')

        # =============================================
        # 4. Create EndOfServiceBenefits (2 records)
        # =============================================
        eos_data = [
            {'employee_idx': 6, 'years_of_service': 2.5, 'total_service_days': 912, 'last_salary': 9500, 'total_benefit': 12500, 'deduction_amount': 0, 'status': 'calculated'},
            {'employee_idx': 7, 'years_of_service': 1.8, 'total_service_days': 657, 'last_salary': 12300, 'total_benefit': 15000, 'deduction_amount': 3000, 'status': 'paid'},
        ]

        eos_count = 0
        for data in eos_data:
            idx = data['employee_idx']
            if idx >= len(employees):
                continue
            emp = employees[idx]

            net = Decimal(str(data['total_benefit'])) - Decimal(str(data['deduction_amount']))

            eos, created = EndOfServiceBenefit.objects.get_or_create(
                employee=emp,
                calculation_date=now.date(),
                defaults={
                    'years_of_service': Decimal(str(data['years_of_service'])),
                    'total_service_days': data['total_service_days'],
                    'last_salary': Decimal(str(data['last_salary'])),
                    'total_benefit': Decimal(str(data['total_benefit'])),
                    'deduction_amount': Decimal(str(data['deduction_amount'])),
                    'net_benefit': net,
                    'status': data['status'],
                    'paid_date': now.date() if data['status'] == 'paid' else None,
                },
            )
            if created:
                eos_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created end of service: {eos.employee_name} - {eos.net_benefit} ريال ({eos.get_status_display()})'))
            else:
                self.stdout.write(f'  Skipped (exists): {eos.employee_name}')

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Payroll Periods: 1 (or existed)')
        self.stdout.write(f'  Salary Advances created: {advance_count}')
        self.stdout.write(f'  Employee Loans created: {loan_count}')
        self.stdout.write(f'  End of Service Benefits created: {eos_count}')
        self.stdout.write(self.style.SUCCESS('Done! Payroll data seeded successfully.'))
