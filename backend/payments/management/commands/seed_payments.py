"""
Management command to seed sample payments data.
Creates payment accounts, financial transactions, cheques, and reconciliations for development.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from payments.models import PaymentAccount, FinancialTransaction, Cheque, Reconciliation


class Command(BaseCommand):
    help = 'Seed sample payment accounts, transactions, cheques, and reconciliations for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample payments data...')

        # =============================================
        # Create Payment Accounts
        # =============================================
        self.stdout.write('\n--- Payment Accounts ---')
        accounts_data = [
            {
                'account_name': 'الحساب الجاري - البنك الأهلي',
                'account_type': 'bank_account',
                'bank_name': 'البنك الأهلي السعودي',
                'account_number': 'SA0380000000608010167519',
                'iban': 'SA0380000000608010167519',
                'currency': 'SAR',
                'is_default': True,
                'current_balance': Decimal('150000.00'),
            },
            {
                'account_name': 'الصندوق النقدي الرئيسي',
                'account_type': 'cash_box',
                'currency': 'SAR',
                'current_balance': Decimal('25000.00'),
            },
            {
                'account_name': 'محفظة مدى - STC Pay',
                'account_type': 'mobile_wallet',
                'currency': 'SAR',
                'current_balance': Decimal('8000.00'),
            },
        ]

        account_objects = []
        for data in accounts_data:
            account, created = PaymentAccount.objects.get_or_create(
                account_name=data['account_name'],
                defaults=data,
            )
            if created:
                account_objects.append(account)
                self.stdout.write(self.style.SUCCESS(f'  Created account: {account.account_name}'))
            else:
                account_objects.append(account)
                self.stdout.write(f'  Skipped (exists): {account.account_name}')

        # =============================================
        # Create Financial Transactions
        # =============================================
        self.stdout.write('\n--- Financial Transactions ---')

        today = date.today()
        transactions_data = [
            {
                'transaction_type': 'receipt',
                'account': account_objects[0],
                'amount': Decimal('150000.00'),
                'reference_type': 'sale',
                'description': 'إيراد مبيعات شهر يناير',
                'transaction_date': today - timedelta(days=30),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'receipt',
                'account': account_objects[0],
                'amount': Decimal('45000.00'),
                'reference_type': 'invoice',
                'description': 'تحصيل فاتورة عميل شركة الخليج للتجارة',
                'transaction_date': today - timedelta(days=25),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'payment',
                'account': account_objects[0],
                'amount': Decimal('32000.00'),
                'reference_type': 'purchase',
                'description': 'دفع ثمن بضاعة مورد الشرق الأوسط',
                'transaction_date': today - timedelta(days=22),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'receipt',
                'account': account_objects[1],
                'amount': Decimal('25000.00'),
                'reference_type': 'sale',
                'description': 'مبيعات نقدية يومية',
                'transaction_date': today - timedelta(days=20),
                'payment_method': 'cash',
                'status': 'completed',
            },
            {
                'transaction_type': 'payment',
                'account': account_objects[1],
                'amount': Decimal('5000.00'),
                'reference_type': 'other',
                'description': 'مصروفات تشغيلية متنوعة',
                'transaction_date': today - timedelta(days=18),
                'payment_method': 'cash',
                'status': 'completed',
            },
            {
                'transaction_type': 'payment',
                'account': account_objects[0],
                'amount': Decimal('78000.00'),
                'reference_type': 'salary',
                'description': 'رواتب الموظفين شهر يناير',
                'transaction_date': today - timedelta(days=15),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'transfer',
                'account': account_objects[0],
                'to_account': account_objects[2],
                'amount': Decimal('8000.00'),
                'description': 'تحويل لمحفظة مدى',
                'transaction_date': today - timedelta(days=10),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'receipt',
                'account': account_objects[0],
                'amount': Decimal('28000.00'),
                'reference_type': 'invoice',
                'description': 'تحصيل فاتورة عميل شركة النور',
                'transaction_date': today - timedelta(days=5),
                'payment_method': 'bank_transfer',
                'status': 'completed',
            },
            {
                'transaction_type': 'payment',
                'account': account_objects[0],
                'amount': Decimal('12000.00'),
                'reference_type': 'purchase',
                'description': 'دفعة مقدمة مورد معدات المكتب',
                'transaction_date': today - timedelta(days=3),
                'payment_method': 'cheque',
                'cheque_number': 'CHK-2024-001',
                'status': 'pending',
            },
            {
                'transaction_type': 'receipt',
                'account': account_objects[2],
                'amount': Decimal('3500.00'),
                'reference_type': 'other',
                'description': 'إيراد خدمات استشارية',
                'transaction_date': today - timedelta(days=1),
                'payment_method': 'mobile',
                'status': 'completed',
            },
        ]

        trx_count = 0
        for data in transactions_data:
            trx, created = FinancialTransaction.objects.get_or_create(
                transaction_number=FinancialTransaction(
                    transaction_date=data['transaction_date']
                ).generate_transaction_number(),
                defaults=data,
            )
            if created:
                trx_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Created transaction: {trx.transaction_number} - '
                    f'{trx.get_transaction_type_display()} - {trx.amount}'
                ))
            else:
                self.stdout.write(f'  Skipped (exists): {trx.transaction_number}')

        # =============================================
        # Create Cheques
        # =============================================
        self.stdout.write('\n--- Cheques ---')
        cheques_data = [
            {
                'cheque_number': 'CHK-2024-001',
                'bank_name': 'البنك الأهلي السعودي',
                'branch_name': 'فرع الرياض الرئيسي',
                'amount': Decimal('12000.00'),
                'due_date': today + timedelta(days=30),
                'payer_name': 'شركة الخليج للتجارة',
                'payee_name': 'مورد معدات المكتب',
                'cheque_type': 'outgoing',
                'status': 'received',
                'notes': 'دفعة مقدمة شراء معدات',
            },
            {
                'cheque_number': 'CHK-2024-002',
                'bank_name': 'بنك الراجحي',
                'branch_name': 'فرع جدة',
                'amount': Decimal('22000.00'),
                'due_date': today + timedelta(days=15),
                'payer_name': 'شركة النور للتجارة',
                'payee_name': 'الشركة',
                'cheque_type': 'incoming',
                'status': 'deposited',
                'notes': 'سداد فاتورة مبيعات',
            },
            {
                'cheque_number': 'CHK-2024-003',
                'bank_name': 'بنك الرياض',
                'branch_name': 'فرع الدمام',
                'amount': Decimal('8500.00'),
                'due_date': today - timedelta(days=5),
                'payer_name': 'شركة البناء الحديث',
                'payee_name': 'الشركة',
                'cheque_type': 'incoming',
                'status': 'cleared',
                'notes': 'سداد عقد صيانة',
            },
        ]

        cheque_count = 0
        for data in cheques_data:
            cheque, created = Cheque.objects.get_or_create(
                cheque_number=data['cheque_number'],
                defaults=data,
            )
            if created:
                cheque_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Created cheque: {cheque.cheque_number} - {cheque.payer_name} - {cheque.amount}'
                ))
            else:
                self.stdout.write(f'  Skipped (exists): {cheque.cheque_number}')

        # =============================================
        # Create Reconciliation
        # =============================================
        self.stdout.write('\n--- Reconciliations ---')
        rec_data = {
            'account': account_objects[0],
            'period_start': today - timedelta(days=30),
            'period_end': today,
            'system_balance': Decimal('96000.00'),
            'actual_balance': Decimal('96000.00'),
            'notes': 'تسوية شهرية لحساب البنك الأهلي',
        }
        rec, created = Reconciliation.objects.get_or_create(
            account=rec_data['account'],
            period_start=rec_data['period_start'],
            period_end=rec_data['period_end'],
            defaults=rec_data,
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'  Created reconciliation: {rec.reconciliation_number} - {rec.account.account_name}'
            ))
        else:
            self.stdout.write(f'  Skipped (exists): {rec.reconciliation_number}')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {len(account_objects)} accounts, '
            f'{trx_count} transactions, {cheque_count} cheques, and 1 reconciliation.'
        ))
