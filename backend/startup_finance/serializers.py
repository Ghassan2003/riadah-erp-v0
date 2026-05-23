"""
Serializers for Startup Finance module.
يوفر تسلسل البيانات (serialization) لجميع النماذج المالية.
"""

from rest_framework import serializers
from django.db.models import Sum, Count, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    StartupProfile,
    FundingRound,
    BurnRateEntry,
    SubscriptionPlan,
    SubscriptionCycle,
    CustomerMetric,
    FinancialKPI,
    FinancialEntry,
)


# ═══════════════════════════════════════════════════════════════
# Startup Profile
# ═══════════════════════════════════════════════════════════════

class StartupProfileSerializer(serializers.ModelSerializer):
    """تسلسل ملف الشركة الناشئة مع الحقول المحسوبة."""

    burn_rate = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True,
        help_text='معدل الحرق الشهري',
    )
    runway_months = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True,
        help_text='أشهر المشاركة المتبقية',
    )
    gross_margin_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True,
        help_text='هامش الربح الإجمالي %',
    )

    class Meta:
        model = StartupProfile
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class StartupProfileListSerializer(serializers.ModelSerializer):
    """تسلسل مبسط لعرض القوائم."""

    burn_rate = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True,
    )
    runway_months = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True,
    )
    stage_display = serializers.CharField(
        source='get_stage_display', read_only=True,
    )

    class Meta:
        model = StartupProfile
        fields = [
            'id', 'company_name', 'stage', 'stage_display',
            'industry', 'team_size', 'currency',
            'monthly_recurring_revenue', 'monthly_operating_expenses',
            'cash_balance', 'burn_rate', 'runway_months',
        ]


# ═══════════════════════════════════════════════════════════════
# Funding Rounds
# ═══════════════════════════════════════════════════════════════

class FundingRoundSerializer(serializers.ModelSerializer):
    """تسلسل جولات التمويل."""

    round_type_display = serializers.CharField(
        source='get_round_type_display', read_only=True,
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True, default='',
    )

    class Meta:
        model = FundingRound
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, attrs):
        """التحقق من صحة البيانات."""
        if attrs.get('equity_diluted') and attrs.get('valuation_pre_money'):
            # التحقق من منطق التقييم
            if attrs.get('valuation_post_money') and attrs['valuation_pre_money'] > 0:
                expected_post = attrs['valuation_pre_money'] + attrs.get('amount_raised', 0)
                if abs(attrs['valuation_post_money'] - expected_post) > attrs['valuation_pre_money'] * 0.05:
                    raise serializers.ValidationError({
                        'valuation_post_money': 'التقييم بعد الجولة يجب أن يساوي تقريباً التقييم قبل + المبلغ المرفوع'
                    })
        return attrs


class FundingRoundListSerializer(serializers.ModelSerializer):
    """تسلسل مبسط لعرض جولات التمويل."""

    round_type_display = serializers.CharField(
        source='get_round_type_display', read_only=True,
    )

    class Meta:
        model = FundingRound
        fields = [
            'id', 'round_type', 'round_type_display', 'round_name',
            'amount_raised', 'valuation_post_money', 'round_date',
        ]


# ═══════════════════════════════════════════════════════════════
# Burn Rate Entries
# ═══════════════════════════════════════════════════════════════

class BurnRateEntrySerializer(serializers.ModelSerializer):
    """تسلسل سجلات معدل الحرق."""

    entry_type_display = serializers.CharField(
        source='get_entry_type_display', read_only=True,
    )
    category_display = serializers.CharField(
        source='get_category_display', read_only=True,
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True, default='',
    )

    class Meta:
        model = BurnRateEntry
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')


class BurnRateEntryCreateSerializer(serializers.ModelSerializer):
    """تسلسل لإنشاء سجل معدل الحرق."""

    class Meta:
        model = BurnRateEntry
        fields = ['startup', 'month', 'category', 'amount', 'entry_type', 'description', 'is_recurring']


# ═══════════════════════════════════════════════════════════════
# Subscription Plans & Cycles
# ═══════════════════════════════════════════════════════════════

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """تسلسل خطط الاشتراك."""

    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_subscriber_count(self, obj):
        """عدد المشتركين النشطين في هذه الخطة."""
        return obj.cycles.filter(status='active').count()


class SubscriptionCycleSerializer(serializers.ModelSerializer):
    """تسلسل دورات الاشتراك."""

    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    billing_cycle_display = serializers.CharField(
        source='get_billing_cycle_display', read_only=True,
    )
    plan_name = serializers.CharField(
        source='plan.name', read_only=True,
    )
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionCycle
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def get_days_remaining(self, obj):
        """عدد الأيام المتبقية في الاشتراك."""
        if not obj.end_date or obj.status in ('cancelled', 'churned'):
            return 0
        delta = (obj.end_date - timezone.now().date()).days
        return max(delta, 0)


class SubscriptionCycleCreateSerializer(serializers.ModelSerializer):
    """تسلسل لإنشاء دورة اشتراك."""

    class Meta:
        model = SubscriptionCycle
        fields = [
            'startup', 'customer', 'customer_name', 'plan',
            'status', 'billing_cycle', 'amount',
            'start_date', 'end_date', 'trial_end_date', 'notes',
        ]


# ═══════════════════════════════════════════════════════════════
# Customer Metrics
# ═══════════════════════════════════════════════════════════════

class CustomerMetricSerializer(serializers.ModelSerializer):
    """تسلسل مقاييس العملاء."""

    ltv_cac_ratio = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True,
    )
    payback_months = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True,
    )

    class Meta:
        model = CustomerMetric
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CustomerMetricCreateSerializer(serializers.ModelSerializer):
    """تسلسل لإنشاء مقاييس العميل."""

    class Meta:
        model = CustomerMetric
        fields = [
            'startup', 'customer', 'customer_name', 'acquisition_channel',
            'acquisition_cost', 'monthly_revenue', 'months_active',
            'total_revenue', 'projected_ltv', 'cohort', 'notes',
        ]


# ═══════════════════════════════════════════════════════════════
# Financial KPIs
# ═══════════════════════════════════════════════════════════════

class FinancialKPISerializer(serializers.ModelSerializer):
    """تسلسل مؤشرات الأداء المالي."""

    month_display = serializers.SerializerMethodField()

    def get_month_display(self, obj):
        return obj.month.strftime('%Y-%m') if obj.month else ''

    class Meta:
        model = FinancialKPI
        fields = '__all__'
        read_only_fields = ('id', 'calculated_at')


# ═══════════════════════════════════════════════════════════════
# Financial Entries
# ═══════════════════════════════════════════════════════════════

class FinancialEntrySerializer(serializers.ModelSerializer):
    """تسلسل القيود المالية."""

    entry_type_display = serializers.CharField(
        source='get_entry_type_display', read_only=True,
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True, default='',
    )

    class Meta:
        model = FinancialEntry
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')


class FinancialEntryCreateSerializer(serializers.ModelSerializer):
    """تسلسل لإنشاء قيد مالي مع Idempotency."""

    class Meta:
        model = FinancialEntry
        fields = [
            'startup', 'entry_type', 'category', 'amount', 'description',
            'entry_date', 'idempotency_key', 'external_reference',
            'external_source', 'metadata',
        ]

    def validate_idempotency_key(self, value):
        """التحقق من عدم تكرار مفتاح عدم التكرار."""
        if value:
            model = self.Meta.model
            if model.objects.filter(idempotency_key=value).exists():
                raise serializers.ValidationError(
                    'هذا المعرف موجود مسبقاً — القيد تم تسجيله من قبل (idempotent)'
                )
        return value


# ═══════════════════════════════════════════════════════════════
# Founder Dashboard — aggregated response
# ═══════════════════════════════════════════════════════════════

class FounderDashboardSerializer(serializers.Serializer):
    """تسلسل لوحة تحكم المؤسسين — بيانات مجمعة من عدة نماذج."""

    profile = StartupProfileSerializer(read_only=True)
    latest_kpi = FinancialKPISerializer(read_only=True)
    total_funding = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_subscribers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    monthly_burn_rate = serializers.DecimalField(max_digits=16, decimal_places=2)
    runway_months = serializers.DecimalField(max_digits=6, decimal_places=1)
    mrr = serializers.DecimalField(max_digits=16, decimal_places=2)
    arr = serializers.DecimalField(max_digits=18, decimal_places=2)
    avg_cac = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_ltv = serializers.DecimalField(max_digits=16, decimal_places=2)
    churn_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    recent_funding_rounds = FundingRoundListSerializer(many=True, read_only=True)
    burn_rate_trend = serializers.ListField(child=serializers.DictField(), read_only=True)
    mrr_trend = serializers.ListField(child=serializers.DictField(), read_only=True)
    revenue_expense_trend = serializers.ListField(child=serializers.DictField(), read_only=True)
