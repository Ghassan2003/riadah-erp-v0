"""
اختبارات الوحدات البرمجية لنماذج نظام المخازن المتعددة.
Unit Tests for Warehouse (Multi-Warehouse) Models.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestWarehouseModel:
    """اختبارات نموذج المستودع."""

    def test_create_warehouse(self, db):
        """اختبار إنشاء مستودع."""
        from warehouse.models import Warehouse
        wh = Warehouse.objects.create(
            name='مستودع الرياض الرئيسي',
            city='الرياض',
            capacity=Decimal('10000'),
        )
        assert wh.code.startswith('WH-')
        assert wh.is_active is True
        assert wh.city == 'الرياض'

    def test_warehouse_str(self, db):
        """اختبار التمثيل النصي للمستودع."""
        from warehouse.models import Warehouse
        wh = Warehouse.objects.create(name='مستودع جدة', city='جدة')
        assert 'مستودع جدة' in str(wh)
        assert 'WH-' in str(wh)

    def test_auto_generate_warehouse_code(self, db):
        """اختبار التوليد التلقائي لرمز المستودع."""
        from warehouse.models import Warehouse
        wh1 = Warehouse.objects.create(name='مستودع 1')
        wh2 = Warehouse.objects.create(name='مستودع 2')
        assert wh1.code == 'WH-001'
        assert wh2.code == 'WH-002'

    def test_multiple_warehouses(self, db):
        """اختبار إنشاء عدة مستودعات."""
        from warehouse.models import Warehouse
        cities = ['الرياض', 'جدة', 'الدمام', 'مكة']
        for city in cities:
            Warehouse.objects.create(name=f'مستودع {city}', city=city, capacity=Decimal('5000'))
        assert Warehouse.objects.count() == 4

    def test_current_stock_level_empty(self, db):
        """اختبار مستوى المخزون الحالي لمستودع فارغ."""
        from warehouse.models import Warehouse
        wh = Warehouse.objects.create(name='مستودع فارغ')
        assert wh.current_stock_level == 0

    def test_utilized_capacity_zero(self, db):
        """اختبار نسبة الاستخدام لمستودع بلا سعة."""
        from warehouse.models import Warehouse
        wh = Warehouse.objects.create(name='مستودع بلا سعة', capacity=0)
        assert wh.utilized_capacity == 0

    def test_utilized_capacity_with_stock(self, db):
        """اختبار نسبة الاستخدام مع مخزون."""
        from warehouse.models import Warehouse, WarehouseStock
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع اختبار', capacity=Decimal('1000'))
        product = Product.objects.create(name='منتج', sku='WS-001', unit_price=10)
        WarehouseStock.objects.create(warehouse=wh, product=product, quantity=Decimal('250'))
        assert wh.utilized_capacity == 25.0

    def test_products_count(self, db):
        """اختبار عداد المنتجات في المستودع."""
        from warehouse.models import Warehouse, WarehouseStock
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع منتجات')
        p1 = Product.objects.create(name='منتج 1', sku='WS-002', unit_price=10)
        p2 = Product.objects.create(name='منتج 2', sku='WS-003', unit_price=20)
        WarehouseStock.objects.create(warehouse=wh, product=p1, quantity=Decimal('10'))
        WarehouseStock.objects.create(warehouse=wh, product=p2, quantity=Decimal('0'))
        assert wh.products_count == 1  # فقط المنتجات بكمية > 0


class TestWarehouseStockModel:
    """اختبارات نموذج رصيد المخزون."""

    def test_create_warehouse_stock(self, db):
        """اختبار إنشاء رصيد مخزون."""
        from warehouse.models import Warehouse, WarehouseStock
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع')
        product = Product.objects.create(name='منتج', sku='STK-001', unit_price=100)
        stock = WarehouseStock.objects.create(
            warehouse=wh, product=product,
            quantity=Decimal('100'), reserved_quantity=Decimal('20'),
        )
        assert stock.available_quantity == Decimal('80')

    def test_unique_warehouse_product(self, db):
        """اختبار عدم تكرار نفس المنتج في نفس المستودع."""
        from warehouse.models import Warehouse, WarehouseStock
        from inventory.models import Product
        from django.db import IntegrityError
        wh = Warehouse.objects.create(name='مستودع فريد')
        product = Product.objects.create(name='منتج فريد', sku='UNQ-001', unit_price=50)
        WarehouseStock.objects.create(warehouse=wh, product=product, quantity=Decimal('10'))
        with pytest.raises(IntegrityError):
            WarehouseStock.objects.create(warehouse=wh, product=product, quantity=Decimal('20'))

    def test_stock_str(self, db):
        """اختبار التمثيل النصي لرصيد المخزون."""
        from warehouse.models import Warehouse, WarehouseStock
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع تمثيل')
        product = Product.objects.create(name='لابتوب', sku='LAP-001', unit_price=3000)
        stock = WarehouseStock.objects.create(warehouse=wh, product=product, quantity=Decimal('5'))
        assert 'لابتوب' in str(stock)
        assert '5' in str(stock)


class TestStockTransferModel:
    """اختبارات نموذج تحويل المخزون."""

    def test_create_stock_transfer(self, db):
        """اختبار إنشاء تحويل مخزون."""
        from warehouse.models import Warehouse, StockTransfer
        wh_from = Warehouse.objects.create(name='مستودع المصدر')
        wh_to = Warehouse.objects.create(name='مستودع الوجهة')
        transfer = StockTransfer.objects.create(
            from_warehouse=wh_from,
            to_warehouse=wh_to,
        )
        assert transfer.status == 'draft'
        assert transfer.transfer_number.startswith('TRF-')

    def test_transfer_str(self, db):
        """اختبار التمثيل النصي لتحويل المخزون."""
        from warehouse.models import Warehouse, StockTransfer
        wh1 = Warehouse.objects.create(name='الرياض')
        wh2 = Warehouse.objects.create(name='جدة')
        transfer = StockTransfer.objects.create(from_warehouse=wh1, to_warehouse=wh2)
        # الـ str يستخدم رموز المستودعات وليس الأسماء
        assert wh1.code in str(transfer)
        assert wh2.code in str(transfer)

    def test_transfer_status_choices(self, db):
        """اختبار حالات التحويل."""
        from warehouse.models import StockTransfer
        expected = ['draft', 'pending', 'in_transit', 'completed', 'cancelled']
        actual = [c[0] for c in StockTransfer.STATUS_CHOICES]
        assert actual == expected


class TestStockTransferItemModel:
    """اختبارات نموذج بند تحويل المخزون."""

    def test_create_transfer_item(self, db):
        """اختبار إنشاء بند تحويل."""
        from warehouse.models import StockTransfer, StockTransferItem
        from inventory.models import Product
        from warehouse.models import Warehouse
        wh1 = Warehouse.objects.create(name='مصدر')
        wh2 = Warehouse.objects.create(name='وجهة')
        transfer = StockTransfer.objects.create(from_warehouse=wh1, to_warehouse=wh2)
        product = Product.objects.create(name='منتج نقل', sku='TRF-001', unit_price=100)
        item = StockTransferItem.objects.create(
            transfer=transfer, product=product, quantity=Decimal('50')
        )
        assert item.received_quantity == Decimal('0')

    def test_transfer_item_str(self, db):
        """اختبار التمثيل النصي لبند التحويل."""
        from warehouse.models import StockTransfer, StockTransferItem
        from inventory.models import Product
        from warehouse.models import Warehouse
        wh1 = Warehouse.objects.create(name='أ')
        wh2 = Warehouse.objects.create(name='ب')
        transfer = StockTransfer.objects.create(from_warehouse=wh1, to_warehouse=wh2)
        product = Product.objects.create(name='كرسي', sku='CHR-001', unit_price=200)
        item = StockTransferItem.objects.create(transfer=transfer, product=product, quantity=Decimal('10'))
        assert 'كرسي' in str(item)


class TestStockAdjustmentModel:
    """اختبارات نموذج تسوية المخزون."""

    def test_create_adjustment(self, db):
        """اختبار إنشاء تسوية مخزون."""
        from warehouse.models import StockAdjustment, Warehouse
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع تسوية')
        product = Product.objects.create(name='منتج تسوية', sku='ADJ-001', unit_price=50)
        adj = StockAdjustment.objects.create(
            warehouse=wh,
            reason='damage',
            product=product,
            previous_quantity=Decimal('100'),
            new_quantity=Decimal('95'),
        )
        assert adj.adjustment_number.startswith('ADJ-')
        assert adj.difference == Decimal('-5')

    def test_adjustment_reasons(self, db):
        """اختبار أسباب التسوية."""
        from warehouse.models import StockAdjustment
        expected = ['damage', 'theft', 'loss', 'correction', 'count', 'received']
        actual = [c[0] for c in StockAdjustment.REASON_CHOICES]
        assert actual == expected


class TestStockCountModel:
    """اختبارات نموذج جرد المخزون."""

    def test_create_stock_count(self, db):
        """اختبار إنشاء جرد مخزون."""
        from warehouse.models import StockCount, Warehouse
        wh = Warehouse.objects.create(name='مستودع جرد')
        count = StockCount.objects.create(warehouse=wh)
        assert count.count_number.startswith('CNT-')
        assert count.status == 'draft'

    def test_stock_count_item(self, db):
        """اختبار بند جرد مخزون."""
        from warehouse.models import StockCount, StockCountItem, Warehouse
        from inventory.models import Product
        wh = Warehouse.objects.create(name='مستودع بند')
        count = StockCount.objects.create(warehouse=wh)
        product = Product.objects.create(name='منتج جرد', sku='CNT-001', unit_price=75)
        item = StockCountItem.objects.create(
            count=count, product=product,
            system_quantity=Decimal('100'), counted_quantity=Decimal('98'),
        )
        assert item.difference == Decimal('-2')

    def test_stock_count_status_choices(self, db):
        """اختبار حالات الجرد."""
        from warehouse.models import StockCount
        expected = ['draft', 'in_progress', 'completed', 'adjusted']
        actual = [c[0] for c in StockCount.STATUS_CHOICES]
        assert actual == expected
