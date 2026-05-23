/**
 * لوحة تحكم المؤسسين - Founder Dashboard
 * صفحة شاملة لعرض مؤشرات الأداء الرئيسية للشركات الناشئة
 * تستخدم Recharts للرسوم البيانية التفاعلية
 * تدعم الوضع الداكن والثنائية اللغوية (عربي / إنجليزي)
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { startupFinanceAPI } from '../api';
import toast from 'react-hot-toast';
import {
  AreaChart, Area, BarChart, Bar, ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  TrendingUp, TrendingDown, Flame, Clock, DollarSign,
  Users, Target, AlertTriangle, RefreshCw, Loader2,
  Rocket, Wallet, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';

/* ── ألوان الرسوم البيانية ── */
const COLORS = {
  green: '#10b981',
  red: '#ef4444',
  blue: '#3b82f6',
  purple: '#8b5cf6',
  amber: '#f59e0b',
  cyan: '#06b6d4',
  emerald: '#10b981',
  rose: '#f43f5e',
};

/* ── تلميح مخصص للرسوم البيانية ── */
const ChartTooltip = ({ active, payload, label, isDark, locale, fmt }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={`rounded-xl shadow-lg border p-3 text-xs ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-white border-gray-200 text-gray-800'}`}>
      <p className="font-semibold mb-1.5">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-gray-500 dark:text-gray-400">{entry.name}:</span>
          <span className="font-bold" dir="ltr">{fmt(entry.value)}</span>
        </div>
      ))}
    </div>
  );
};

/* ── وسيلة إيضاح مخصصة ── */
const CustomLegend = ({ payload, isDark }) => {
  if (!payload) return null;
  return (
    <div className="flex flex-wrap justify-center gap-3 mt-2">
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-1.5 text-xs">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function FounderDashboardPage() {
  const { t, locale, isRTL } = useI18n();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const isDark = document.documentElement.classList.contains('dark');

  /* ── تنسيق الأرقام حسب اللغة ── */
  const fmt = useCallback((val) =>
    Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }),
    [locale],
  );

  const fmtPct = useCallback((val) =>
    Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }),
    [locale],
  );

  const cur = t('currency') || 'ر.س';

  /* ── جلب بيانات لوحة التحكم ── */
  const fetchDashboard = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const res = await startupFinanceAPI.getDashboard();
      setData(res.data);
    } catch {
      toast.error(t('loadFailed') || 'فشل تحميل البيانات');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [t]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  /* ── حالة التحميل ── */
  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-accent-500" />
        <p className="text-sm text-gray-500 dark:text-gray-400">{t('loading') || 'جاري التحميل...'}</p>
      </div>
    );
  }

  const d = data || {};

  /* ── تحديد لون المشاركة (Runway) ── */
  const getRunwayColor = (months) => {
    if (months > 6) return { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-300', badge: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', dot: 'bg-green-500' };
    if (months > 3) return { bg: 'bg-yellow-50 dark:bg-yellow-900/20', text: 'text-yellow-700 dark:text-yellow-300', badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', dot: 'bg-yellow-500' };
    return { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-300', badge: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300', dot: 'bg-red-500' };
  };

  const getRunwayLabel = (months) => {
    if (months > 6) return t('runwayHealthy') || 'مشاركة صحية';
    if (months > 3) return t('runwayWarning') || 'تنبيه: مشاركة محدودة';
    return t('runwayCritical') || 'حرج: أقل من 3 أشهر';
  };

  /* ── بيانات الرسوم البيانية ── */
  const burnRateTrendData = useMemo(() => {
    const entries = d.burn_rate_trend || d.monthly_burn_rate || [];
    if (entries.length > 0) {
      return entries.map(m => ({
        name: m.month?.slice(5) || m.name || '',
        [t('burnRate')]: m.amount || m.burn_rate || m.total || 0,
      }));
    }
    /* بيانات تجريبية فارغة */
    return [];
  }, [d, t]);

  const revenueVsExpensesData = useMemo(() => {
    const entries = d.revenue_vs_expenses || d.monthly_revenue_expenses || [];
    if (entries.length > 0) {
      return entries.map(m => ({
        name: m.month?.slice(5) || m.name || '',
        [t('revenue')]: m.revenue || m.income || 0,
        [t('expenses')]: m.expenses || m.total_expenses || 0,
      }));
    }
    return [];
  }, [d, t]);

  const mrrTrendData = useMemo(() => {
    const entries = d.mrr_trend || d.monthly_mrr || [];
    if (entries.length > 0) {
      return entries.map(m => ({
        name: m.month?.slice(5) || m.name || '',
        [t('mrr')]: m.mrr || m.amount || 0,
        [t('activeSubscribers')]: m.subscribers || m.active_subscribers || 0,
      }));
    }
    return [];
  }, [d, t]);

  const fundingRoundsData = useMemo(() => {
    const entries = d.funding_rounds || d.recent_funding_rounds || [];
    if (entries.length > 0) {
      return entries.map(r => ({
        name: r.round_name || r.name || r.round_type || t('fundingRounds'),
        [t('amount')]: r.amount || r.raised || 0,
      }));
    }
    return [];
  }, [d, t]);

  const fundingRoundsTable = d.funding_rounds || d.recent_funding_rounds || [];

  /* ── مؤشرات الأداء الرئيسية ── */
  const runwayMonths = d.runway_months || d.runway || 0;
  const runwayColor = getRunwayColor(runwayMonths);

  const kpiCards = [
    {
      title: t('burnRate') || 'معدل الحرق',
      value: `${fmt(d.monthly_burn_rate || d.burn_rate || 0)} ${cur}`,
      icon: Flame,
      trend: d.burn_rate_trend_direction || 'neutral',
      color: 'red',
    },
    {
      title: t('runwayMonths') || 'أشهر المشاركة',
      value: `${fmt(runwayMonths)}`,
      icon: Clock,
      trend: runwayMonths > 6 ? 'up' : runwayMonths > 3 ? 'neutral' : 'down',
      color: 'amber',
      subtitle: getRunwayLabel(runwayMonths),
      subtitleColor: runwayColor,
    },
    {
      title: t('mrr') || 'الإيرادات المتكررة الشهرية',
      value: `${fmt(d.mrr || d.monthly_recurring_revenue || 0)} ${cur}`,
      icon: Wallet,
      trend: d.mrr_trend_direction || 'neutral',
      color: 'green',
    },
    {
      title: t('arr') || 'الإيرادات السنوية المتكررة',
      value: `${fmt(d.arr || d.annual_recurring_revenue || 0)} ${cur}`,
      icon: TrendingUp,
      trend: 'neutral',
      color: 'blue',
    },
    {
      title: t('totalFunding') || 'إجمالي التمويل',
      value: `${fmt(d.total_funding_raised || d.total_funding || 0)} ${cur}`,
      icon: Rocket,
      trend: 'neutral',
      color: 'purple',
    },
    {
      title: t('activeSubscribers') || 'المشتركون النشطون',
      value: `${fmt(d.active_subscribers || d.subscribers || 0)}`,
      icon: Users,
      trend: d.subscribers_trend_direction || 'neutral',
      color: 'cyan',
    },
  ];

  /* ── خريطة الألوان للبطاقات ── */
  const colorMap = {
    red: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400' },
    amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400' },
    green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400' },
    blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400' },
    purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400' },
    cyan: { bg: 'bg-cyan-50 dark:bg-cyan-900/20', text: 'text-cyan-600 dark:text-cyan-400' },
  };

  /* ── مؤشر الاتجاه ── */
  const TrendIndicator = ({ direction }) => {
    if (direction === 'up') return <ArrowUpRight className="w-3.5 h-3.5 text-green-500" />;
    if (direction === 'down') return <ArrowDownRight className="w-3.5 h-3.5 text-red-500" />;
    return null;
  };

  /* ── المقياس الجدولي ── */
  const keyMetrics = [
    {
      label: t('cac') || 'تكلفة الاكتساب',
      value: d.cac || d.customer_acquisition_cost || 0,
      format: 'currency',
      color: COLORS.blue,
    },
    {
      label: t('ltv') || 'قيمة العميل مدى الحياة',
      value: d.ltv || d.lifetime_value || 0,
      format: 'currency',
      color: COLORS.green,
    },
    {
      label: t('churnRate') || 'معدل فقد العملاء',
      value: d.churn_rate || 0,
      format: 'percent',
      color: COLORS.red,
    },
    {
      label: t('ltvCacRatio') || 'نسبة LTV/CAC',
      value: d.ltv_cac_ratio || d.ltv_to_cac || 0,
      format: 'ratio',
      color: COLORS.purple,
    },
    {
      label: t('grossMargin') || 'هامش الربح الإجمالي',
      value: d.gross_margin || 0,
      format: 'percent',
      color: COLORS.emerald,
    },
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* ══════════════════════════════════════════════════
          الرأس - Header
          ══════════════════════════════════════════════════ */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2.5">
              <Rocket className="w-6 h-6 text-accent-500" />
              {t('founderDashboard') || 'لوحة تحكم المؤسسين'}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {t('startupFinance') || 'تمويل الشركات الناشئة'}
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchDashboard(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all disabled:opacity-50 text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {t('refresh') || 'تحديث'}
        </button>
      </div>

      {/* ══════════════════════════════════════════════════
          القسم الأول: بطاقات المؤشرات الرئيسية - KPI Cards
          ══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {kpiCards.map((card, i) => {
          const Icon = card.icon;
          const c = colorMap[card.color] || colorMap.blue;
          return (
            <div
              key={i}
              className={`bg-white dark:bg-gray-800 rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all`}
            >
              {/* رأس البطاقة */}
              <div className="flex items-center justify-between mb-2">
                <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${c.text}`} />
                </div>
                <TrendIndicator direction={card.trend} />
              </div>
              {/* القيمة */}
              <p className="text-base sm:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                {card.value}
              </p>
              {/* العنوان */}
              <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                {card.title}
              </p>
              {/* تسمية فرعية (للمشاركة) */}
              {card.subtitle && (
                <span className={`inline-block mt-1 text-[9px] sm:text-[10px] px-1.5 py-0.5 rounded-full font-medium ${card.subtitleColor?.badge || ''}`}>
                  {card.subtitle}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* ══════════════════════════════════════════════════
          القسم الثاني: الرسوم البيانية - الصف الأول
          ══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* رسم بياني: اتجاه معدل الحرق */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Flame className="w-4 h-4 text-red-500" />
            {t('burnRateTrend') || 'اتجاه معدل الحرق'}
          </h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {burnRateTrendData.length > 0 ? (
                <AreaChart data={burnRateTrendData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="burnGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.red} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLORS.red} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Area
                    type="monotone"
                    dataKey={t('burnRate')}
                    stroke={COLORS.red}
                    strokeWidth={2.5}
                    fill="url(#burnGrad)"
                    dot={{ r: 3, fill: COLORS.red }}
                    activeDot={{ r: 5, stroke: COLORS.red, strokeWidth: 2 }}
                  />
                </AreaChart>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <Flame className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">{t('noData')}</p>
                </div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* رسم بياني: الإيرادات مقابل المصروفات */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-blue-500" />
            {t('revenueVsExpenses') || 'الإيرادات مقابل المصروفات'}
          </h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {revenueVsExpensesData.length > 0 ? (
                <ComposedChart data={revenueVsExpensesData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.green} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLORS.green} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Legend content={<CustomLegend isDark={isDark} />} />
                  <Area
                    type="monotone"
                    dataKey={t('revenue')}
                    stroke={COLORS.green}
                    strokeWidth={2.5}
                    fill="url(#revGrad)"
                    dot={{ r: 3, fill: COLORS.green }}
                  />
                  <Line
                    type="monotone"
                    dataKey={t('expenses')}
                    stroke={COLORS.red}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ r: 2.5, fill: COLORS.red }}
                  />
                </ComposedChart>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <DollarSign className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">{t('noData')}</p>
                </div>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════
          القسم الثالث: الرسوم البيانية - الصف الثاني
          ══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* رسم بياني: اتجاه الإيرادات المتكررة الشهرية */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            {t('mrrTrend') || 'اتجاه الإيرادات المتكررة'}
          </h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {mrrTrendData.length > 0 ? (
                <AreaChart data={mrrTrendData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="mrrGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.green} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLORS.green} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation={isRTL ? 'left' : 'right'} tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Legend content={<CustomLegend isDark={isDark} />} />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey={t('mrr')}
                    stroke={COLORS.green}
                    strokeWidth={2.5}
                    fill="url(#mrrGrad)"
                    dot={{ r: 3, fill: COLORS.green }}
                    activeDot={{ r: 5, stroke: COLORS.green, strokeWidth: 2 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey={t('activeSubscribers')}
                    stroke={COLORS.cyan}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ r: 2.5, fill: COLORS.cyan }}
                  />
                </AreaChart>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <TrendingUp className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">{t('noData')}</p>
                </div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* رسم بياني: جولات التمويل */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-500" />
            {t('fundingRounds') || 'جولات التمويل'}
          </h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {fundingRoundsData.length > 0 ? (
                <BarChart data={fundingRoundsData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="fundGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.purple} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={COLORS.purple} stopOpacity={0.3} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Bar dataKey={t('amount')} fill="url(#fundGrad)" radius={[6, 6, 0, 0]} animationDuration={800} />
                </BarChart>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <Target className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">{t('noData')}</p>
                </div>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════
          القسم الرابع: الجداول التفصيلية
          ══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* جدول: جولات التمويل الأخيرة */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
            <Rocket className="w-4 h-4 text-purple-500" />
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">
              {t('fundingRounds') || 'جولات التمويل'}
            </h3>
          </div>
          {fundingRoundsTable.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 dark:border-gray-700">
                    <th className={`text-xs font-semibold text-gray-500 dark:text-gray-400 px-4 py-2.5 text-start`}>
                      {t('name') || 'الاسم'}
                    </th>
                    <th className={`text-xs font-semibold text-gray-500 dark:text-gray-400 px-4 py-2.5 text-start`}>
                      {t('type') || 'النوع'}
                    </th>
                    <th className={`text-xs font-semibold text-gray-500 dark:text-gray-400 px-4 py-2.5 text-end`}>
                      {t('amount') || 'المبلغ'}
                    </th>
                    <th className={`text-xs font-semibold text-gray-500 dark:text-gray-400 px-4 py-2.5 text-start`}>
                      {t('date') || 'التاريخ'}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50">
                  {fundingRoundsTable.slice(0, 5).map((round, i) => (
                    <tr key={round.id || i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-2.5 text-gray-800 dark:text-gray-200 font-medium">
                        {round.round_name || round.name || '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                          {round.round_type || round.type || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100 font-bold text-end" dir="ltr">
                        {fmt(round.amount || round.raised || 0)} {cur}
                      </td>
                      <td className="px-4 py-2.5 text-gray-500 dark:text-gray-400 text-xs">
                        {round.date || round.created_at || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center">
              <Rocket className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-400 dark:text-gray-500">{t('noData')}</p>
            </div>
          )}
        </div>

        {/* بطاقات: المقاييس الرئيسية */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 sm:p-5">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            {t('customerMetrics') || 'مقاييس العملاء'}
          </h3>
          <div className="space-y-3">
            {keyMetrics.map((metric, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: metric.color }} />
                  <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                    {metric.label}
                  </span>
                </div>
                <span className="text-sm font-bold text-gray-900 dark:text-gray-100" dir="ltr">
                  {metric.format === 'currency' && `${fmt(metric.value)} ${cur}`}
                  {metric.format === 'percent' && `${fmtPct(metric.value)}%`}
                  {metric.format === 'ratio' && `${fmtPct(metric.value)}x`}
                </span>
              </div>
            ))}
          </div>

          {/* مقياس بصري لنسبة LTV/CAC */}
          <div className="mt-5 pt-4 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {t('ltvCacRatio') || 'نسبة LTV/CAC'}
              </span>
              <span className={`text-xs font-bold ${
                (d.ltv_cac_ratio || d.ltv_to_cac || 0) >= 3
                  ? 'text-green-600 dark:text-green-400'
                  : (d.ltv_cac_ratio || d.ltv_to_cac || 0) >= 1
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-red-600 dark:text-red-400'
              }`}>
                {fmtPct(d.ltv_cac_ratio || d.ltv_to_cac || 0)}x
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  (d.ltv_cac_ratio || d.ltv_to_cac || 0) >= 3
                    ? 'bg-green-500'
                    : (d.ltv_cac_ratio || d.ltv_to_cac || 0) >= 1
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${Math.min((d.ltv_cac_ratio || d.ltv_to_cac || 0) / 5 * 100, 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[9px] text-gray-400">1x</span>
              <span className="text-[9px] text-gray-400">3x (مثالي)</span>
              <span className="text-[9px] text-gray-400">5x</span>
            </div>
          </div>

          {/* مقياس بصري لمعدل فقد العملاء */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {t('churnRate') || 'معدل فقد العملاء'}
              </span>
              <span className={`text-xs font-bold ${
                (d.churn_rate || 0) <= 3
                  ? 'text-green-600 dark:text-green-400'
                  : (d.churn_rate || 0) <= 7
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-red-600 dark:text-red-400'
              }`}>
                {fmtPct(d.churn_rate || 0)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  (d.churn_rate || 0) <= 3
                    ? 'bg-green-500'
                    : (d.churn_rate || 0) <= 7
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${Math.min((d.churn_rate || 0) / 10 * 100, 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[9px] text-gray-400">0%</span>
              <span className="text-[9px] text-gray-400">5% (جيد)</span>
              <span className="text-[9px] text-gray-400">10%+</span>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════
          التذييل - Footer
          ══════════════════════════════════════════════════ */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between gap-2 text-xs text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-3">
          <span>{t('erpSystem') || 'RIADAH'} v5.0</span>
          <span>{t('startupFinance') || 'تمويل الشركات الناشئة'}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-green-600 dark:text-green-400">{t('systemOnline') || 'النظام يعمل'}</span>
        </div>
      </div>
    </div>
  );
}
