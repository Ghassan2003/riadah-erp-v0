"""
اختبارات الوحدات البرمجية لنماذج المستودعات والمدفوعات.
Unit Tests for Warehouse and Payments Models.
"""

import pytest
from decimal import Decimal
from datetime import date


# =============================================
# اختبارات نموذج المستودع (Warehouse)
# =============================================


class TestWarehouseModel:
    """اختبارات نموذج المستودع."""

    def test_create_warehouse(self, db):
        """اختبار إنشاء مستودع جديد."""
        from warehouse.models import Warehouse
        warehouse = Warehouse.objects.create(
            name='المستودع الرئيسي',
            address='الرياض، حي الصناعة',
            city='الرياض',
            capacity=Decimal('10000.00'),
        )
        assert warehouse.name == 'المستودع الرئيسي'
        assert warehouse.city == 'الرياض'
        assert warehouse.is_active is True
        assert warehouse.capacity == Decimal('10000.00')

    def test_warehouse_code_auto_generated(self, db):
        """اختبار التوليد التلقائي لرمز المستودع."""
        from warehouse.models import Warehouse
        wh1 = Warehouse.objects.create(name='المستودع الأول')
        wh2 = Warehouse.objects.create(name='المستودع الثاني')
        assert wh1.code.startswith('WH-')
        assert wh2.code.startswith('WH-')
        assert wh1.code != wh2.code

    def test_warehouse_str(self, db):
        """اختبار التمثيل النصي للمستودع."""
        from warehouse.models import Warehouse
        warehouse = Warehouse.objects.create(name='مستودع جدة')
        assert warehouse.code in str(warehouse)
        assert 'مستودع جدة' in str(warehouse)

    def test_warehouse_default_values(self, db):
        """اختبار القيم الافتراضية للمستودع."""
        from warehouse.models import Warehouse
        warehouse = Warehouse.objects.create(name='مستودع افتراضي')
        assert warehouse.address == ''
        assert warehouse.city == ''
        assert warehouse.capacity == Decimal('0')
        assert warehouse.is_active is True

    def test_warehouse_ordering(self, db):
        """اختبار ترتيب المستودعات حسب الاسم."""
        from warehouse.models import Warehouse
        Warehouse.objects.create(name='مستودع ب')
        Warehouse.objects.create(name='مستودع أ')
        warehouses = list(Warehouse.objects.all())
        assert warehouses[0].name == 'مستودع أ'
        assert warehouses[1].name == 'مستودع ب'

    def test_warehouse_unique_code(self, db):
        """اختبار تفرد رمز المستودع."""
        from warehouse.models import Warehouse
        wh1 = Warehouse.objects.create(name='مستودع 1')
        wh1.code = 'WH-001'
        wh1.save()
        # إنشاء مستودع آخر بنفس الرمز يجب أن يفشل
        wh2 = Warehouse(name='مستودع 2', code='WH-001')
        with pytest.raises(Exception):
            wh2.save()


class TestWarehouseStockModel:
    """اختبارات نموذج رصيد المخزون."""

    @pytest.mark.skip(reason="inventory/warehouse module removed - WarehouseStock requires inventory.Product")
    def test_create_warehouse_stock(self, db, product):
        """اختبار إنشاء رصيد مخزون."""
        from warehouse.models import Warehouse, WarehouseStock
        warehouse = Warehouse.objects.create(name='المستودع')
        stock = WarehouseStock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity=Decimal('500.00'),
            reserved_quantity=Decimal('50.00'),
            min_stock_level=Decimal('100.00'),
        )
        assert stock.quantity == Decimal('500.00')
        assert stock.reserved_quantity == Decimal('50.00')

    @pytest.mark.skip(reason="inventory/warehouse module removed")
    def test_warehouse_stock_available_quantity(self, db, product):
        """اختبار حساب الكمية المتاحة."""
        from warehouse.models import Warehouse, WarehouseStock
        warehouse = Warehouse.objects.create(name='المستودع')
        stock = WarehouseStock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity=Decimal('200.00'),
            reserved_quantity=Decimal('50.00'),
        )
        assert stock.available_quantity == Decimal('150.00')

    @pytest.mark.skip(reason="inventory/warehouse module removed")
    def test_warehouse_stock_str(self, db, product):
        """اختبار التمثيل النصي لرصيد المخزون."""
        from warehouse.models import Warehouse, WarehouseStock
        warehouse = Warehouse.objects.create(name='المستودع')
        stock = WarehouseStock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity=Decimal('100.00'),
        )
        assert product.name in str(stock)
        assert '100' in str(stock)

    @pytest.mark.skip(reason="inventory/warehouse module removed")
    def test_warehouse_stock_unique_together(self, db, product):
        """اختبار عدم تكرار المنتج في نفس المستودع."""
        from warehouse.models import Warehouse, WarehouseStock
        warehouse = Warehouse.objects.create(name='المستودع')
        WarehouseStock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity=Decimal('10.00'),
        )
        with pytest.raises(Exception):
            WarehouseStock.objects.create(
                warehouse=warehouse,
                product=product,
                quantity=Decimal('20.00'),
            )


class TestStockTransferModel:
    """اختبارات نموذج تحويل المخزون."""

    def test_create_stock_transfer(self, db):
        """اختبار إنشاء تحويل مخزون."""
        from warehouse.models import Warehouse, StockTransfer
        wh_from = Warehouse.objects.create(name='المستودع المصدر')
        wh_to = Warehouse.objects.create(name='المستودع المستهدف')
        transfer = StockTransfer.objects.create(
            from_warehouse=wh_from,
            to_warehouse=wh_to,
        )
        assert transfer.status == 'draft'
        assert transfer.transfer_number.startswith('TRF-')

    def test_stock_transfer_number_auto_generated(self, db):
        """اختبار التوليد التلقائي لرقم التحويل."""
        from warehouse.models import Warehouse, StockTransfer
        wh_from = Warehouse.objects.create(name='من')
        wh_to = Warehouse.objects.create(name='إلى')
        tr1 = StockTransfer.objects.create(from_warehouse=wh_from, to_warehouse=wh_to)
        tr2 = StockTransfer.objects.create(from_warehouse=wh_from, to_warehouse=wh_to)
        assert tr1.transfer_number.startswith('TRF-')
        assert tr1.transfer_number != tr2.transfer_number

    def test_stock_transfer_str(self, db):
        """اختبار التمثيل النصي لتحويل المخزون."""
        from warehouse.models import Warehouse, StockTransfer
        wh_from = Warehouse.objects.create(name='مصدر')
        wh_to = Warehouse.objects.create(name='هدف')
        transfer = StockTransfer.objects.create(from_warehouse=wh_from, to_warehouse=wh_to)
        assert '→' in str(transfer)

    def test_stock_transfer_status_choices(self, db):
        """اختبار خيارات حالة التحويل."""
        from warehouse.models import StockTransfer
        valid_statuses = ['draft', 'pending', 'in_transit', 'completed', 'cancelled']
        for st in valid_statuses:
            assert st in dict(StockTransfer.STATUS_CHOICES)


class TestStockAdjustmentModel:
    """اختبارات نموذج تسوية المخزون."""

    def test_create_stock_adjustment(self, db, product, admin_user):
        """اختبار إنشاء تسوية مخزون."""
        from warehouse.models import Warehouse, StockAdjustment
        warehouse = Warehouse.objects.create(name='المستودع')
        adj = StockAdjustment.objects.create(
            warehouse=warehouse,
            reason='damage',
            product=product,
            previous_quantity=Decimal('100.00'),
            new_quantity=Decimal('90.00'),
            created_by=admin_user,
        )
        assert adj.reason == 'damage'
        assert adj.adjustment_number.startswith('ADJ-')
        assert adj.difference == Decimal('-10.00')

    def test_stock_adjustment_difference(self, db, product):
        """اختبار حساب فرق التسوية."""
        from warehouse.models import Warehouse, StockAdjustment
        warehouse = Warehouse.objects.create(name='المستودع')
        # اختبار زيادة المخزون
        adj_up = StockAdjustment.objects.create(
            warehouse=warehouse,
            reason='received',
            product=product,
            previous_quantity=Decimal('50.00'),
            new_quantity=Decimal('80.00'),
        )
        assert adj_up.difference == Decimal('30.00')
        # اختبار نقص المخزون
        adj_down = StockAdjustment.objects.create(
            warehouse=warehouse,
            reason='correction',
            product=product,
            previous_quantity=Decimal('80.00'),
            new_quantity=Decimal('60.00'),
        )
        assert adj_down.difference == Decimal('-20.00')

    def test_stock_adjustment_str(self, db, product):
        """اختبار التمثيل النصي لتسوية المخزون."""
        from warehouse.models import Warehouse, StockAdjustment
        warehouse = Warehouse.objects.create(name='المستودع')
        adj = StockAdjustment.objects.create(
            warehouse=warehouse,
            reason='count',
            product=product,
            previous_quantity=Decimal('100.00'),
            new_quantity=Decimal('95.00'),
        )
        assert product.name in str(adj)
        assert adj.reason in str(adj)


class TestStockCountModel:
    """اختبارات نموذج جرد المخزون."""

    def test_create_stock_count(self, db, admin_user):
        """اختبار إنشاء جرد مخزون."""
        from warehouse.models import Warehouse, StockCount
        warehouse = Warehouse.objects.create(name='المستودع')
        count = StockCount.objects.create(
            warehouse=warehouse,
            counted_by=admin_user,
        )
        assert count.status == 'draft'
        assert count.count_number.startswith('CNT-')

    def test_stock_count_str(self, db):
        """اختبار التمثيل النصي لجرد المخزون."""
        from warehouse.models import Warehouse, StockCount
        warehouse = Warehouse.objects.create(name='مستودع الاختبار')
        count = StockCount.objects.create(warehouse=warehouse)
        text = str(count)
        assert 'مستودع الاختبار' in text
        assert 'مسودة' in text


# =============================================
# اختبارات نموذج المدفوعات (Payments)
# =============================================


class TestPaymentAccountModel:
    """اختبارات نموذج الحساب المالي."""

    def test_create_payment_account(self, db):
        """اختبار إنشاء حساب مالي."""
        from payments.models import PaymentAccount
        account = PaymentAccount.objects.create(
            account_name='الحساب الجاري',
            account_type='bank_account',
            bank_name='البنك الأهلي',
            account_number='SA0380000000608010167519',
            iban='SA0380000000608010167519',
            current_balance=Decimal('50000.00'),
        )
        assert account.account_name == 'الحساب الجاري'
        assert account.account_type == 'bank_account'
        assert account.currency == 'SAR'
        assert account.is_active is True
        assert account.is_default is False

    def test_payment_account_str(self, db):
        """اختبار التمثيل النصي للحساب المالي."""
        from payments.models import PaymentAccount
        account = PaymentAccount.objects.create(
            account_name='الصندوق النقدي',
            account_type='cash_box',
        )
        text = str(account)
        assert 'الصندوق النقدي' in text
        assert 'صندوق نقدي' in text

    def test_payment_account_default_values(self, db):
        """اختبار القيم الافتراضية للحساب المالي."""
        from payments.models import PaymentAccount
        account = PaymentAccount.objects.create(
            account_name='حساب افتراضي',
            account_type='mobile_wallet',
        )
        assert account.bank_name == ''
        assert account.account_number == ''
        assert account.iban == ''
        assert account.currency == 'SAR'
        assert account.current_balance == Decimal('0')
        assert account.is_default is False
        assert account.is_active is True

    def test_payment_account_type_choices(self, db):
        """اختبار أنواع الحسابات المتاحة."""
        from payments.models import PaymentAccount
        types = ['bank_account', 'cash_box', 'mobile_wallet']
        for atype in types:
            account = PaymentAccount.objects.create(
                account_name=f'حساب {atype}',
                account_type=atype,
            )
            assert account.account_type == atype

    def test_payment_account_is_default_unique(self, db):
        """اختبار أن حساباً واحداً فقط يمكن أن يكون الافتراضي."""
        from payments.models import PaymentAccount
        acc1 = PaymentAccount.objects.create(
            account_name='حساب أول',
            account_type='bank_account',
            is_default=True,
        )
        acc2 = PaymentAccount.objects.create(
            account_name='حساب ثاني',
            account_type='bank_account',
            is_default=True,
        )
        acc1.refresh_from_db()
        # الحساب الأول لم يعد الافتراضي
        assert acc1.is_default is False
        assert acc2.is_default is True


class TestFinancialTransactionModel:
    """اختبارات نموذج العملية المالية."""

    def test_create_financial_transaction(self, db):
        """اختبار إنشاء عملية مالية."""
        from payments.models import PaymentAccount, FinancialTransaction
        account = PaymentAccount.objects.create(
            account_name='حساب اختبار',
            account_type='bank_account',
        )
        transaction = FinancialTransaction.objects.create(
            transaction_type='receipt',
            account=account,
            amount=Decimal('10000.00'),
            transaction_date=date(2024, 6, 1),
            payment_method='bank_transfer',
            status='completed',
        )
        assert transaction.transaction_type == 'receipt'
        assert transaction.amount == Decimal('10000.00')
        assert transaction.transaction_number.startswith('TRX-')
        assert transaction.currency == 'SAR'

    def test_financial_transaction_str(self, db):
        """اختبار التمثيل النصي للعملية المالية."""
        from payments.models import PaymentAccount, FinancialTransaction
        account = PaymentAccount.objects.create(
            account_name='الحساب',
            account_type='cash_box',
        )
        transaction = FinancialTransaction.objects.create(
            transaction_type='payment',
            account=account,
            amount=Decimal('5000.00'),
            transaction_date=date(2024, 6, 15),
            payment_method='cash',
        )
        text = str(transaction)
        assert transaction.transaction_number in text
        assert 'دفع' in text
        assert '5000' in text

    def test_financial_transaction_default_values(self, db):
        """اختبار القيم الافتراضية للعملية المالية."""
        from payments.models import PaymentAccount, FinancialTransaction
        account = PaymentAccount.objects.create(
            account_name='حساب',
            account_type='bank_account',
        )
        transaction = FinancialTransaction.objects.create(
            transaction_type='transfer',
            account=account,
            amount=Decimal('2000.00'),
            transaction_date=date(2024, 1, 1),
            payment_method='card',
        )
        assert transaction.currency == 'SAR'
        assert transaction.status == 'completed'
        assert transaction.cheque_number == ''

    def test_financial_transaction_type_choices(self, db):
        """اختبار أنواع العمليات المالية المتاحة."""
        from payments.models import FinancialTransaction
        types = ['receipt', 'payment', 'transfer', 'adjustment']
        for ttype in types:
            assert ttype in dict(FinancialTransaction.TRANSACTION_TYPE_CHOICES)


class TestChequeModel:
    """اختبارات نموذج الشيك."""

    def test_create_cheque(self, db):
        """اختبار إنشاء شيك."""
        from payments.models import Cheque
        cheque = Cheque.objects.create(
            cheque_number='CHK-2024-001',
            bank_name='البنك السعودي الفرنسي',
            amount=Decimal('25000.00'),
            due_date=date(2024, 7, 15),
            payer_name='شركة المورد',
            payee_name='شركتنا',
            cheque_type='incoming',
        )
        assert cheque.cheque_number == 'CHK-2024-001'
        assert cheque.amount == Decimal('25000.00')
        assert cheque.status == 'received'

    def test_cheque_str(self, db):
        """اختبار التمثيل النصي للشيك."""
        from payments.models import Cheque
        cheque = Cheque.objects.create(
            cheque_number='CHK-001',
            bank_name='بنك الراجحي',
            amount=Decimal('15000.00'),
            due_date=date(2024, 8, 1),
            payer_name='الشركة المرسلة',
            payee_name='الشركة المستلمة',
            cheque_type='outgoing',
        )
        text = str(cheque)
        assert 'CHK-001' in text
        assert 'الشركة المرسلة' in text
        assert '15000' in text

    def test_cheque_default_values(self, db):
        """اختبار القيم الافتراضية للشيك."""
        from payments.models import Cheque
        cheque = Cheque.objects.create(
            cheque_number='CHK-DEFAULT',
            bank_name='بنك',
            amount=Decimal('1000.00'),
            due_date=date(2024, 12, 1),
            payer_name='محرر',
            payee_name='مستفيد',
        )
        assert cheque.branch_name == ''
        assert cheque.notes == ''
        assert cheque.status == 'received'

    def test_cheque_type_choices(self, db):
        """اختبار أنواع الشيكات المتاحة."""
        from payments.models import Cheque
        types = ['incoming', 'outgoing']
        for ctype in types:
            cheque = Cheque.objects.create(
                cheque_number=f'CHK-{ctype}',
                bank_name='بنك',
                amount=Decimal('1000.00'),
                due_date=date(2024, 6, 1),
                payer_name='محرر',
                payee_name='مستفيد',
                cheque_type=ctype,
            )
            assert cheque.cheque_type == ctype


class TestReconciliationModel:
    """اختبارات نموذج التسوية."""

    def test_create_reconciliation(self, db):
        """اختبار إنشاء تسوية."""
        from payments.models import PaymentAccount, Reconciliation
        account = PaymentAccount.objects.create(
            account_name='حساب التسوية',
            account_type='bank_account',
        )
        recon = Reconciliation.objects.create(
            account=account,
            period_start=date(2024, 6, 1),
            period_end=date(2024, 6, 30),
            system_balance=Decimal('100000.00'),
            actual_balance=Decimal('100000.00'),
        )
        assert recon.reconciliation_number.startswith('REC-')
        assert recon.difference == Decimal('0')

    def test_reconciliation_auto_status_reconciled(self, db):
        """اختبار التغيير التلقائي للحالة إلى متوازن عند تطابق الأرصدة."""
        from payments.models import PaymentAccount, Reconciliation
        account = PaymentAccount.objects.create(
            account_name='حساب متوازن',
            account_type='bank_account',
        )
        recon = Reconciliation.objects.create(
            account=account,
            period_start=date(2024, 7, 1),
            period_end=date(2024, 7, 31),
            system_balance=Decimal('50000.00'),
            actual_balance=Decimal('50000.00'),
        )
        # يجب أن تكون الحالة تلقائياً "متوازن"
        assert recon.status == 'reconciled'

    def test_reconciliation_status_discrepancy(self, db):
        """اختبار حالة الفارق عند عدم تطابق الأرصدة."""
        from payments.models import PaymentAccount, Reconciliation
        account = PaymentAccount.objects.create(
            account_name='حساب غير متوازن',
            account_type='bank_account',
        )
        recon = Reconciliation.objects.create(
            account=account,
            period_start=date(2024, 8, 1),
            period_end=date(2024, 8, 31),
            system_balance=Decimal('50000.00'),
            actual_balance=Decimal('49500.00'),
        )
        # الحالة الافتراضية هي draft
        assert recon.status == 'draft'
        assert recon.difference == Decimal('-500.00')

    def test_reconciliation_str(self, db):
        """اختبار التمثيل النصي للتسوية."""
        from payments.models import PaymentAccount, Reconciliation
        account = PaymentAccount.objects.create(
            account_name='حساب رئيسي',
            account_type='bank_account',
        )
        recon = Reconciliation.objects.create(
            account=account,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            system_balance=Decimal('80000.00'),
            actual_balance=Decimal('80000.00'),
        )
        assert 'حساب رئيسي' in str(recon)
        assert recon.reconciliation_number in str(recon)

    def test_reconciliation_difference_property(self, db):
        """اختبار خاصية حساب فرق التسوية."""
        from payments.models import PaymentAccount, Reconciliation
        account = PaymentAccount.objects.create(
            account_name='حساب الفرق',
            account_type='bank_account',
        )
        # رصيد فعلي أكبر من رصيد النظام
        recon_positive = Reconciliation.objects.create(
            account=account,
            period_start=date(2024, 9, 1),
            period_end=date(2024, 9, 30),
            system_balance=Decimal('30000.00'),
            actual_balance=Decimal('30500.00'),
        )
        assert recon_positive.difference == Decimal('500.00')
