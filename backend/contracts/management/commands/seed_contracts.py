"""Management command to seed sample contracts data."""
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from contracts.models import Contract, ContractMilestone, ContractPayment

class Command(BaseCommand):
    help = 'Seed sample contracts for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample contracts data...')
        try:
            from sales.models import Customer
            from projects.models import Project
            from users.models import User
        except ImportError as e:
            self.stdout.write(f'Skipping - missing dependency: {e}')
            return

        admin = User.objects.filter(username='admin').first()
        if not admin:
            self.stdout.write('No admin user found. Skipping.')
            return

        customers = list(Customer.objects.filter(is_active=True)[:3])
        projects = list(Project.objects.all()[:2])

        contracts_data = [
            {'title': 'عقد تطوير النظام المحاسبي', 'title_en': 'Accounting System Development', 'type': 'service', 'value': 150000, 'duration': 180},
            {'title': 'عقد صيانة الأجهزة', 'title_en': 'Equipment Maintenance Contract', 'type': 'maintenance', 'value': 50000, 'duration': 365},
            {'title': 'عقد توريد المعدات المكتبية', 'title_en': 'Office Equipment Supply', 'type': 'purchase', 'value': 75000, 'duration': 90},
        ]

        count = 0
        for i, data in enumerate(contracts_data):
            ctr_num = f'CTR-{date.today().strftime("%Y%m%d")}-{(i+1):04d}'
            customer = customers[i] if i < len(customers) else None
            project = projects[i] if i < len(projects) else None

            ctr, created = Contract.objects.get_or_create(
                contract_number=ctr_num,
                defaults={
                    'title': data['title'],
                    'title_en': data['title_en'],
                    'contract_type': data['type'],
                    'customer': customer,
                    'project': project,
                    'start_date': date.today() - timedelta(days=30),
                    'end_date': date.today() + timedelta(days=data['duration']),
                    'value': data['value'],
                    'currency': 'SAR',
                    'status': 'active',
                    'signed_date': date.today() - timedelta(days=25),
                    'signed_by': admin,
                    'responsible_person': admin,
                    'created_by': admin,
                    'renewal_reminder_days': 30,
                    'vat_inclusive': True,
                }
            )
            if created:
                count += 1
                # Create milestones
                for m in range(3):
                    ContractMilestone.objects.create(
                        contract=ctr,
                        title=f'المرحلة {m+1}',
                        due_date=date.today() + timedelta(days=(m+1) * data['duration'] // 3),
                        amount=data['value'] / 3,
                        status='completed' if m == 0 else ('in_progress' if m == 1 else 'pending'),
                    )
                # Create payments
                for p in range(2):
                    ContractPayment.objects.create(
                        contract=ctr,
                        amount=data['value'] / 3,
                        due_date=date.today() + timedelta(days=p * 60),
                        payment_status='paid' if p == 0 else 'pending',
                        paid_amount=data['value'] / 3 if p == 0 else 0,
                        paid_date=date.today() if p == 0 else None,
                    )

        self.stdout.write(f'Done! Created {count} contracts with milestones and payments.')
