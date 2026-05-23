"""
Management command to seed sample Budget Management data.
Creates Budgets, BudgetCategories, BudgetItems, BudgetTransfers, and BudgetExpenses
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from budget.models import (
    Budget,
    BudgetCategory,
    BudgetItem,
    BudgetTransfer,
    BudgetExpense,
)


class Command(BaseCommand):
    help = 'Seed sample budget data for the ERP system'

    def handle(self, *args, **options):
        from hr.models import Department
        from users.models import User

        self.stdout.write('Creating sample Budget data...')

        # Get an admin user for created_by fields
        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. Create 3 Budgets for fiscal year 2025
        # =============================================
        departments = {
            'IT': Department.objects.filter(name__icontains='تقنية').first() or Department.objects.filter(name__icontains='IT').first(),
            'Marketing': Department.objects.filter(name__icontains='تسويق').first() or Department.objects.filter(name__icontains='Marketing').first(),
            'Operations': Department.objects.filter(name__icontains='عمليات').first() or Department.objects.filter(name__icontains='Operations').first(),
        }

        budgets_data = [
            {'name': 'ميزانية قسم تقنية المعلومات 2025', 'key': 'IT', 'total_budget': 500000, 'utilized': 150000},
            {'name': 'ميزانية قسم التسويق 2025', 'key': 'Marketing', 'total_budget': 300000, 'utilized': 120000},
            {'name': 'ميزانية قسم العمليات 2025', 'key': 'Operations', 'total_budget': 800000, 'utilized': 350000},
        ]

        budgets = {}
        for data in budgets_data:
            key = data['key']
            dept = departments.get(key)
            budget, created = Budget.objects.get_or_create(
                name=data['name'],
                fiscal_year=2025,
                defaults={
                    'department': dept,
                    'total_budget': Decimal(str(data['total_budget'])),
                    'utilized_amount': Decimal(str(data['utilized'])),
                    'remaining_amount': Decimal(str(data['total_budget'] - data['utilized'])),
                    'status': 'active',
                    'start_date': timezone.now().date().replace(month=1, day=1),
                    'end_date': timezone.now().date().replace(month=12, day=31),
                    'description': f'ميزانية قسم {key} للسنة المالية 2025',
                    'created_by': admin_user,
                },
            )
            budgets[key] = budget
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created budget: {budget.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {budget.name}')

        # =============================================
        # 2. Create BudgetCategories (2-3 per budget)
        # =============================================
        categories_data = {
            'IT': [
                {'name': 'تطوير البرمجيات', 'allocated': 250000, 'utilized': 80000},
                {'name': 'البنية التحتية', 'allocated': 150000, 'utilized': 50000},
                {'name': 'التدريب والتطوير', 'allocated': 100000, 'utilized': 20000},
            ],
            'Marketing': [
                {'name': 'الحملات الإعلانية', 'allocated': 150000, 'utilized': 70000},
                {'name': 'العلاقات العامة', 'allocated': 100000, 'utilized': 35000},
                {'name': 'البحوث والدراسات', 'allocated': 50000, 'utilized': 15000},
            ],
            'Operations': [
                {'name': 'المصروفات التشغيلية', 'allocated': 400000, 'utilized': 200000},
                {'name': 'الصيانة', 'allocated': 250000, 'utilized': 100000},
            ],
        }

        all_categories = {}
        for budget_key, cats in categories_data.items():
            budget = budgets.get(budget_key)
            if not budget:
                continue
            all_categories[budget_key] = []
            for cat_data in cats:
                category, created = BudgetCategory.objects.get_or_create(
                    budget=budget,
                    name=cat_data['name'],
                    defaults={
                        'allocated_amount': Decimal(str(cat_data['allocated'])),
                        'utilized_amount': Decimal(str(cat_data['utilized'])),
                        'remaining_amount': Decimal(str(cat_data['allocated'] - cat_data['utilized'])),
                        'description': f'{cat_data["name"]} ضمن {budget.name}',
                    },
                )
                all_categories[budget_key].append(category)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created category: {category.name}'))
                else:
                    self.stdout.write(f'  Skipped (exists): {category.name}')

        # =============================================
        # 3. Create BudgetItems (3-5 per category)
        # =============================================
        items_data = {
            'IT': {
                'تطوير البرمجيات': [
                    {'description': 'رواتب فريق التطوير', 'planned': 180000, 'actual': 60000, 'status': 'on_track'},
                    {'description': 'تراخيص البرمجيات', 'planned': 30000, 'actual': 10000, 'status': 'on_track'},
                    {'description': 'خدمات سحابية', 'planned': 25000, 'actual': 7000, 'status': 'under_budget'},
                    {'description': 'أدوات التطوير', 'planned': 15000, 'actual': 3000, 'status': 'under_budget'},
                ],
                'البنية التحتية': [
                    {'description': 'خوادم ومعدات', 'planned': 80000, 'actual': 30000, 'status': 'on_track'},
                    {'description': 'شبكات واتصالات', 'planned': 40000, 'actual': 12000, 'status': 'under_budget'},
                    {'description': 'الأمن السيبراني', 'planned': 30000, 'actual': 8000, 'status': 'under_budget'},
                ],
                'التدريب والتطوير': [
                    {'description': 'دورات تدريبية للموظفين', 'planned': 50000, 'actual': 12000, 'status': 'under_budget'},
                    {'description': 'حضور مؤتمرات', 'planned': 30000, 'actual': 5000, 'status': 'under_budget'},
                    {'description': 'شهادات مهنية', 'planned': 20000, 'actual': 3000, 'status': 'under_budget'},
                ],
            },
            'Marketing': {
                'الحملات الإعلانية': [
                    {'description': 'إعلانات رقمية', 'planned': 60000, 'actual': 35000, 'status': 'on_track'},
                    {'description': 'إعلانات تقليدية', 'planned': 50000, 'actual': 20000, 'status': 'on_track'},
                    {'description': 'تسويق عبر وسائل التواصل', 'planned': 40000, 'actual': 15000, 'status': 'under_budget'},
                ],
                'العلاقات العامة': [
                    {'description': 'فعاليات ورعايات', 'planned': 50000, 'actual': 20000, 'status': 'on_track'},
                    {'description': 'خدمات علاقات عامة', 'planned': 30000, 'actual': 10000, 'status': 'under_budget'},
                    {'description': 'هدايا وتذكارات', 'planned': 20000, 'actual': 5000, 'status': 'under_budget'},
                ],
                'البحوث والدراسات': [
                    {'description': 'أبحاث السوق', 'planned': 30000, 'actual': 10000, 'status': 'under_budget'},
                    {'description': 'استبيانات وتحليلات', 'planned': 20000, 'actual': 5000, 'status': 'under_budget'},
                ],
            },
            'Operations': {
                'المصروفات التشغيلية': [
                    {'description': 'إيجارات المرافق', 'planned': 200000, 'actual': 120000, 'status': 'on_track'},
                    {'description': 'فواتير الكهرباء والماء', 'planned': 80000, 'actual': 45000, 'status': 'on_track'},
                    {'description': 'مصاريف نقل وشحن', 'planned': 70000, 'actual': 20000, 'status': 'under_budget'},
                    {'description': 'مستلزمات مكتبية', 'planned': 30000, 'actual': 8000, 'status': 'under_budget'},
                    {'description': 'خدمات نظافة', 'planned': 20000, 'actual': 7000, 'status': 'under_budget'},
                ],
                'الصيانة': [
                    {'description': 'صيانة مباني', 'planned': 120000, 'actual': 60000, 'status': 'on_track'},
                    {'description': 'صيانة معدات', 'planned': 80000, 'actual': 25000, 'status': 'under_budget'},
                    {'description': 'قطع غيار', 'planned': 50000, 'actual': 15000, 'status': 'under_budget'},
                ],
            },
        }

        item_count = 0
        for budget_key, budget_cats in items_data.items():
            if budget_key not in all_categories:
                continue
            for category in all_categories[budget_key]:
                cat_items = budget_cats.get(category.name, [])
                for item_data in cat_items:
                    item, created = BudgetItem.objects.get_or_create(
                        category=category,
                        description=item_data['description'],
                        defaults={
                            'planned_amount': Decimal(str(item_data['planned'])),
                            'actual_amount': Decimal(str(item_data['actual'])),
                            'status': item_data['status'],
                        },
                    )
                    if created:
                        item_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  Created item: {item.description}'))

        # =============================================
        # 4. Create BudgetTransfers (2 records)
        # =============================================
        it_budget = budgets.get('IT')
        marketing_budget = budgets.get('Marketing')
        operations_budget = budgets.get('Operations')

        transfers_data = [
            {
                'from': it_budget,
                'to': marketing_budget,
                'amount': 20000,
                'reason': 'تحويل مبلغ لدعم حملة تسويقية جديدة',
                'status': 'approved',
            },
            {
                'from': operations_budget,
                'to': it_budget,
                'amount': 15000,
                'reason': 'تحويل مبلغ لترقية البنية التحتية التقنية',
                'status': 'pending',
            },
        ]

        transfer_count = 0
        for t_data in transfers_data:
            if not t_data['from'] or not t_data['to']:
                continue
            transfer, created = BudgetTransfer.objects.get_or_create(
                from_budget=t_data['from'],
                to_budget=t_data['to'],
                amount=Decimal(str(t_data['amount'])),
                defaults={
                    'reason': t_data['reason'],
                    'status': t_data['status'],
                    'approved_by': admin_user if t_data['status'] == 'approved' else None,
                },
            )
            if created:
                transfer_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created transfer: {transfer.from_budget.name} → {transfer.to_budget.name} - {transfer.amount}'))

        # =============================================
        # 5. Create BudgetExpenses (3 records)
        # =============================================
        expense_count = 0
        if it_budget and all_categories.get('IT'):
            cat_it = all_categories['IT'][0]  # تطوير البرمجيات
            expense, created = BudgetExpense.objects.get_or_create(
                budget=it_budget,
                description='شراء خوادم جديدة',
                expense_date=timezone.now().date(),
                defaults={
                    'category': cat_it,
                    'amount': Decimal('45000'),
                    'reference_number': 'EXP-2025-001',
                    'status': 'approved',
                    'approved_by': admin_user,
                },
            )
            if created:
                expense_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created expense: {expense.description}'))

        if marketing_budget and all_categories.get('Marketing'):
            cat_mkt = all_categories['Marketing'][0]  # الحملات الإعلانية
            expense, created = BudgetExpense.objects.get_or_create(
                budget=marketing_budget,
                description='حملة إعلانية رمضانية',
                expense_date=timezone.now().date(),
                defaults={
                    'category': cat_mkt,
                    'amount': Decimal('25000'),
                    'reference_number': 'EXP-2025-002',
                    'status': 'pending',
                },
            )
            if created:
                expense_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created expense: {expense.description}'))

        if operations_budget and all_categories.get('Operations'):
            cat_ops = all_categories['Operations'][0]  # المصروفات التشغيلية
            expense, created = BudgetExpense.objects.get_or_create(
                budget=operations_budget,
                description='صيانة دورية للمكاتب',
                expense_date=timezone.now().date(),
                defaults={
                    'category': cat_ops,
                    'amount': Decimal('12000'),
                    'reference_number': 'EXP-2025-003',
                    'status': 'rejected',
                    'approved_by': admin_user,
                },
            )
            if created:
                expense_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created expense: {expense.description}'))

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Budgets: {len(budgets)} (or existed)')
        total_cats = sum(len(v) for v in all_categories.values())
        self.stdout.write(f'  Budget Categories: {total_cats} (or existed)')
        self.stdout.write(f'  Budget Items created: {item_count}')
        self.stdout.write(f'  Budget Transfers created: {transfer_count}')
        self.stdout.write(f'  Budget Expenses created: {expense_count}')
        self.stdout.write(self.style.SUCCESS('Done! Budget data seeded successfully.'))
