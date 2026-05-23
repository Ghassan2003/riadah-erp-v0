"""
Unit tests for Startup Finance models.
اختبارات وحدة لنماذج تمويل الشركات الناشئة.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestStartupProfile:
    """اختبارات ملف الشركة الناشئة."""

    def test_create_startup_profile(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة اختبار',
            industry='تقنية',
            stage='seed',
            team_size=5,
            currency='SAR',
            initial_funding=Decimal('500000'),
            monthly_recurring_revenue=Decimal('100000'),
            monthly_operating_expenses=Decimal('150000'),
            cash_balance=Decimal('2000000'),
        )
        assert profile.company_name == 'شركة اختبار'
        assert profile.stage == 'seed'
        assert profile.team_size == 5

    def test_burn_rate_calculation(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة اختبار',
            monthly_recurring_revenue=Decimal('100000'),
            monthly_operating_expenses=Decimal('150000'),
            cash_balance=Decimal('2000000'),
        )
        # burn_rate = expenses - revenue = 150000 - 100000 = 50000
        assert profile.burn_rate == Decimal('50000')

    def test_burn_rate_zero_when_profitable(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة مربحة',
            monthly_recurring_revenue=Decimal('200000'),
            monthly_operating_expenses=Decimal('100000'),
            cash_balance=Decimal('1000000'),
        )
        # لا حرق عندما الإيرادات > المصروفات
        assert profile.burn_rate == Decimal('0')

    def test_runway_months_calculation(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة اختبار',
            monthly_recurring_revenue=Decimal('100000'),
            monthly_operating_expenses=Decimal('150000'),
            cash_balance=Decimal('2000000'),
        )
        # runway = 2000000 / 50000 = 40 months
        assert profile.runway_months == Decimal('40')

    def test_runway_infinite_when_no_burn(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة مربحة',
            monthly_recurring_revenue=Decimal('200000'),
            monthly_operating_expenses=Decimal('100000'),
            cash_balance=Decimal('1000000'),
        )
        assert profile.runway_months == 999

    def test_gross_margin_calculation(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة اختبار',
            monthly_recurring_revenue=Decimal('200000'),
            monthly_operating_expenses=Decimal('120000'),
        )
        # margin = (200000 - 120000) / 200000 * 100 = 40%
        assert abs(profile.gross_margin_pct - Decimal('40.0')) < Decimal('0.01')

    def test_gross_margin_zero_when_no_revenue(self):
        from startup_finance.models import StartupProfile
        profile = StartupProfile.objects.create(
            company_name='شركة اختبار',
            monthly_recurring_revenue=Decimal('0'),
            monthly_operating_expenses=Decimal('100000'),
        )
        assert profile.gross_margin_pct == 0

    def test_stage_choices(self):
        from startup_finance.models import StartupProfile
        for stage_key, _ in StartupProfile.STAGE_CHOICES:
            profile = StartupProfile.objects.create(
                company_name=f'شركة {stage_key}',
                stage=stage_key,
            )
            assert profile.get_stage_display() is not None


@pytest.mark.django_db
class TestFundingRound:
    """اختبارات جولات التمويل."""

    def _create_profile(self):
        from startup_finance.models import StartupProfile
        return StartupProfile.objects.create(
            company_name='شركة اختبار',
            cash_balance=Decimal('1000000'),
        )

    def test_create_funding_round(self):
        from startup_finance.models import FundingRound
        profile = self._create_profile()
        round_obj = FundingRound.objects.create(
            startup=profile,
            round_type='seed',
            round_name='Seed Round',
            amount_raised=Decimal('500000'),
            valuation_pre_money=Decimal('3000000'),
            round_date=date(2024, 1, 1),
            investor_names='مستثمر أ',
        )
        assert round_obj.amount_raised == Decimal('500000')
        assert round_obj.round_type == 'seed'

    def test_funding_round_ordering(self):
        from startup_finance.models import FundingRound
        profile = self._create_profile()
        FundingRound.objects.create(
            startup=profile, round_type='seed',
            amount_raised=Decimal('100000'), round_date=date(2023, 1, 1),
        )
        FundingRound.objects.create(
            startup=profile, round_type='series_a',
            amount_raised=Decimal('500000'), round_date=date(2024, 1, 1),
        )
        rounds = list(FundingRound.objects.filter(startup=profile))
        assert rounds[0].round_date > rounds[1].round_date


@pytest.mark.django_db
class TestBurnRateEntry:
    """اختبارات سجلات معدل الحرق."""

    def _create_profile(self):
        from startup_finance.models import StartupProfile
        return StartupProfile.objects.create(
            company_name='شركة اختبار',
            monthly_recurring_revenue=Decimal('100000'),
            monthly_operating_expenses=Decimal('100000'),
            cash_balance=Decimal('1000000'),
        )

    def test_create_expense_entry(self):
        from startup_finance.models import BurnRateEntry
        profile = self._create_profile()
        entry = BurnRateEntry.objects.create(
            startup=profile,
            month=date(2024, 1, 1),
            category='payroll',
            amount=Decimal('50000'),
            entry_type='expense',
            is_recurring=True,
        )
        assert entry.amount == Decimal('50000')
        assert entry.is_recurring is True

    def test_unique_together_constraint(self):
        from startup_finance.models import BurnRateEntry
        from django.db import IntegrityError
        profile = self._create_profile()
        BurnRateEntry.objects.create(
            startup=profile, month=date(2024, 1, 1),
            category='payroll', entry_type='expense', amount=Decimal('100'),
        )
        with pytest.raises(IntegrityError):
            BurnRateEntry.objects.create(
                startup=profile, month=date(2024, 1, 1),
                category='payroll', entry_type='expense', amount=Decimal('200'),
            )


@pytest.mark.django_db
class TestSubscriptionPlan:
    """اختبارات خطط الاشتراك."""

    def test_create_plan(self):
        from startup_finance.models import SubscriptionPlan
        plan = SubscriptionPlan.objects.create(
            name='الاحترافية',
            price_monthly=Decimal('299'),
            price_yearly=Decimal('2990'),
            trial_days=14,
            max_users=25,
        )
        assert plan.price_monthly == Decimal('299')
        assert plan.is_active is True


@pytest.mark.django_db
class TestFinancialEntry:
    """اختبارات القيود المالية مع Idempotency."""

    def _create_profile(self):
        from startup_finance.models import StartupProfile
        return StartupProfile.objects.create(
            company_name='شركة اختبار',
            cash_balance=Decimal('1000000'),
        )

    def test_create_entry_with_idempotency_key(self):
        from startup_finance.models import FinancialEntry
        profile = self._create_profile()
        entry = FinancialEntry.objects.create(
            startup=profile,
            entry_type='revenue',
            category='subscription',
            amount=Decimal('299'),
            entry_date=date(2024, 1, 1),
            idempotency_key='stripe_charge_12345',
            external_reference='ch_12345',
            external_source='stripe',
        )
        assert entry.idempotency_key == 'stripe_charge_12345'
        assert entry.external_source == 'stripe'

    def test_idempotency_key_unique(self):
        from startup_finance.models import FinancialEntry
        from django.db import IntegrityError
        profile = self._create_profile()
        FinancialEntry.objects.create(
            startup=profile, entry_type='revenue',
            amount=Decimal('100'),
            idempotency_key='unique_key_123',
        )
        with pytest.raises(IntegrityError):
            FinancialEntry.objects.create(
                startup=profile, entry_type='revenue',
                amount=Decimal('200'),
                idempotency_key='unique_key_123',
            )

    def test_entry_without_idempotency(self):
        from startup_finance.models import FinancialEntry
        profile = self._create_profile()
        entry = FinancialEntry.objects.create(
            startup=profile,
            entry_type='expense',
            category='marketing',
            amount=Decimal('500'),
        )
        assert entry.idempotency_key == ''


@pytest.mark.django_db
class TestFinancialKPI:
    """اختبارات مؤشرات الأداء المالي المخزنة."""

    def _create_profile(self):
        from startup_finance.models import StartupProfile
        return StartupProfile.objects.create(
            company_name='شركة اختبار',
            cash_balance=Decimal('1000000'),
        )

    def test_create_kpi(self):
        from startup_finance.models import FinancialKPI
        profile = self._create_profile()
        kpi = FinancialKPI.objects.create(
            startup=profile,
            month=date(2024, 1, 1),
            mrr=Decimal('185000'),
            arr=Decimal('2220000'),
            burn_rate=Decimal('135000'),
            runway_months=Decimal('7.4'),
            total_subscribers=42,
            churn_rate_pct=Decimal('5.2'),
        )
        assert kpi.arr == kpi.mrr * 12
        assert kpi.runway_months == Decimal('7.4')

    def test_unique_together_profile_month(self):
        from startup_finance.models import FinancialKPI
        from django.db import IntegrityError
        profile = self._create_profile()
        FinancialKPI.objects.create(
            startup=profile, month=date(2024, 1, 1),
            mrr=Decimal('100000'),
        )
        with pytest.raises(IntegrityError):
            FinancialKPI.objects.create(
                startup=profile, month=date(2024, 1, 1),
                mrr=Decimal('200000'),
            )
