"""
اختبارات الوحدات البرمجية لنماذج نظام الفواتير الضريبية.
Unit Tests for Invoicing (Tax Invoicing) Models.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestInvoiceModel:
    """اختبارات نموذج الفاتورة."""

    def _create_invoice_dependencies(self, db):
        """إنشاء المتطلبات الأساسية لفاتورة."""
        from sales.models import Customer
        from inventory.models import Product
        customer = Customer.objects.create(
            name='عميل اختبار', phone='0501234567',
            address='الرياض',
        )
        product = Product.objects.create(
            name='منتج فاتورة', sku='INV-001',
            unit_price=Decimal('100'), quantity=50,
        )
        return customer, product

    def test_create_invoice(self, db):
        """اختبار إنشاء فاتورة."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        assert invoice.status == 'draft'
        assert invoice.payment_status == 'unpaid'
        assert invoice.vat_rate == Decimal('15.00')
        assert invoice.company_tax_number == '300000000000003'

    def test_auto_generate_invoice_number(self, db):
        """اختبار التوليد التلقائي لرقم الفاتورة."""
        from invoicing.models import Invoice
        inv1 = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today()
        )
        assert inv1.invoice_number.startswith('INV-')

    def test_vat_calculation(self, db):
        """اختبار حساب ضريبة القيمة المضافة."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        assert invoice.vat_amount == Decimal('150.00')
        assert invoice.total_amount == Decimal('1150.00')

    def test_percentage_discount(self, db):
        """اختبار الخصم بالنسبة المئوية."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000'),
            discount_type='percentage',
            discount_value=Decimal('10'),
        )
        assert invoice.discount_amount == Decimal('100.00')
        assert invoice.total_after_discount == Decimal('900.00')
        # VAT on discounted amount: 900 * 15% = 135
        assert invoice.vat_amount == Decimal('135.00')
        assert invoice.total_amount == Decimal('1035.00')

    def test_fixed_discount(self, db):
        """اختبار الخصم بمبلغ ثابت."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('500'),
            discount_type='fixed',
            discount_value=Decimal('50'),
        )
        assert invoice.discount_amount == Decimal('50.00')
        assert invoice.total_after_discount == Decimal('450.00')
        assert invoice.vat_amount == Decimal('67.50')

    def test_remaining_amount(self, db):
        """اختبار حساب المبلغ المتبقي."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        assert invoice.remaining_amount == Decimal('1150.00')

    def test_invoice_types(self, db):
        """اختبار أنواع الفواتير."""
        from invoicing.models import Invoice
        types = ['sales', 'purchase', 'credit_note', 'debit_note']
        for inv_type in types:
            Invoice.objects.create(
                invoice_type=inv_type,
                issue_date=date.today(),
                due_date=date.today(),
                subtotal=Decimal('100'),
            )
        assert Invoice.objects.count() == 4

    def test_invoice_with_customer(self, db):
        """اختبار إنشاء فاتورة مع عميل."""
        customer, _ = self._create_invoice_dependencies(db)
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales',
            customer=customer,
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        assert invoice.customer.name == 'عميل اختبار'


class TestInvoiceItemModel:
    """اختبارات نموذج بند الفاتورة."""

    def test_create_invoice_item(self, db):
        """اختبار إنشاء بند فاتورة."""
        from invoicing.models import Invoice, InvoiceItem
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today()
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            description='بند اختبار',
            quantity=Decimal('5'),
            unit_price=Decimal('100'),
        )
        assert item.subtotal == Decimal('500.00')
        assert item.vat_amount == Decimal('75.00')
        assert item.total == Decimal('575.00')

    def test_invoice_item_with_percentage_discount(self, db):
        """اختبار بند فاتورة مع خصم نسبي."""
        from invoicing.models import Invoice, InvoiceItem
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today()
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            description='بند مع خصم',
            quantity=Decimal('10'),
            unit_price=Decimal('50'),
            discount_type='percentage',
            discount_value=Decimal('10'),
        )
        # Line subtotal = 10 * 50 = 500, discount = 50
        assert item.subtotal == Decimal('450.00')
        assert item.vat_amount == Decimal('67.50')
        assert item.total == Decimal('517.50')

    def test_invoice_item_with_product(self, db):
        """اختبار بند فاتورة مع منتج."""
        from sales.models import Customer
        from inventory.models import Product
        customer = Customer.objects.create(
            name='عميل منتج', phone='0501234567', address='الرياض',
        )
        product = Product.objects.create(
            name='منتج بند', sku='INV-002',
            unit_price=Decimal('100'), quantity=50,
        )
        from invoicing.models import Invoice, InvoiceItem
        invoice = Invoice.objects.create(
            invoice_type='sales', customer=customer,
            issue_date=date.today(), due_date=date.today()
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            description='منتج فاتورة',
            quantity=Decimal('2'),
            unit_price=Decimal('100'),
        )
        assert item.product.name == 'منتج بند'


class TestPaymentModel:
    """اختبارات نموذج الدفعة."""

    def test_create_payment(self, db):
        """اختبار إنشاء دفعة."""
        from invoicing.models import Invoice, Payment
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('500'),
            payment_method='bank_transfer',
            payment_date=date.today(),
        )
        assert payment.payment_number.startswith('PAY-')
        # The invoice payment status should be updated
        invoice.refresh_from_db()
        assert invoice.paid_amount == Decimal('500.00')
        assert invoice.payment_status == 'partially_paid'

    def test_full_payment_updates_status(self, db):
        """اختبار تحديث حالة الفاتورة عند الدفع الكامل."""
        from invoicing.models import Invoice, Payment
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today(),
            subtotal=Decimal('1000'),
        )
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total_amount,
            payment_method='cash',
            payment_date=date.today(),
        )
        invoice.refresh_from_db()
        assert invoice.payment_status == 'paid'
        assert invoice.status == 'paid'

    def test_payment_methods(self, db):
        """اختبار طرق الدفع المتاحة."""
        from invoicing.models import Payment
        methods = ['bank_transfer', 'cash', 'cheque', 'card', 'online']
        actual = [c[0] for c in Payment.PAYMENT_METHOD_CHOICES]
        assert actual == methods


class TestPaymentReminderModel:
    """اختبارات نموذج تذكير الدفع."""

    def test_create_payment_reminder(self, db):
        """اختبار إنشاء تذكير دفع."""
        from invoicing.models import Invoice, PaymentReminder
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today()
        )
        reminder = PaymentReminder.objects.create(
            invoice=invoice,
            reminder_type='first',
            message='تذكير بالدفع',
            sent_via='email',
        )
        assert reminder.status == 'pending'
        assert str(reminder)  # لا ينبغي أن يفشل
