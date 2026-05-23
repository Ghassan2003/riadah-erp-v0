"""
اختبارات الوحدات البرمجية لنماذج نظام العقود.
Unit Tests for Contracts Models.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal


class TestContractModel:
    """اختبارات نموذج العقد."""

    def test_create_contract(self, db):
        """اختبار إنشاء عقد."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد صيانة المبنى',
            contract_type='service',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            value=Decimal('120000'),
        )
        assert contract.contract_number.startswith('CTR-')
        assert contract.status == 'draft'
        assert contract.currency == 'SAR'

    def test_contract_str(self, db):
        """اختبار التمثيل النصي للعقد."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد توريد',
            contract_type='purchase',
            start_date=date.today(),
        )
        assert 'عقد توريد' in str(contract)

    def test_remaining_days_future(self, db):
        """اختبار الأيام المتبقية لعقد مستقبلي."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد مستقبلي',
            contract_type='service',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
        )
        assert contract.remaining_days == 90

    def test_remaining_days_expired(self, db):
        """اختبار الأيام المتبقية لعقد منتهي."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد منتهي',
            contract_type='service',
            start_date=date.today() - timedelta(days=400),
            end_date=date.today() - timedelta(days=35),
        )
        assert contract.remaining_days == 0

    def test_remaining_days_no_end(self, db):
        """اختبار الأيام المتبقية لعقد بدون تاريخ انتهاء."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد مفتوح',
            contract_type='service',
            start_date=date.today(),
        )
        assert contract.remaining_days is None

    def test_is_expired(self, db):
        """اختبار خاصية انتهاء العقد."""
        from contracts.models import Contract
        expired = Contract.objects.create(
            title='منتهي', contract_type='service',
            start_date=date.today() - timedelta(days=400),
            end_date=date.today() - timedelta(days=30),
        )
        active = Contract.objects.create(
            title='نشط', contract_type='service',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        assert expired.is_expired is True
        assert active.is_expired is False

    def test_is_expired_no_end(self, db):
        """اختبار انتهاء عقد بدون تاريخ انتهاء."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='مفتوح', contract_type='service',
            start_date=date.today(),
        )
        assert contract.is_expired is False

    def test_days_active(self, db):
        """اختبار عدد أيام تفعيل العقد."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد نشط',
            contract_type='service',
            start_date=date.today() - timedelta(days=100),
            end_date=date.today() + timedelta(days=265),
        )
        assert contract.days_active == 365

    def test_contract_types(self, db):
        """اختبار أنواع العقود."""
        from contracts.models import Contract
        expected = ['sales', 'purchase', 'service', 'rental', 'employment', 'consultancy', 'maintenance', 'other']
        actual = [c[0] for c in Contract.TYPE_CHOICES]
        assert actual == expected

    def test_contract_status_choices(self, db):
        """اختبار حالات العقد."""
        from contracts.models import Contract
        expected = ['draft', 'active', 'expired', 'terminated', 'renewed', 'cancelled']
        actual = [c[0] for c in Contract.STATUS_CHOICES]
        assert actual == expected

    def test_vat_inclusive_default(self, db):
        """اختبار أن القيمة الافتراضية لشمل الضريبة هي True."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد ضريبة', contract_type='service',
            start_date=date.today(), value=Decimal('100000'),
        )
        assert contract.vat_inclusive is True

    def test_renewal_reminder_days(self, db):
        """اختبار أيام تذكير التجديد."""
        from contracts.models import Contract
        contract = Contract.objects.create(
            title='عقد تذكير', contract_type='service',
            start_date=date.today(), renewal_reminder_days=60,
        )
        assert contract.renewal_reminder_days == 60


class TestContractMilestoneModel:
    """اختبارات نموذج مرحلة العقد."""

    def test_create_milestone(self, db):
        """اختبار إنشاء مرحلة عقد."""
        from contracts.models import Contract, ContractMilestone
        contract = Contract.objects.create(
            title='عقد مراحل', contract_type='service',
            start_date=date.today(), value=Decimal('300000'),
        )
        milestone = ContractMilestone.objects.create(
            contract=contract,
            title='المرحلة الأولى - التصميم',
            description='تصميم المخططات',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('100000'),
        )
        assert milestone.status == 'pending'

    def test_milestone_str(self, db):
        """اختبار التمثيل النصي للمرحلة."""
        from contracts.models import Contract, ContractMilestone
        contract = Contract.objects.create(
            title='عقد تمثيل', contract_type='service', start_date=date.today()
        )
        milestone = ContractMilestone.objects.create(
            contract=contract,
            title='المرحلة النهائية',
            due_date=date.today(),
            amount=Decimal('50000'),
        )
        assert 'المرحلة النهائية' in str(milestone)

    def test_milestone_status_choices(self, db):
        """اختبار حالات المرحلة."""
        from contracts.models import ContractMilestone
        expected = ['pending', 'in_progress', 'completed', 'overdue']
        actual = [c[0] for c in ContractMilestone.STATUS_CHOICES]
        assert actual == expected


class TestContractPaymentModel:
    """اختبارات نموذج دفعة العقد."""

    def test_create_contract_payment(self, db):
        """اختبار إنشاء دفعة عقد."""
        from contracts.models import Contract, ContractMilestone, ContractPayment
        contract = Contract.objects.create(
            title='عقد دفعات', contract_type='service',
            start_date=date.today(), value=Decimal('200000'),
        )
        milestone = ContractMilestone.objects.create(
            contract=contract, title='مرحلة 1',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('100000'),
        )
        payment = ContractPayment.objects.create(
            contract=contract,
            milestone=milestone,
            amount=Decimal('100000'),
            due_date=date.today() + timedelta(days=30),
        )
        assert payment.payment_status == 'pending'
        assert payment.paid_amount == Decimal('0')

    def test_payment_status_choices(self, db):
        """اختبار حالات دفع العقد."""
        from contracts.models import ContractPayment
        expected = ['pending', 'paid', 'partially_paid', 'overdue']
        actual = [c[0] for c in ContractPayment.PAYMENT_STATUS_CHOICES]
        assert actual == expected

    def test_payment_str(self, db):
        """اختبار التمثيل النصي لدفعة العقد."""
        from contracts.models import Contract, ContractPayment
        contract = Contract.objects.create(
            title='عقد دفع تمثيل', contract_type='service', start_date=date.today()
        )
        payment = ContractPayment.objects.create(
            contract=contract,
            amount=Decimal('50000'),
            due_date=date.today() + timedelta(days=30),
        )
        assert 'عقد دفع تمثيل' in str(payment)
