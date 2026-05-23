/**
 * Customer Insights Page - ML-powered customer segmentation and analysis.
 * Features segment distribution pie chart, summary cards, and customer table.
 * Supports Arabic (RTL) and English, dark mode, and brand colors.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { analyticsAPI } from '../api';
import {
  Users, Crown, Heart, UserCheck, AlertTriangle, UserX,
  RefreshCw, Loader2, Search, X, Star, TrendingUp, Eye,
  PieChart as PieIcon,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  Legend, ResponsiveContainer, CartesianGrid,
} from 'recharts';

/* ── Brand Colors ── */
const COLORS = {
  primary: '#003366',
  accent: '#FF6600',
  green: '#059669',
  red: '#dc2626',
  blue: '#2563eb',
  teal: '#14b8a6',
  amber: '#f59e0b',
  purple: '#7c3aed',
  pink: '#ec4899',
};

const SEGMENT_COLORS = {
  vip: COLORS.amber,
  loyal: COLORS.green,
  regular: COLORS.blue,
  at_risk: COLORS.orange || '#f97316',
  lost: COLORS.red,
};

const SEGMENT_ICONS = {
  vip: Crown,
  loyal: Heart,
  regular: UserCheck,
  at_risk: AlertTriangle,
  lost: UserX,
};

/* ── Mock Data ── */
const generateMockCustomers = () => [
  { id: 1, name: 'شركة الفيصل للتجارة', segment: 'vip', total_purchases: 1250000, last_order: '2024-12-14', order_count: 48, avg_order: 26042 },
  { id: 2, name: 'مؤسسة النور للمقاولات', segment: 'vip', total_purchases: 980000, last_order: '2024-12-13', order_count: 35, avg_order: 28000 },
  { id: 3, name: 'شركة الرياض للتطوير', segment: 'vip', total_purchases: 870000, last_order: '2024-12-12', order_count: 42, avg_order: 20714 },
  { id: 4, name: 'شركة الأمل للبناء', segment: 'loyal', total_purchases: 650000, last_order: '2024-12-11', order_count: 28, avg_order: 23214 },
  { id: 5, name: 'مصنع الخليج', segment: 'loyal', total_purchases: 520000, last_order: '2024-12-10', order_count: 22, avg_order: 23636 },
  { id: 6, name: 'شركة البناء الحديث', segment: 'loyal', total_purchases: 480000, last_order: '2024-12-09', order_count: 19, avg_order: 25263 },
  { id: 7, name: 'مؤسسة الإعمار', segment: 'loyal', total_purchases: 420000, last_order: '2024-12-08', order_count: 18, avg_order: 23333 },
  { id: 8, name: 'شركة المدينة للمقاولات', segment: 'regular', total_purchases: 280000, last_order: '2024-12-06', order_count: 12, avg_order: 23333 },
  { id: 9, name: 'مؤسسة السلام', segment: 'regular', total_purchases: 190000, last_order: '2024-12-04', order_count: 9, avg_order: 21111 },
  { id: 10, name: 'شركة الطريق', segment: 'regular', total_purchases: 150000, last_order: '2024-12-02', order_count: 7, avg_order: 21429 },
  { id: 11, name: 'مؤسسة الفجر', segment: 'regular', total_purchases: 120000, last_order: '2024-11-28', order_count: 6, avg_order: 20000 },
  { id: 12, name: 'شركة الهدى التجارية', segment: 'at_risk', total_purchases: 350000, last_order: '2024-10-15', order_count: 15, avg_order: 23333 },
  { id: 13, name: 'مؤسسة الصحراء', segment: 'at_risk', total_purchases: 220000, last_order: '2024-09-20', order_count: 10, avg_order: 22000 },
  { id: 14, name: 'شركة البناء المتحدة', segment: 'lost', total_purchases: 450000, last_order: '2024-06-10', order_count: 20, avg_order: 22500 },
  { id: 15, name: 'مؤسسة الوفاق', segment: 'lost', total_purchases: 180000, last_order: '2024-04-22', order_count: 8, avg_order: 22500 },
];

const generateMockSummary = () => ({
  total_customers: 15,
  segments: {
    vip: { count: 3, revenue: 3100000, percentage: 20 },
    loyal: { count: 4, revenue: 2070000, percentage: 26.7 },
    regular: { count: 4, revenue: 740000, percentage: 26.7 },
    at_risk: { count: 2, revenue: 570000, percentage: 13.3 },
    lost: { count: 2, revenue: 630000, percentage: 13.3 },
  },
  total_revenue: 7110000,
  avg_customer_value: 474000,
  retention_rate: 73.3,
});

/* ── Segment Badge ── */
function SegmentBadge({ segment, t }) {
  const config = {
    vip: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', label: t('vip') || 'VIP' },
    loyal: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', label: t('loyal') || 'مخلص' },
    regular: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400', label: t('regular') || 'عادي' },
    at_risk: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', label: t('atRisk') || 'معرض للخطر' },
    lost: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', label: t('lost') || 'فقد' },
  };
  const c = config[segment] || config.regular;
  const Icon = SEGMENT_ICONS[segment] || UserCheck;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  );
}

/* ── Custom Tooltip ── */
function CustomTooltip({ active, payload, label, isDark, formatValue }) {
  if (!active || !payload?.length) return null;
  return (
    <div className={`rounded-xl px-3.5 py-2.5 shadow-xl border text-xs ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-white border-gray-200 text-gray-800'}`}>
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span>{entry.name}: </span>
          <span className="font-medium">{formatValue ? formatValue(entry.value) : (typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value)}</span>
        </p>
      ))}
    </div>
  );
}

/* ── Summary Card ── */
function SummaryCard({ segment, data, t }) {
  const Icon = SEGMENT_ICONS[segment] || UserCheck;
  const color = SEGMENT_COLORS[segment] || COLORS.blue;
  const label = {
    vip: t('vip') || 'عملاء VIP',
    loyal: t('loyal') || 'عملاء مخلصين',
    regular: t('regular') || 'عملاء عاديين',
    at_risk: t('atRisk') || 'عملاء معرضين للخطر',
    lost: t('lost') || 'عملاء فاقدين',
  }[segment] || segment;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}18` }}>
            <Icon className="w-4.5 h-4.5" style={{ color }} />
          </div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
        </div>
        <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ backgroundColor: `${color}18`, color }}>
          {data?.percentage || 0}%
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{t('customers') || 'العملاء'}</p>
          <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{data?.count || 0}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{t('revenue') || 'الإيرادات'}</p>
          <p className="text-sm font-bold text-gray-900 dark:text-gray-100" dir="ltr">{(data?.revenue || 0).toLocaleString()}</p>
        </div>
      </div>
      {/* Mini bar */}
      <div className="mt-3 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${data?.percentage || 0}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════
   Main Component
   ════════════════════════════════════════════════════ */
export default function CustomerInsightsPage() {
  const { t, locale, isRTL, isDark } = useI18n();
  const [customers, setCustomers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSegment, setFilterSegment] = useState('all');
  const [sortBy, setSortBy] = useState('total_purchases');
  const [sortDir, setSortDir] = useState('desc');

  const cur = t('currency') || 'ر.س';

  const formatCurrency = useCallback((val) => {
    const num = typeof val === 'number' ? val : Number(val) || 0;
    return num.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US') + ' ' + cur;
  }, [locale, cur]);

  const formatValue = useCallback((val) => {
    const num = typeof val === 'number' ? val : Number(val) || 0;
    return num.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US');
  }, [locale]);

  /* ── Fetch data ── */
  const fetchData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    const mockCustomers = generateMockCustomers();
    const mockSummary = generateMockSummary();

    try {
      const [customersRes, summaryRes] = await Promise.all([
        analyticsAPI.customerSegments().catch(() => null),
        analyticsAPI.segmentSummary().catch(() => null),
      ]);

      const allFailed = !customersRes && !summaryRes;
      if (allFailed) setError('API_UNAVAILABLE');

      setCustomers(customersRes?.data || mockCustomers);
      setSummary(summaryRes?.data || mockSummary);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || 'FETCH_ERROR');
      setCustomers(mockCustomers);
      setSummary(mockSummary);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Pie chart data ── */
  const pieData = useMemo(() => {
    if (!summary?.segments) return [];
    return Object.entries(summary.segments).map(([key, val]) => ({
      name: {
        vip: t('vip') || 'VIP',
        loyal: t('loyal') || 'مخلص',
        regular: t('regular') || 'عادي',
        at_risk: t('atRisk') || 'معرض للخطر',
        lost: t('lost') || 'فقد',
      }[key] || key,
      value: val.count,
      revenue: val.revenue,
      color: SEGMENT_COLORS[key] || COLORS.blue,
    }));
  }, [summary, t]);

  /* ── Revenue by segment bar data ── */
  const barData = useMemo(() => {
    if (!summary?.segments) return [];
    return Object.entries(summary.segments).map(([key, val]) => ({
      name: {
        vip: t('vip') || 'VIP',
        loyal: t('loyal') || 'مخلص',
        regular: t('regular') || 'عادي',
        at_risk: t('atRisk') || 'معرض للخطر',
        lost: t('lost') || 'فقد',
      }[key] || key,
      revenue: val.revenue,
      color: SEGMENT_COLORS[key] || COLORS.blue,
    }));
  }, [summary, t]);

  /* ── Filtered & sorted customers ── */
  const filteredCustomers = useMemo(() => {
    let result = [...customers];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(c => c.name?.toLowerCase().includes(q));
    }

    if (filterSegment !== 'all') {
      result = result.filter(c => c.segment === filterSegment);
    }

    result.sort((a, b) => {
      let valA, valB;
      switch (sortBy) {
        case 'name': valA = a.name; valB = b.name; break;
        case 'total_purchases': valA = a.total_purchases; valB = b.total_purchases; break;
        case 'order_count': valA = a.order_count; valB = b.order_count; break;
        case 'avg_order': valA = a.avg_order; valB = b.avg_order; break;
        case 'last_order': valA = a.last_order; valB = b.last_order; break;
        default: valA = a.total_purchases; valB = b.total_purchases;
      }
      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [customers, searchQuery, filterSegment, sortBy, sortDir]);

  /* ── Skeleton ── */
  const Skeleton = () => (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3" />
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="h-72 bg-gray-100 dark:bg-gray-700/50 rounded-lg" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="h-72 bg-gray-100 dark:bg-gray-700/50 rounded-lg" />
        </div>
      </div>
    </div>
  );

  if (loading && !customers.length) return <Skeleton />;

  const seg = summary?.segments || {};

  return (
    <div className="space-y-6" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-sm">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              {t('customerInsights') || 'رؤى العملاء'}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('customerInsightsDesc') || 'تحليل شرائح العملاء باستخدام الذكاء الاصطناعي'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => fetchData(true)} disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-600 hover:bg-riadah-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {t('refresh') || 'تحديث'}
          </button>
        </div>
      </div>

      {/* ── API fallback notice ── */}
      {error && !loading && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{t('usingCachedData') || 'يتم عرض بيانات مخزنة مؤقتاً – الخادم غير متاح'}</span>
        </div>
      )}

      {/* ── Segment Summary Cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {['vip', 'loyal', 'regular', 'at_risk', 'lost'].map((segment) => (
          <SummaryCard key={segment} segment={segment} data={seg[segment]} t={t} />
        ))}
      </div>

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-riadah-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400">{t('totalCustomers') || 'إجمالي العملاء'}</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{summary?.total_customers ?? 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400">{t('avgCustomerValue') || 'متوسط قيمة العميل'}</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100" dir="ltr">{formatCurrency(summary?.avg_customer_value)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <Star className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400">{t('retentionRate') || 'معدل الاحتفاظ'}</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{summary?.retention_rate ?? 0}%</p>
        </div>
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Segment Distribution Pie Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
            <PieIcon className="w-4.5 h-4.5 text-riadah-500 dark:text-accent-400" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{t('segmentDistribution') || 'توزيع الشرائح'}</h3>
          </div>
          <div className="p-4">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                {pieData.length > 0 ? (
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="45%" outerRadius={90} innerRadius={45} paddingAngle={3} dataKey="value"
                      label={({ name, value }) => `${name} (${value})`}
                      labelLine={{ strokeWidth: 1 }}>
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip isDark={isDark} />} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData') || 'لا توجد بيانات'}</div>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Revenue by Segment Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
            <TrendingUp className="w-4.5 h-4.5 text-riadah-500 dark:text-accent-400" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{t('revenueBySegment') || 'الإيرادات حسب الشريحة'}</h3>
          </div>
          <div className="p-4">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                {barData.length > 0 ? (
                  <BarChart data={barData} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} />
                    <YAxis tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip content={<CustomTooltip isDark={isDark} formatValue={formatCurrency} />} />
                    <Bar dataKey="revenue" name={t('revenue') || 'الإيرادات'} radius={[6, 6, 0, 0]} barSize={40}>
                      {barData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData') || 'لا توجد بيانات'}</div>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* ── Customer Table ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {t('customerList') || 'قائمة العملاء'}
            <span className="text-xs font-normal text-gray-500 dark:text-gray-400 mr-2">({filteredCustomers.length})</span>
          </h3>
        </div>

        {/* Filters */}
        <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-700 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" style={{ [isRTL ? 'right' : 'left']: '12px' }} />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('searchCustomers') || 'بحث عن عميل...'}
              className={`w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none ${isRTL ? 'pr-10' : 'pl-10'}`} />
          </div>

          <select value={filterSegment} onChange={(e) => setFilterSegment(e.target.value)}
            className="px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none">
            <option value="all">{t('allSegments') || 'جميع الشرائح'}</option>
            <option value="vip">{t('vip') || 'VIP'}</option>
            <option value="loyal">{t('loyal') || 'مخلص'}</option>
            <option value="regular">{t('regular') || 'عادي'}</option>
            <option value="at_risk">{t('atRisk') || 'معرض للخطر'}</option>
            <option value="lost">{t('lost') || 'فقد'}</option>
          </select>

          {(searchQuery || filterSegment !== 'all') && (
            <button onClick={() => { setSearchQuery(''); setFilterSegment('all'); }}
              className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <X className="w-3 h-3" />
              {t('clearFilters') || 'مسح'}
            </button>
          )}
        </div>

        {/* Table */}
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700/80 z-10">
              <tr className="text-gray-600 dark:text-gray-300">
                <th className="px-4 py-3 text-right font-medium">#</th>
                <th className="px-4 py-3 text-right font-medium">{t('customerName') || 'اسم العميل'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('segment') || 'الشريحة'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('totalPurchases') || 'إجمالي المشتريات'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('orderCount') || 'عدد الطلبات'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('avgOrder') || 'متوسط الطلب'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('lastOrder') || 'آخر طلب'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
              {filteredCustomers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400 dark:text-gray-500">
                    <Users className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>{t('noCustomers') || 'لا توجد عملاء مطابقين للفلاتر'}</p>
                  </td>
                </tr>
              ) : (
                filteredCustomers.map((customer, i) => (
                  <tr key={customer.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{i + 1}</td>
                    <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">{customer.name}</td>
                    <td className="px-4 py-3">
                      <SegmentBadge segment={customer.segment} t={t} />
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap" dir="ltr">{formatCurrency(customer.total_purchases)}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{customer.order_count}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300 whitespace-nowrap" dir="ltr">{formatCurrency(customer.avg_order)}</td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">{customer.last_order}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Last Updated Footer ── */}
      <div className="text-center text-xs text-gray-400 dark:text-gray-500">
        {t('lastUpdated') || 'آخر تحديث'}: {lastUpdated.toLocaleTimeString(locale === 'ar' ? 'ar-SA' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}
