"""
Views for Startup Finance module — واجهات برمجة التطبيقات المالية للشركات الناشئة.
يدعم: CRUD لجميع النماذج، لوحة تحكم المؤسسين، حساب KPIs، Idempotency.
"""

from rest_framework import generics, views, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.db.models import Sum, Count, Avg, F, DecimalField, Value, Q
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import timedelta

from users.permissions import IsAdmin

from .models import (
    StartupProfile, FundingRound, BurnRateEntry,
    SubscriptionPlan, SubscriptionCycle, CustomerMetric,
    FinancialKPI, FinancialEntry,
)
from .serializers import (
    StartupProfileSerializer, StartupProfileListSerializer,
    FundingRoundSerializer, FundingRoundListSerializer,
    BurnRateEntrySerializer, BurnRateEntryCreateSerializer,
    SubscriptionPlanSerializer, SubscriptionCycleSerializer,
    SubscriptionCycleCreateSerializer,
    CustomerMetricSerializer, CustomerMetricCreateSerializer,
    FinancialKPISerializer,
    FinancialEntrySerializer, FinancialEntryCreateSerializer,
    FounderDashboardSerializer,
)


# ═══════════════════════════════════════════════════════════════
# Mixins المساعدة
# ═══════════════════════════════════════════════════════════════

class StartupFinanceBaseMixin:
    """Mixin أساسي يضيف created_by تلقائياً."""

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ═══════════════════════════════════════════════════════════════
# 1. Startup Profile — CRUD
# ═══════════════════════════════════════════════════════════════

class StartupProfileListCreateView(StartupFinanceBaseMixin, generics.ListCreateAPIView):
    """GET: قائمة الشركات | POST: إنشاء شركة جديدة."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = StartupProfile.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'industry']
    ordering_fields = ['company_name', 'stage', 'monthly_recurring_revenue', 'cash_balance']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StartupProfileSerializer
        return StartupProfileListSerializer


class StartupProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل شركة ناشئة."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = StartupProfile.objects.all()
    serializer_class = StartupProfileSerializer


# ═══════════════════════════════════════════════════════════════
# 2. Funding Rounds — CRUD
# ═══════════════════════════════════════════════════════════════

class FundingRoundListCreateView(StartupFinanceBaseMixin, generics.ListCreateAPIView):
    """GET: قائمة جولات التمويل | POST: إنشاء جولة جديدة."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = FundingRoundSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['round_name', 'investor_names']
    ordering_fields = ['round_date', 'amount_raised', 'round_type']

    def get_queryset(self):
        qs = FundingRound.objects.select_related('startup')
        startup_id = self.request.query_params.get('startup')
        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FundingRoundSerializer
        return FundingRoundListSerializer


class FundingRoundDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل جولة تمويل."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = FundingRound.objects.select_related('startup')
    serializer_class = FundingRoundSerializer


# ═══════════════════════════════════════════════════════════════
# 3. Burn Rate Entries — CRUD
# ═══════════════════════════════════════════════════════════════

class BurnRateEntryListCreateView(StartupFinanceBaseMixin, generics.ListCreateAPIView):
    """GET: سجلات معدل الحرق | POST: إنشاء سجل جديد."""
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['month', 'category', 'amount', 'entry_type']

    def get_queryset(self):
        qs = BurnRateEntry.objects.select_related('startup', 'created_by')
        startup_id = self.request.query_params.get('startup')
        month_from = self.request.query_params.get('month_from')
        month_to = self.request.query_params.get('month_to')
        entry_type = self.request.query_params.get('entry_type')

        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        if month_from:
            qs = qs.filter(month__gte=month_from)
        if month_to:
            qs = qs.filter(month__lte=month_to)
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BurnRateEntryCreateSerializer
        return BurnRateEntrySerializer


class BurnRateEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل سجل معدل الحرق."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = BurnRateEntry.objects.all()
    serializer_class = BurnRateEntrySerializer


# ═══════════════════════════════════════════════════════════════
# 4. Subscription Plans — CRUD
# ═══════════════════════════════════════════════════════════════

class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
    """GET: خطط الاشتراك | POST: إنشاء خطة جديدة."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price_monthly', 'name']


class SubscriptionPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل خطة اشتراك."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


# ═══════════════════════════════════════════════════════════════
# 5. Subscription Cycles — CRUD
# ═══════════════════════════════════════════════════════════════

class SubscriptionCycleListCreateView(StartupFinanceBaseMixin, generics.ListCreateAPIView):
    """GET: دورات الاشتراك | POST: إنشاء دورة جديدة."""
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name']
    ordering_fields = ['start_date', 'amount', 'status']

    def get_queryset(self):
        qs = SubscriptionCycle.objects.select_related('startup', 'plan', 'customer')
        startup_id = self.request.query_params.get('startup')
        status = self.request.query_params.get('status')
        plan_id = self.request.query_params.get('plan')

        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        if status:
            qs = qs.filter(status=status)
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubscriptionCycleCreateSerializer
        return SubscriptionCycleSerializer


class SubscriptionCycleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل دورة اشتراك."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = SubscriptionCycle.objects.select_related('startup', 'plan', 'customer')
    serializer_class = SubscriptionCycleSerializer


# ═══════════════════════════════════════════════════════════════
# 6. Customer Metrics — CRUD
# ═══════════════════════════════════════════════════════════════

class CustomerMetricListCreateView(generics.ListCreateAPIView):
    """GET: مقاييس العملاء | POST: إنشاء مقياس جديد."""
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'acquisition_channel']
    ordering_fields = ['acquisition_cost', 'monthly_revenue', 'total_revenue', 'created_at']

    def get_queryset(self):
        qs = CustomerMetric.objects.select_related('startup', 'customer')
        startup_id = self.request.query_params.get('startup')
        channel = self.request.query_params.get('acquisition_channel')
        cohort = self.request.query_params.get('cohort')

        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        if channel:
            qs = qs.filter(acquisition_channel=channel)
        if cohort:
            qs = qs.filter(cohort=cohort)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerMetricCreateSerializer
        return CustomerMetricSerializer


class CustomerMetricDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل مقاييس العميل."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = CustomerMetric.objects.all()
    serializer_class = CustomerMetricSerializer


# ═══════════════════════════════════════════════════════════════
# 7. Financial Entries — CRUD مع Idempotency
# ═══════════════════════════════════════════════════════════════

class FinancialEntryListCreateView(StartupFinanceBaseMixin, generics.ListCreateAPIView):
    """GET: القيود المالية | POST: إنشاء قيد جديد (يدعم Idempotency)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'category', 'external_reference']
    ordering_fields = ['entry_date', 'amount', 'entry_type', 'category']

    def get_queryset(self):
        qs = FinancialEntry.objects.select_related('startup', 'created_by')
        startup_id = self.request.query_params.get('startup')
        entry_type = self.request.query_params.get('entry_type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        source = self.request.query_params.get('source')

        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        if date_from:
            qs = qs.filter(entry_date__gte=date_from)
        if date_to:
            qs = qs.filter(entry_date__lte=date_to)
        if source:
            qs = qs.filter(external_source=source)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FinancialEntryCreateSerializer
        return FinancialEntrySerializer


class FinancialEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE: تفاصيل قيد مالي."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = FinancialEntry.objects.all()
    serializer_class = FinancialEntrySerializer


# ═══════════════════════════════════════════════════════════════
# 8. Financial KPIs — قراءة فقط (تُحسب عبر Celery)
# ═══════════════════════════════════════════════════════════════

class FinancialKPIListView(generics.ListAPIView):
    """GET: مؤشرات الأداء المالي (تاريخية)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = FinancialKPISerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['month']

    def get_queryset(self):
        qs = FinancialKPI.objects.select_related('startup')
        startup_id = self.request.query_params.get('startup')
        months = int(self.request.query_params.get('months', 12))
        if startup_id:
            qs = qs.filter(startup_id=startup_id)
        return qs[:months]


# ═══════════════════════════════════════════════════════════════
# 9. لوحة تحكم المؤسسين (Founder Dashboard) — نقطة النهاية الرئيسية
# ═══════════════════════════════════════════════════════════════

@method_decorator(cache_page(60), name='get')
class FounderDashboardView(views.APIView):
    """
    GET /api/startup-finance/dashboard/
    لوحة تحكم المؤسسين — تجمع بيانات من عدة نماذج في استجابة واحدة.
    تُخزّن مؤقتاً لمدة 60 ثانية.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        startup_id = request.query_params.get('startup')
        now = timezone.now()

        # 1. ملف الشركة
        profile_qs = StartupProfile.objects.all()
        if startup_id:
            profile_qs = profile_qs.filter(id=startup_id)
        profile = profile_qs.first()

        if not profile:
            # إنشاء ملف افتراضي إذا لم يكن موجوداً
            profile, created = StartupProfile.objects.get_or_create(
                defaults={
                    'company_name': 'شركة ناشئة',
                    'stage': 'seed',
                    'team_size': 1,
                }
            )

        # 2. KPIs الأخيرة
        latest_kpi = FinancialKPI.objects.filter(
            startup=profile
        ).order_by('-month').first()

        # 3. إجمالي التمويل
        total_funding = FundingRound.objects.filter(
            startup=profile
        ).aggregate(
            t=Coalesce(Sum('amount_raised'), Value(0), output_field=DecimalField(max_digits=18, decimal_places=2))
        )['t']

        # 4. إحصائيات الاشتراكات
        sub_stats = SubscriptionCycle.objects.filter(startup=profile).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            new=Count('id', filter=Q(start_date__year=now.year, start_date__month=now.month)),
            churned=Count('id', filter=Q(status='churned')),
        )
        active_subs = sub_stats['active'] or 0

        # 5. MRR من الاشتراكات النشطة
        mrr = SubscriptionCycle.objects.filter(
            startup=profile, status='active'
        ).aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        # 6. CAC و LVT المتوسط
        avg_metrics = CustomerMetric.objects.filter(startup=profile).aggregate(
            avg_cac=Coalesce(Avg('acquisition_cost'), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)),
            avg_ltv=Coalesce(Avg('projected_ltv'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)),
        )

        # 7. معدل فقد العملاء
        churn_rate = 0.0
        if sub_stats['total'] and sub_stats['total'] > 0:
            churn_rate = round(float(sub_stats['churned'] or 0) / sub_stats['total'] * 100, 2)

        # 8. جولات التمويل الأخيرة
        recent_funding = FundingRound.objects.filter(
            startup=profile
        ).order_by('-round_date')[:5]

        # 9. اتجاه معدل الحرق (آخر 12 شهر)
        twelve_months_ago = now - timedelta(days=365)
        burn_trend = BurnRateEntry.objects.filter(
            startup=profile,
            month__gte=twelve_months_ago,
            entry_type='expense',
        ).annotate(
            month_label=TruncMonth('month'),
        ).values('month_label').annotate(
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        ).order_by('month_label')
        burn_rate_trend = [
            {'month': m['month_label'].strftime('%Y-%m'), 'amount': float(m['total'])}
            for m in burn_trend
        ]

        # 10. اتجاه MRR (آخر 12 شهر من KPIs)
        mrr_trend = FinancialKPI.objects.filter(
            startup=profile,
            month__gte=twelve_months_ago,
        ).order_by('month').values('month', 'mrr', 'total_subscribers', 'churn_rate_pct')
        mrr_trend_data = [
            {
                'month': k['month'].strftime('%Y-%m'),
                'mrr': float(k['mrr']),
                'subscribers': k['total_subscribers'],
                'churn_rate': float(k['churn_rate_pct']),
            }
            for k in mrr_trend
        ]

        # 11. اتجاه الإيرادات مقابل المصروفات
        revenue_expense_trend = FinancialKPI.objects.filter(
            startup=profile,
            month__gte=twelve_months_ago,
        ).order_by('month').values('month', 'total_revenue', 'total_expenses')
        re_trend = [
            {
                'month': r['month'].strftime('%Y-%m'),
                'revenue': float(r['total_revenue']),
                'expenses': float(r['total_expenses']),
            }
            for r in revenue_expense_trend
        ]

        # بناء الاستجابة
        data = {
            'profile': StartupProfileListSerializer(profile).data,
            'latest_kpi': FinancialKPISerializer(latest_kpi).data if latest_kpi else None,
            'total_funding': float(total_funding),
            'total_subscribers': sub_stats['total'] or 0,
            'active_subscribers': active_subs,
            'new_subscribers_this_month': sub_stats['new'] or 0,
            'monthly_burn_rate': float(profile.burn_rate),
            'runway_months': float(profile.runway_months),
            'mrr': float(mrr),
            'arr': float(mrr * 12),
            'avg_cac': float(avg_metrics['avg_cac']),
            'avg_ltv': float(avg_metrics['avg_ltv']),
            'churn_rate': churn_rate,
            'recent_funding_rounds': FundingRoundListSerializer(recent_funding, many=True).data,
            'burn_rate_trend': burn_rate_trend,
            'mrr_trend': mrr_trend_data,
            'revenue_expense_trend': re_trend,
        }

        return Response(data)


# ═══════════════════════════════════════════════════════════════
# 10. حساب KPIs — نهاية يدوية أو عبر Celery
# ═══════════════════════════════════════════════════════════════

class CalculateKPIsView(views.APIView):
    """
    POST /api/startup-finance/calculate-kpis/
    يحسب مؤشرات الأداء المالي للشهر الحالي ويخزنها.
    يمكن استدعاؤه يدوياً أو عبر Celery Beat.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        startup_id = request.data.get('startup')
        target_month = request.data.get('month')  # YYYY-MM-DD format

        profiles = StartupProfile.objects.all()
        if startup_id:
            profiles = profiles.filter(id=startup_id)

        calculated = []
        for profile in profiles:
            month_date = target_month or timezone.now().date().replace(day=1)
            month_start = month_date
            month_end = month_date

            # إجمالي الإيرادات من BurnRateEntry
            revenue = BurnRateEntry.objects.filter(
                startup=profile,
                month=month_date,
                entry_type='revenue',
            ).aggregate(
                t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['t']

            # إجمالي المصروفات
            expenses = BurnRateEntry.objects.filter(
                startup=profile,
                month=month_date,
                entry_type='expense',
            ).aggregate(
                t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['t']

            # MRR من الاشتراكات النشطة
            mrr = SubscriptionCycle.objects.filter(
                startup=profile, status='active'
            ).aggregate(
                t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['t']

            # إحصائيات الاشتراك
            sub_stats = SubscriptionCycle.objects.filter(startup=profile).aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='active')),
                new=Count('id', filter=Q(start_date__year=month_date.year, start_date__month=month_date.month)),
                churned=Count('id', filter=Q(status='churned')),
            )

            # CAC و LTV
            metrics = CustomerMetric.objects.filter(startup=profile).aggregate(
                avg_cac=Coalesce(Avg('acquisition_cost'), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)),
                avg_ltv=Coalesce(Avg('projected_ltv'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)),
            )

            # إجمالي التمويل
            total_funding = FundingRound.objects.filter(
                startup=profile, round_date__lte=month_end
            ).aggregate(
                t=Coalesce(Sum('amount_raised'), Value(0), output_field=DecimalField(max_digits=18, decimal_places=2))
            )['t']

            # حساب المشتقات
            burn = max(expenses - revenue, 0)
            runway = float(profile.cash_balance / burn) if burn > 0 else 999
            gross_margin = float((revenue - expenses) / revenue * 100) if revenue > 0 else 0
            net_margin = float((revenue - expenses) / revenue * 100) if revenue > 0 else 0
            ltv_cac = float(metrics['avg_ltv'] / metrics['avg_cac']) if metrics['avg_cac'] > 0 else 0
            churn = round(float(sub_stats['churned'] or 0) / sub_stats['total'] * 100, 2) if sub_stats['total'] > 0 else 0

            # تحديث أو إنشاء KPI
            kpi, _ = FinancialKPI.objects.update_or_create(
                startup=profile,
                month=month_date,
                defaults={
                    'total_revenue': revenue,
                    'mrr': mrr,
                    'arr': mrr * 12,
                    'arpu': mrr / max(sub_stats['active'], 1),
                    'total_expenses': expenses,
                    'burn_rate': burn,
                    'cac': metrics['avg_cac'],
                    'ltv': metrics['avg_ltv'],
                    'runway_months': runway,
                    'gross_margin_pct': gross_margin,
                    'net_margin_pct': net_margin,
                    'ltv_cac_ratio': ltv_cac,
                    'quick_ratio': 1.0,  # يُحسب بدقة أكبر لاحقاً
                    'total_subscribers': sub_stats['total'] or 0,
                    'new_subscribers': sub_stats['new'] or 0,
                    'churned_subscribers': sub_stats['churned'] or 0,
                    'churn_rate_pct': churn,
                    'cash_balance': profile.cash_balance,
                    'total_funding_raised': total_funding,
                }
            )
            calculated.append(kpi.id)

        return Response({
            'status': 'success',
            'message': f'تم حساب {len(calculated)} KPI بنجاح',
            'kpi_ids': calculated,
        }, status=200)
