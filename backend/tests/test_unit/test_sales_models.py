"""
اختبارات الوحدات البرمجية لنماذج المبيعات.
Unit Tests for Sales Models.
"""

import pytest
from django.utils import timezone


class TestCustomerModel:
    """اختبارات نموذج العميل."""

    def test_create_customer(self, customer):
        """اختبار إنشاء عميل."""
        assert customer.name == 'عميل اختبار'
        assert customer.email == 'customer@test.com'
        assert customer.is_active is True

    def test_customer_str(self, customer):
        """اختبار التمثيل النصي."""
        assert customer.name == str(customer)

    def test_soft_delete_customer(self, customer):
        """اختبار الحذف الناعم."""
        customer.soft_delete()
        assert customer.is_active is False

    def test_restore_customer(self, customer):
        """اختبار استعادة العميل."""
        customer.soft_delete()
        customer.restore()
        assert customer.is_active is True


class TestSalesOrderModel:
    """اختبارات نموذج أمر البيع."""

    def test_create_sales_order(self, admin_user, customer):
        """اختبار إنشاء أمر بيع."""
        from sales.models import SalesOrder
        order = SalesOrder.objects.create(
            customer=customer,
            created_by=admin_user,
            notes='اختبار',
        )
        assert order.status == 'draft'
        assert order.total_amount == 0
        assert order.order_number.startswith('SO-')

    def test_order_number_format(self, admin_user, customer):
        """اختبار تنسيق رقم الأمر."""
        from sales.models import SalesOrder
        order = SalesOrder.objects.create(
            customer=customer,
            created_by=admin_user,
        )
        parts = order.order_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'SO'
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # XXXX

    def test_order_number_sequence(self, admin_user, customer):
        """اختبار تسلسل أرقام الأوامر."""
        from sales.models import SalesOrder
        order1 = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        order2 = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        seq1 = int(order1.order_number.split('-')[-1])
        seq2 = int(order2.order_number.split('-')[-1])
        assert seq2 == seq1 + 1

    def test_order_str(self, admin_user, customer):
        """اختبار التمثيل النصي."""
        from sales.models import SalesOrder
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        assert order.order_number in str(order)
        assert customer.name in str(order)

    def test_calculate_total(self, admin_user, customer, product):
        """اختبار حساب الإجمالي."""
        from sales.models import SalesOrder, SalesOrderItem
        from inventory.models import Product
        product2 = Product.objects.create(
            name='منتج ثاني', sku='CALC-002', quantity=50, unit_price=30.00,
        )
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            unit_price=50.00,
        )
        SalesOrderItem.objects.create(
            order=order,
            product=product2,
            quantity=3,
            unit_price=30.00,
        )
        total = order.calculate_total()
        assert total == 340.00  # (5*50) + (3*30)

    def test_confirm_order_deducts_inventory(self, admin_user, customer, product):
        """اختبار أن تأكيد الأمر يخصم من المخزون."""
        from sales.models import SalesOrder, SalesOrderItem
        initial_qty = product.quantity
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order,
            product=product,
            quantity=10,
            unit_price=product.unit_price,
        )
        order.confirm_order()
        product.refresh_from_db()
        assert product.quantity == initial_qty - 10
        assert order.status == 'confirmed'

    def test_confirm_order_insufficient_stock(self, admin_user, customer, product):
        """اختبار تأكيد أمر بكمية غير متوفرة."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order,
            product=product,
            quantity=9999,
            unit_price=product.unit_price,
        )
        with pytest.raises(ValueError):
            order.confirm_order()

    def test_confirm_non_draft_order(self, admin_user, customer, product):
        """اختبار تأكيد أمر ليس في حالة مسودة."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        order.confirm_order()
        order.refresh_from_db()
        with pytest.raises(ValueError):
            order.confirm_order()

    def test_cancel_order_returns_inventory(self, admin_user, customer, product):
        """اختبار أن إلغاء الأمر المؤكد يعيد الكمية للمخزون."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=10, unit_price=50.00,
        )
        order.confirm_order()
        product.refresh_from_db()
        qty_after_confirm = product.quantity

        order.cancel_order()
        product.refresh_from_db()
        assert product.quantity == qty_after_confirm + 10
        assert order.status == 'cancelled'

    def test_change_status_valid_transition(self, admin_user, customer, product):
        """اختبار انتقال الحالة الصالح."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        order.change_status('confirmed')
        assert order.status == 'confirmed'
        order.change_status('shipped')
        assert order.status == 'shipped'
        order.change_status('delivered')
        assert order.status == 'delivered'

    def test_change_status_invalid_transition(self, admin_user, customer):
        """اختبار انتقال الحالة غير الصالح."""
        from sales.models import SalesOrder
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        order.status = 'delivered'
        order.save()
        with pytest.raises(ValueError):
            order.change_status('confirmed')


class TestSalesOrderItemModel:
    """اختبارات نموذج بنود أمر البيع."""

    def test_auto_calculate_subtotal(self, admin_user, customer, product):
        """اختبار الحساب التلقائي للإجمالي الفرعي."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        item = SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        assert item.subtotal == 250.00

    def test_unique_order_product(self, admin_user, customer, product):
        """اختبار عدم تكرار المنتج في نفس الأمر."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        with pytest.raises(Exception):
            SalesOrderItem.objects.create(
                order=order, product=product, quantity=3, unit_price=50.00,
            )
