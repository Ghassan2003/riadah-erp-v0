"""
اختبارات الوحدات البرمجية لنماذج المخزون والمنتجات.
Unit Tests for Inventory/Product Models.
"""

import pytest


class TestProductModel:
    """اختبارات نموذج المنتج."""

    def test_create_product(self, product):
        """اختبار إنشاء منتج."""
        assert product.name == 'منتج اختبار'
        assert product.sku == 'TEST-001'
        assert product.quantity == 100
        assert float(product.unit_price) == 50.00
        assert product.is_active is True

    def test_product_str(self, product):
        """اختبار التمثيل النصي."""
        assert 'منتج اختبار' in str(product)
        assert 'TEST-001' in str(product)

    def test_is_low_stock_true(self, product_low_stock):
        """اختبار كشف مخزون منخفض."""
        assert product_low_stock.is_low_stock is True

    def test_is_low_stock_false(self, product):
        """اختبار أن المخزون ليس منخفضاً."""
        assert product.is_low_stock is False

    def test_total_value(self, product):
        """اختبار حساب القيمة الإجمالية."""
        assert product.total_value == product.quantity * product.unit_price

    def test_soft_delete(self, product):
        """اختبار الحذف الناعم."""
        product.soft_delete()
        assert product.is_active is False
        # المنتج لا يظهر في المدير الافتراضي
        from inventory.models import Product
        assert product not in Product.objects.all()

    def test_restore(self, product):
        """اختبار استعادة المنتج المحذوف."""
        product.soft_delete()
        product.restore()
        assert product.is_active is True
        from inventory.models import Product
        assert product in Product.objects.all()

    def test_unique_sku(self, product):
        """اختبار تفرد رمز المنتج."""
        from inventory.models import Product
        from django.db.utils import IntegrityError
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name='منتج آخر',
                sku='TEST-001',
                quantity=10,
                unit_price=30.00,
            )

    def test_product_manager_only_active(self, product, db):
        """اختبار أن المدير الافتراضي يعرض المنتجات النشطة فقط."""
        from inventory.models import Product
        product.soft_delete()
        active_count = Product.objects.count()
        assert active_count == 0

    def test_all_objects_manager(self, product, db):
        """اختبار أن المدير all_objects يعرض جميع المنتجات."""
        from inventory.models import Product
        product.soft_delete()
        all_count = Product.all_objects.count()
        assert all_count == 1

    def test_default_quantity(self, db):
        """اختبار القيمة الافتراضية للكمية."""
        from inventory.models import Product
        p = Product.objects.create(
            name='منتج بدون كمية',
            sku='DEF-001',
            unit_price=10.00,
        )
        assert p.quantity == 0

    def test_reorder_level_default(self, db):
        """اختبار القيمة الافتراضية لحد إعادة الطلب."""
        from inventory.models import Product
        p = Product.objects.create(
            name='منتج حد افتراضي',
            sku='REORDER-001',
            unit_price=10.00,
        )
        assert p.reorder_level == 10
