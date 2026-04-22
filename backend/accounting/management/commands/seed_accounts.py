"""
Management command to seed default chart of accounts.
Creates a standard chart of accounts structure for the ERP system.
"""

from django.core.management.base import BaseCommand
from accounting.models import Account, AccountType


class Command(BaseCommand):
    help = 'Seed default chart of accounts for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating default chart of accounts...')

        accounts_data = [
            # Assets (1xxx)
            {'code': '1000', 'name': 'الأصول', 'name_en': 'Assets', 'account_type': AccountType.ASSET, 'parent': None, 'description': 'إجمالي الأصول'},
            {'code': '1001', 'name': 'النقدية والبنوك', 'name_en': 'Cash & Banks', 'account_type': AccountType.ASSET, 'parent': '1000', 'description': 'حساب النقدية والبنوك'},
            {'code': '1100', 'name': 'المدينون (العملاء)', 'name_en': 'Accounts Receivable', 'account_type': AccountType.ASSET, 'parent': '1000', 'description': 'مبالغ مستحقة من العملاء'},
            {'code': '1200', 'name': 'المخزون', 'name_en': 'Inventory', 'account_type': AccountType.ASSET, 'parent': '1000', 'description': 'تكلفة المخزون المتاح'},
            {'code': '1300', 'name': 'المصروفات المدفوعة مقدماً', 'name_en': 'Prepaid Expenses', 'account_type': AccountType.ASSET, 'parent': '1000', 'description': 'مصروفات مدفوعة مقدماً'},
            {'code': '1500', 'name': 'الأصول الثابتة', 'name_en': 'Fixed Assets', 'account_type': AccountType.ASSET, 'parent': '1000', 'description': 'الأصول الثابتة والمعدات'},
            {'code': '1510', 'name': 'المعدات والأجهزة', 'name_en': 'Equipment & Devices', 'account_type': AccountType.ASSET, 'parent': '1500', 'description': 'المعدات والأجهزة'},
            {'code': '1520', 'name': 'المركبات', 'name_en': 'Vehicles', 'account_type': AccountType.ASSET, 'parent': '1500', 'description': 'مركبات الشركة'},

            # Liabilities (2xxx)
            {'code': '2000', 'name': 'الخصوم', 'name_en': 'Liabilities', 'account_type': AccountType.LIABILITY, 'parent': None, 'description': 'إجمالي الخصوم'},
            {'code': '2100', 'name': 'الدائنون (الموردون)', 'name_en': 'Accounts Payable', 'account_type': AccountType.LIABILITY, 'parent': '2000', 'description': 'مبالغ مستحقة للموردين'},
            {'code': '2200', 'name': 'مصروفات مستحقة', 'name_en': 'Accrued Expenses', 'account_type': AccountType.LIABILITY, 'parent': '2000', 'description': 'مصروفات مستحقة الدفع'},
            {'code': '2300', 'name': 'إيرادات مقدمة', 'name_en': 'Deferred Revenue', 'account_type': AccountType.LIABILITY, 'parent': '2000', 'description': 'إيرادات تم استلامها مقدماً'},
            {'code': '2500', 'name': 'قروض قصيرة الأجل', 'name_en': 'Short-term Loans', 'account_type': AccountType.LIABILITY, 'parent': '2000', 'description': 'قروض مستحقة خلال سنة'},
            {'code': '2600', 'name': 'ضريبة القيمة المضافة', 'name_en': 'VAT Payable', 'account_type': AccountType.LIABILITY, 'parent': '2000', 'description': 'ضريبة القيمة المضافة المستحقة'},

            # Equity (3xxx)
            {'code': '3000', 'name': 'حقوق الملكية', 'name_en': 'Equity', 'account_type': AccountType.EQUITY, 'parent': None, 'description': 'إجمالي حقوق الملكية'},
            {'code': '3100', 'name': 'رأس المال', 'name_en': 'Capital', 'account_type': AccountType.EQUITY, 'parent': '3000', 'description': 'رأس مال الشركة'},
            {'code': '3200', 'name': 'الأرباح المحتجزة', 'name_en': 'Retained Earnings', 'account_type': AccountType.EQUITY, 'parent': '3000', 'description': 'الأرباح المحتجزة'},

            # Income (4xxx)
            {'code': '4000', 'name': 'الإيرادات', 'name_en': 'Revenue', 'account_type': AccountType.INCOME, 'parent': None, 'description': 'إجمالي الإيرادات'},
            {'code': '4100', 'name': 'إيرادات المبيعات', 'name_en': 'Sales Revenue', 'account_type': AccountType.INCOME, 'parent': '4000', 'description': 'إيرادات المبيعات الرئيسية'},
            {'code': '4200', 'name': 'إيرادات أخرى', 'name_en': 'Other Revenue', 'account_type': AccountType.INCOME, 'parent': '4000', 'description': 'إيرادات ثانوية وأخرى'},

            # Expenses (5xxx)
            {'code': '5000', 'name': 'المصروفات', 'name_en': 'Expenses', 'account_type': AccountType.EXPENSE, 'parent': None, 'description': 'إجمالي المصروفات'},
            {'code': '5100', 'name': 'تكلفة البضاعة المباعة', 'name_en': 'Cost of Goods Sold', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'تكلفة البضاعة المباعة'},
            {'code': '5200', 'name': 'مصروفات الرواتب', 'name_en': 'Salaries Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'رواتب الموظفين'},
            {'code': '5300', 'name': 'مصروفات الإيجار', 'name_en': 'Rent Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'إيجارات المباني والمعدات'},
            {'code': '5400', 'name': 'مصروفات المرافق', 'name_en': 'Utilities Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'كهرباء وماء واتصالات'},
            {'code': '5500', 'name': 'مصروفات النقل', 'name_en': 'Transportation Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'مصروفات الشحن والنقل'},
            {'code': '5600', 'name': 'مصروفات عامة وإدارية', 'name_en': 'General & Administrative', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'مصروفات إدارية متنوعة'},
            {'code': '5700', 'name': 'مصروفات التسويق', 'name_en': 'Marketing Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'إعلانات وتسويق'},
            {'code': '5800', 'name': 'مصروفات الاستهلاك', 'name_en': 'Depreciation Expense', 'account_type': AccountType.EXPENSE, 'parent': '5000', 'description': 'استهلاك الأصول الثابتة'},
        ]

        # Track parent references
        account_cache = {}
        created_count = 0
        skipped_count = 0

        for data in accounts_data:
            parent_code = data.pop('parent')
            if parent_code:
                data['parent'] = account_cache.get(parent_code)

            account, created = Account.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            account_cache[data['code']] = account

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {account.code} - {account.name}'))
            else:
                skipped_count += 1
                self.stdout.write(f'  Skipped (exists): {account.code} - {account.name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {created_count} accounts, skipped {skipped_count} existing.'
        ))
