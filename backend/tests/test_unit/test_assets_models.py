"""
اختبارات الوحدات البرمجية لنماذج نظام الأصول الثابتة.
Unit Tests for Fixed Assets Models.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestAssetCategoryModel:
    """اختبارات نموذج تصنيف الأصل."""

    def test_create_asset_category(self, db):
        """اختبار إنشاء تصنيف أصل."""
        from assets.models import AssetCategory
        cat = AssetCategory.objects.create(
            name='الأثاث المكتبي',
            name_en='Office Furniture',
            useful_life_years=10,
            depreciation_method='straight_line',
            salvage_value_rate=Decimal('10.00'),
        )
        assert cat.is_active is True
        assert cat.depreciation_method == 'straight_line'

    def test_category_str(self, db):
        """اختبار التمثيل النصي للتصنيف."""
        from assets.models import AssetCategory
        cat = AssetCategory.objects.create(name='أجهزة الحاسب')
        assert str(cat) == 'أجهزة الحاسب'

    def test_depreciation_methods(self, db):
        """اختبار طرق الإهلاك."""
        from assets.models import AssetCategory
        methods = ['straight_line', 'declining_balance']
        actual = [c[0] for c in AssetCategory._meta.get_field('depreciation_method').choices]
        assert actual == methods


class TestFixedAssetModel:
    """اختبارات نموذج الأصل الثابت."""

    def _create_category(self, db, method='straight_line', life_years=5):
        """إنشاء تصنيف اختبار."""
        from assets.models import AssetCategory
        return AssetCategory.objects.create(
            name='تصنيف اختبار',
            useful_life_years=life_years,
            depreciation_method=method,
            salvage_value_rate=Decimal('0'),
        )

    def test_create_fixed_asset(self, db):
        """اختبار إنشاء أصل ثابت."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='طابعة HP',
            category=cat,
            purchase_date=date(2024, 1, 15),
            purchase_price=Decimal('5000'),
            salvage_value=Decimal('0'),
            useful_life_months=60,
        )
        assert asset.asset_number.startswith('AST-')
        assert asset.status == 'active'
        assert asset.accumulated_depreciation == Decimal('0')

    def test_asset_str(self, db):
        """اختبار التمثيل النصي للأصل."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='جهاز كمبيوتر',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            useful_life_months=36,
        )
        assert 'جهاز كمبيوتر' in str(asset)

    def test_current_value_new_asset(self, db):
        """اختبار القيمة الحالية لأصل جديد."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل جديد',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            salvage_value=Decimal('1000'),
            useful_life_months=60,
        )
        assert asset.current_value == Decimal('10000')

    def test_current_value_with_depreciation(self, db):
        """اختبار القيمة الحالية مع إهلاك."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل مهلك',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            salvage_value=Decimal('0'),
            useful_life_months=60,
            accumulated_depreciation=Decimal('3000'),
        )
        assert asset.current_value == Decimal('7000')

    def test_current_value_minimum_salvage(self, db):
        """اختبار أن القيمة الحالية لا تقل عن القيمة التخريدية."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل مشطوب',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            salvage_value=Decimal('1000'),
            useful_life_months=60,
            accumulated_depreciation=Decimal('15000'),  # أكثر من القيمة
        )
        assert asset.current_value == Decimal('1000')  # لا تقل عن salvage_value

    def test_straight_line_depreciation(self, db):
        """اختبار الإهلاك بطريقة القسط الثابت."""
        cat = self._create_category(db, method='straight_line')
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل قسط ثابت',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('60000'),
            salvage_value=Decimal('0'),
            useful_life_months=60,  # 5 سنوات
        )
        monthly_dep = asset.calculate_depreciation()
        assert monthly_dep == Decimal('1000')  # 60000 / 60

    def test_straight_line_with_salvage(self, db):
        """اختبار القسط الثابت مع قيمة تخريدية."""
        cat = self._create_category(db, method='straight_line')
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل مع تخريد',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('55000'),
            salvage_value=Decimal('5000'),
            useful_life_months=60,
        )
        monthly_dep = asset.calculate_depreciation()
        assert monthly_dep == Decimal('833.33')  # (55000 - 5000) / 60

    def test_zero_useful_life(self, db):
        """اختبار إهلاك أصل بعمر افتراضي صفري."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل بدون عمر',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            useful_life_months=0,
        )
        assert asset.calculate_depreciation() == Decimal('0.00')

    def test_monthly_depreciation_property(self, db):
        """اختبار خاصية الإهلاك الشهري."""
        cat = self._create_category(db)
        from assets.models import FixedAsset
        asset = FixedAsset.objects.create(
            name='أصل خاصية',
            category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('12000'),
            useful_life_months=12,
        )
        assert asset.monthly_depreciation == Decimal('1000')

    def test_asset_status_choices(self, db):
        """اختبار حالات الأصل."""
        from assets.models import FixedAsset
        expected = ['active', 'in_maintenance', 'disposed', 'sold', 'lost']
        actual = [c[0] for c in FixedAsset.STATUS_CHOICES]
        assert actual == expected


class TestAssetTransferModel:
    """اختبارات نموذج نقل الأصل."""

    def test_create_asset_transfer(self, db):
        """اختبار إنشاء نقل أصل."""
        from assets.models import AssetTransfer, FixedAsset, AssetCategory
        from hr.models import Department
        cat = AssetCategory.objects.create(name='تصنيف نقل')
        asset = FixedAsset.objects.create(
            name='أصل منقول', category=cat,
            purchase_date=date.today(), purchase_price=Decimal('5000'),
            useful_life_months=60,
        )
        dept_from = Department.objects.create(name='قسم المصدر')
        dept_to = Department.objects.create(name='قسم الوجهة')
        transfer = AssetTransfer.objects.create(
            asset=asset,
            from_department=dept_from,
            to_department=dept_to,
            transfer_date=date.today(),
        )
        assert 'أصل منقول' in str(transfer)


class TestAssetMaintenanceModel:
    """اختبارات نموذج صيانة الأصل."""

    def test_create_maintenance(self, db):
        """اختبار إنشاء سجل صيانة."""
        from assets.models import AssetMaintenance, FixedAsset, AssetCategory
        cat = AssetCategory.objects.create(name='تصنيف صيانة')
        asset = FixedAsset.objects.create(
            name='أصل صيانة', category=cat,
            purchase_date=date.today(), purchase_price=Decimal('5000'),
            useful_life_months=60,
        )
        maint = AssetMaintenance.objects.create(
            asset=asset,
            maintenance_type='preventive',
            description='صيانة دورية',
            cost=Decimal('500'),
            maintenance_date=date.today(),
        )
        assert maint.status == 'scheduled'
        assert 'وقائية' in maint.get_maintenance_type_display()

    def test_maintenance_types(self, db):
        """اختبار أنواع الصيانة."""
        from assets.models import AssetMaintenance
        expected = ['preventive', 'corrective', 'emergency']
        actual = [c[0] for c in AssetMaintenance.TYPE_CHOICES]
        assert actual == expected


class TestAssetDisposalModel:
    """اختبارات نموذج تخريد الأصل."""

    def test_create_disposal(self, db):
        """اختبار إنشاء تخريد."""
        from assets.models import AssetDisposal, FixedAsset, AssetCategory
        cat = AssetCategory.objects.create(name='تصنيف تخريد')
        asset = FixedAsset.objects.create(
            name='أصل مخرد', category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            salvage_value=Decimal('0'),
            useful_life_months=60,
            accumulated_depreciation=Decimal('10000'),
        )
        disposal = AssetDisposal.objects.create(
            asset=asset,
            disposal_type='sold',
            disposal_date=date.today(),
            disposal_value=Decimal('2000'),
        )
        assert disposal.loss_gain == Decimal('2000')

    def test_disposal_loss(self, db):
        """اختبار خسارة التخريد."""
        from assets.models import AssetDisposal, FixedAsset, AssetCategory
        cat = AssetCategory.objects.create(name='تصنيف خسارة')
        asset = FixedAsset.objects.create(
            name='أصل خسارة', category=cat,
            purchase_date=date.today(),
            purchase_price=Decimal('10000'),
            salvage_value=Decimal('0'),
            useful_life_months=60,
            accumulated_depreciation=Decimal('5000'),
        )
        disposal = AssetDisposal.objects.create(
            asset=asset,
            disposal_type='scraped',
            disposal_date=date.today(),
            disposal_value=Decimal('1000'),
        )
        assert disposal.loss_gain == Decimal('-4000')  # 1000 - 5000

    def test_disposal_types(self, db):
        """اختبار أنواع التخريد."""
        from assets.models import AssetDisposal
        expected = ['sold', 'scraped', 'donated', 'lost']
        actual = [c[0] for c in AssetDisposal.DISPOSAL_TYPE_CHOICES]
        assert actual == expected
