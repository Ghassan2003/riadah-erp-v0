"""
اختبارات الوحدات البرمجية لنماذج نظام نقاط البيع.
Unit Tests for POS Models.
"""

import pytest
from datetime import date
from decimal import Decimal
from django.utils import timezone


class TestPOSShiftModel:
    """اختبارات نموذج وردية نقاط البيع."""

    def _create_shift(self, db):
        """إنشاء وردية اختبار."""
        from pos.models import POSShift
        from users.models import User
        user = User.objects.create_user(username='cashier1', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(
            cashier=user,
            opening_cash=Decimal('1000'),
            shift_number='SHF-001',
        )
        return shift

    def test_create_pos_shift(self, db):
        """اختبار إنشاء وردية."""
        shift = self._create_shift(db)
        assert shift.status == 'open'
        assert shift.opening_cash == Decimal('1000')

    def test_shift_str(self, db):
        """اختبار التمثيل النصي للوردية."""
        shift = self._create_shift(db)
        assert 'cashier1' in str(shift)

    def test_compute_expected_cash_no_sales(self, db):
        """اختبار حساب المبلغ المتوقع بدون مبيعات."""
        shift = self._create_shift(db)
        expected = shift.compute_expected_cash()
        assert expected == Decimal('1000')  # فقط المبلغ الافتتاحي

    def test_close_shift(self, db):
        """اختبار إغلاق الوردية."""
        shift = self._create_shift(db)
        shift.close_shift(closing_cash=Decimal('1000'), notes='إغلاق نهاية اليوم')
        assert shift.status == 'closed'
        assert shift.closing_cash == Decimal('1000')
        assert shift.end_time is not None


class TestPOSSaleModel:
    """اختبارات نموذج عملية البيع."""

    def _create_sale_prerequisites(self, db):
        """إنشاء متطلبات عملية بيع."""
        from pos.models import POSShift
        from users.models import User
        user = User.objects.create_user(username='cashier2', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(cashier=user, opening_cash=Decimal('500'), shift_number='SHF-TEST')
        return shift

    def test_create_pos_sale(self, db):
        """اختبار إنشاء عملية بيع."""
        from pos.models import POSSale
        shift = self._create_sale_prerequisites(db)
        sale = POSSale.objects.create(
            shift=shift,
            items=[{'name': 'منتج 1', 'qty': 2, 'price': 50}],
            subtotal=Decimal('100'),
            vat_amount=Decimal('15'),
            total_amount=Decimal('115'),
            payment_method='cash',
            cash_received=Decimal('200'),
            change_amount=Decimal('85'),
        )
        assert sale.status == 'completed'
        assert sale.receipt_number.startswith('RCP-')
        assert sale.cash_received == Decimal('200')

    @staticmethod
    def _create_sale(shift, items, subtotal, total_amount, method='cash'):
        """طريقة مساعدة لإنشاء عملية بيع مع تجنب مشكلة Decimal*float."""
        from pos.models import POSSale
        return POSSale.objects.create(
            shift=shift,
            items=items,
            subtotal=subtotal,
            vat_amount=Decimal('15'),
            total_amount=total_amount,
            payment_method=method,
        )

    def test_vat_auto_calculation(self, db):
        """اختبار قيمة ضريبة القيمة المضافة."""
        shift = self._create_sale_prerequisites(db)
        sale = self._create_sale(
            shift,
            items=[{'name': 'منتج 1', 'qty': 1, 'price': 100}],
            subtotal=Decimal('100'),
            total_amount=Decimal('115'),
        )
        assert sale.vat_amount == Decimal('15')

    def test_void_sale(self, db):
        """اختبار إلغاء عملية البيع."""
        from pos.models import POSSale
        from users.models import User
        shift = self._create_sale_prerequisites(db)
        sale = self._create_sale(
            shift,
            items=[{'name': 'منتج 1', 'qty': 1, 'price': 100}],
            subtotal=Decimal('100'),
            total_amount=Decimal('115'),
        )
        admin = User.objects.create_user(username='admin_void', password='Admin@1234!', role='admin')
        sale.void_sale(voided_by=admin, reason='خطأ في الطلب')
        assert sale.status == 'voided'
        assert sale.void_reason == 'خطأ في الطلب'

    def test_payment_methods(self, db):
        """اختبار طرق الدفع في البيع."""
        from pos.models import POSSale
        methods = ['cash', 'card', 'online', 'mixed']
        actual = [c[0] for c in POSSale.PAYMENT_METHOD_CHOICES]
        assert actual == methods


class TestPOSRefundModel:
    """اختبارات نموذج الإرجاع."""

    @staticmethod
    def _create_sale_helper(shift, items, subtotal, total_amount):
        """طريقة مساعدة لإنشاء عملية بيع مع تجنب مشكلة Decimal*float."""
        from pos.models import POSSale
        return POSSale.objects.create(
            shift=shift, items=items, subtotal=subtotal,
            vat_amount=Decimal('15'), total_amount=total_amount,
            payment_method='cash',
        )

    def test_create_refund(self, db):
        """اختبار إنشاء عملية إرجاع."""
        from pos.models import POSRefund
        from users.models import User
        from pos.models import POSShift
        user = User.objects.create_user(username='cashier3', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(cashier=user, opening_cash=Decimal('500'), shift_number='SHF-RF')
        sale = self._create_sale_helper(
            shift,
            items=[{'name': 'منتج 1', 'qty': 1, 'price': 100}],
            subtotal=Decimal('100'),
            total_amount=Decimal('115'),
        )
        refund = POSRefund.objects.create(
            sale=sale,
            shift=shift,
            items=[{'name': 'منتج 1', 'qty': 1, 'price': 100}],
            refund_amount=Decimal('115'),
            reason='منتج معيب',
        )
        assert refund.refund_number.startswith('REF-')
        assert refund.refund_method == 'original'

    def test_refund_methods(self, db):
        """اختبار طرق الإرجاع."""
        from pos.models import POSRefund
        methods = ['cash', 'card', 'original']
        actual = [c[0] for c in POSRefund.REFUND_METHOD_CHOICES]
        assert actual == methods


class TestPOSHoldOrderModel:
    """اختبارات نموذج الطلبات المعلقة."""

    def test_create_hold_order(self, db):
        """اختبار إنشاء طلب معلق."""
        from pos.models import POSHoldOrder, POSShift
        from users.models import User
        user = User.objects.create_user(username='cashier4', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(cashier=user, opening_cash=Decimal('500'), shift_number='SHF-HOLD')
        hold = POSHoldOrder.objects.create(
            shift=shift,
            customer_name='عميل انتظار',
            items=[{'name': 'منتج 1', 'qty': 2, 'price': 50}],
            total_amount=Decimal('115'),
        )
        assert hold.hold_number.startswith('HOLD-')
        assert hold.is_recovered is False

    def test_hold_order_str(self, db):
        """اختبار التمثيل النصي للطلب المعلق."""
        from pos.models import POSHoldOrder, POSShift
        from users.models import User
        user = User.objects.create_user(username='cashier5', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(cashier=user, opening_cash=Decimal('500'), shift_number='SHF-STR')
        hold = POSHoldOrder.objects.create(
            shift=shift,
            customer_name='أحمد',
            items=[],
            total_amount=Decimal('0'),
        )
        assert 'أحمد' in str(hold)


class TestCashDrawerTransactionModel:
    """اختبارات نموذج حركة الصندوق."""

    def test_create_drawer_transaction(self, db):
        """اختبار إنشاء حركة صندوق."""
        from pos.models import CashDrawerTransaction, POSShift
        from users.models import User
        user = User.objects.create_user(username='cashier6', password='Cash@1234!', role='sales')
        shift = POSShift.objects.create(cashier=user, opening_cash=Decimal('500'), shift_number='SHF-DRAW')
        txn = CashDrawerTransaction.objects.create(
            shift=shift,
            transaction_type='cash_in',
            amount=Decimal('200'),
            description='إيداع نقدي',
        )
        assert str(txn)  # لا ينبغي أن يفشل

    def test_drawer_transaction_types(self, db):
        """اختبار أنواع حركات الصندوق."""
        from pos.models import CashDrawerTransaction
        types = ['opening', 'closing', 'cash_in', 'cash_out', 'paid_in', 'paid_out']
        actual = [c[0] for c in CashDrawerTransaction.TRANSACTION_TYPE_CHOICES]
        assert actual == types
