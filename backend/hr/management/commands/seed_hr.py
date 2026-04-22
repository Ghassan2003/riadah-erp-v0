"""
Management command to seed sample HR data.
Creates departments and sample employees for development.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from hr.models import Department, Employee


class Command(BaseCommand):
    help = 'Seed sample departments and employees for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample HR data...')

        # Create departments
        departments_data = [
            {'name': 'الإدارة العامة', 'name_en': 'General Management'},
            {'name': 'المبيعات', 'name_en': 'Sales'},
            {'name': 'المحاسبة والمالية', 'name_en': 'Accounting & Finance'},
            {'name': 'المخازن واللوجستيات', 'name_en': 'Warehouse & Logistics'},
            {'name': 'تقنية المعلومات', 'name_en': 'IT'},
            {'name': 'الموارد البشرية', 'name_en': 'Human Resources'},
        ]

        dept_objects = {}
        for data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            dept_objects[data['name']] = dept
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created department: {dept.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {dept.name}')

        # Create sample employees
        employees_data = [
            {'first_name': 'أحمد', 'last_name': 'محمد العتيبي', 'department': 'الإدارة العامة', 'position': 'المدير التنفيذي', 'salary': 25000, 'housing': 3000, 'transport': 1500, 'gender': 'male'},
            {'first_name': 'فاطمة', 'last_name': 'الزهراني', 'department': 'المبيعات', 'position': 'مدير المبيعات', 'salary': 18000, 'housing': 2500, 'transport': 1200, 'gender': 'female'},
            {'first_name': 'خالد', 'last_name': 'القحطاني', 'department': 'المحاسبة والمالية', 'position': 'المدير المالي', 'salary': 20000, 'housing': 3000, 'transport': 1500, 'gender': 'male'},
            {'first_name': 'سارة', 'last_name': 'الدوسري', 'department': 'المحاسبة والمالية', 'position': 'محاسب أول', 'salary': 12000, 'housing': 2000, 'transport': 1000, 'gender': 'female'},
            {'first_name': 'عبدالله', 'last_name': 'الشمري', 'department': 'المخازن واللوجستيات', 'position': 'مدير المخازن', 'salary': 15000, 'housing': 2000, 'transport': 1000, 'gender': 'male'},
            {'first_name': 'نورة', 'last_name': 'العنزي', 'department': 'تقنية المعلومات', 'position': 'مهندس برمجيات', 'salary': 16000, 'housing': 2500, 'transport': 1200, 'gender': 'female'},
            {'first_name': 'محمد', 'last_name': 'الغامدي', 'department': 'المبيعات', 'position': 'مندوب مبيعات', 'salary': 8000, 'housing': 1500, 'transport': 800, 'gender': 'male'},
            {'first_name': 'ريم', 'last_name': 'المالكي', 'department': 'الموارد البشرية', 'position': 'مسؤول موارد بشرية', 'salary': 10000, 'housing': 1500, 'transport': 800, 'gender': 'female'},
        ]

        emp_count = 0
        for data in employees_data:
            dept_name = data.pop('department')
            dept = dept_objects.get(dept_name)
            if not dept:
                continue

            emp, created = Employee.objects.get_or_create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                defaults={
                    'email': f"{data['first_name'].lower()}.{data['last_name'].split()[0].lower()}@erp.com",
                    'phone': f"05{str(emp_count + 1).zfill(8)}",
                    'department': dept,
                    'hire_date': '2023-01-15',
                    'salary': data['salary'],
                    'housing_allowance': data['housing'],
                    'transport_allowance': data['transport'],
                    'gender': data['gender'],
                },
            )
            if created:
                emp_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created employee: {emp.full_name} ({emp.employee_number})'))
            else:
                self.stdout.write(f'  Skipped (exists): {emp.full_name}')

        # Set department managers
        if emp_count > 0:
            try:
                ceo = Employee.objects.filter(first_name='أحمد', last_name='محمد العتيبي').first()
                if ceo:
                    mgmt = dept_objects.get('الإدارة العامة')
                    if mgmt:
                        mgmt.manager = ceo
                        mgmt.save()
                        self.stdout.write('  Set CEO as department manager')
            except Exception:
                pass

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created {emp_count} employees.'))
