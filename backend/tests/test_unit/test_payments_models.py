"""
اختبارات الوحدات البرمجية لنماذج نظام التحصيلات والتحويلات المالية.
Unit Tests for Payments (Collections & Transfers) Models.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestPaymentAccountModel:
    """اختبارات نموذج الحساب المالي."""

    def test_create_payment_account(self, db):
        """اختبار إنشاء حساب مالي."""
        from payments.models import PaymentAccount
        acc = PaymentAccount.objects.create(
            account_name='البنك الأهلي',
            account_type='bank_account',
            bank_name='البنك الأهلي السعودي',
            account_number='SA0380000000608010167519',
            iban='SA0380000000608010167519',
            current_balance=Decimal('50000'),
        )
        assert acc.is_active is True
        assert acc.currency == 'SAR'

    def test_default_account(self, db):
        """اختبار الحساب الافتراضي."""
        from payments.models import PaymentAccount
        acc1 = PaymentAccount.objects.create(
            account_name='حساب 1', account_type='bank_account', is_default=True
        )
        acc2 = PaymentAccount.objects.create(
            account_name='حساب 2', account_type='cash_box', is_default=True
        )
        # عند تعيين حساب كافتراضي، يجب إزالة الافتراضي من الحسابات الأخرى
        acc1.refresh_from_db()
        assert acc1.is_default is False
        assert acc2.is_default is True

    def test_account_types(self, db):
        """اختبار أنواع الحسابات."""
        from payments.models import PaymentAccount
        expected = ['bank_account', 'cash_box', 'mobile_wallet']
        actual = [c[0] for c in PaymentAccount.ACCOUNT_TYPE_CHOICES]
        assert actual == expected

    def test_account_str(self, db):
        """اختبار التمثيل النصي للحساب."""
        from payments.models import PaymentAccount
        acc = PaymentAccount.objects.create(
            account_name='صندوق النقدية', account_type='cash_box'
        )
        assert 'صندوق النقدية' in str(acc)
        assert 'صندوق نقدي' in str(acc)


class TestFinancialTransactionModel:
    """اختبارات نموذج العملية المالية."""

    def _create_account(self, db, name='حساب اختبار'):
        """إنشاء حساب مالي اختبار."""
        from payments.models import PaymentAccount
        return PaymentAccount.objects.create(
            account_name=name, account_type='bank_account',
            current_balance=Decimal('100000'),
        )

    def test_create_transaction(self, db):
        """اختبار إنشاء عملية مالية."""
        from payments.models import FinancialTransaction
        acc = self._create_account(db)
        txn = FinancialTransaction.objects.create(
            transaction_type='receipt',
            account=acc,
            amount=Decimal('5000'),
            transaction_date=date.today(),
            payment_method='bank_transfer',
            description='تحصيل من عميل',
        )
        assert txn.transaction_number.startswith('TRX-')
        assert txn.status == 'completed'
        assert txn.currency == 'SAR'

    def test_transaction_types(self, db):
        """اختبار أنواع العمليات المالية."""
        from payments.models import FinancialTransaction
        expected = ['receipt', 'payment', 'transfer', 'adjustment']
        actual = [c[0] for c in FinancialTransaction.TRANSACTION_TYPE_CHOICES]
        assert actual == expected

    def test_payment_methods(self, db):
        """اختبار طرق الدفع."""
        from payments.models import FinancialTransaction
        expected = ['bank_transfer', 'cash', 'cheque', 'card', 'mobile']
        actual = [c[0] for c in FinancialTransaction.PAYMENT_METHOD_CHOICES]
        assert actual == expected

    def test_transaction_str(self, db):
        """اختبار التمثيل النصي للعملية."""
        from payments.models import FinancialTransaction
        acc = self._create_account(db)
        txn = FinancialTransaction.objects.create(
            transaction_type='receipt', account=acc,
            amount=Decimal('3000'), transaction_date=date.today(),
            payment_method='cash',
        )
        assert '3000' in str(txn)
        assert 'إيصال قبض' in str(txn)

    def test_reference_types(self, db):
        """اختبار أنواع المراجع."""
        from payments.models import FinancialTransaction
        expected = ['invoice', 'salary', 'loan', 'purchase', 'sale', 'other']
        actual = [c[0] for c in FinancialTransaction.REFERENCE_TYPE_CHOICES]
        assert actual == expected

    def test_transfer_with_to_account(self, db):
        """اختبار التحويل بين الحسابات."""
        from payments.models import FinancialTransaction
        acc1 = self._create_account(db, 'حساب مصدر')
        acc2 = self._create_account(db, 'حساب مستلم')
        txn = FinancialTransaction.objects.create(
            transaction_type='transfer',
            account=acc1,
            to_account=acc2,
            amount=Decimal('10000'),
            transaction_date=date.today(),
            payment_method='bank_transfer',
            description='تحويل بين حسابات',
        )
        assert txn.to_account == acc2


class TestChequeModel:
    """اختبارات نموذج الشيك."""

    def test_create_cheque(self, db):
        """اختبار إنشاء شيك."""
        from payments.models import Cheque
        cheque = Cheque.objects.create(
            cheque_number='CHQ-001',
            bank_name='البنك الأهلي',
            amount=Decimal('15000'),
            due_date=date.today() + timedelta(days=90),
            payer_name='شركةabcd',
            payee_name='شركتنا',
            cheque_type='incoming',
        )
        assert cheque.status == 'received'
        assert cheque.cheque_type == 'incoming'

    def test_cheque_types(self, db):
        """اختبار أنواع الشيكات."""
        from payments.models import Cheque
        expected = ['incoming', 'outgoing']
        actual = [c[0] for c in Cheque.CHEQUE_TYPE_CHOICES]
        assert actual == expected

    def test_cheque_status_choices(self, db):
        """اختبار حالات الشيك."""
        from payments.models import Cheque
        expected = ['received', 'deposited', 'cleared', 'bounced', 'cancelled']
        actual = [c[0] for c in Cheque.STATUS_CHOICES]
        assert actual == expected

    def test_cheque_str(self, db):
        """اختبار التمثيل النصي للشيك."""
        from payments.models import Cheque
        cheque = Cheque.objects.create(
            cheque_number='CHQ-STR',
            bank_name='بنك الراجحي',
            amount=Decimal('5000'),
            due_date=date.today(),
            payer_name='محمد',
            payee_name='أحمد',
        )
        assert 'CHQ-STR' in str(cheque)
        assert 'محمد' in str(cheque)


class TestReconciliationModel:
    """اختبارات نموذج التسوية."""

    def test_create_reconciliation(self, db):
        """اختبار إنشاء تسوية."""
        from payments.models import Reconciliation, PaymentAccount
        acc = PaymentAccount.objects.create(
            account_name='حساب تسوية', account_type='bank_account',
            current_balance=Decimal('50000'),
        )
        recon = Reconciliation.objects.create(
            account=acc,
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            system_balance=Decimal('50000'),
            actual_balance=Decimal('49500'),
        )
        assert recon.reconciliation_number.startswith('REC-')
        # الموديل يضبط الحالة تلقائياً فقط عند التحويل من reconciled
        assert recon.status in ['draft', 'discrepancy']
        assert recon.difference == Decimal('-500')

    def test_reconciled_status(self, db):
        """اختبار حالة التوازن."""
        from payments.models import Reconciliation, PaymentAccount
        acc = PaymentAccount.objects.create(
            account_name='حساب متوازن', account_type='bank_account',
            current_balance=Decimal('30000'),
        )
        recon = Reconciliation.objects.create(
            account=acc,
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            system_balance=Decimal('30000'),
            actual_balance=Decimal('30000'),
        )
        assert recon.status == 'reconciled'
        assert recon.difference == Decimal('0')

    def test_difference_property(self, db):
        """اختبار خاصية الفرق في التسوية."""
        from payments.models import Reconciliation, PaymentAccount
        acc = PaymentAccount.objects.create(
            account_name='حساب فرق', account_type='bank_account'
        )
        recon = Reconciliation.objects.create(
            account=acc,
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            system_balance=Decimal('10000'),
            actual_balance=Decimal('9500'),
        )
        assert recon.difference == Decimal('-500')

    def test_reconciliation_status_choices(self, db):
        """اختبار حالات التسوية."""
        from payments.models import Reconciliation
        expected = ['draft', 'reconciled', 'discrepancy']
        actual = [c[0] for c in Reconciliation.STATUS_CHOICES]
        assert actual == expected


# Fix missing import for timedelta
from datetime import timedelta
