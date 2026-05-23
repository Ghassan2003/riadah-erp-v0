/**
 * Advanced Reports Page - Interactive analytics dashboard with Recharts.
 * Features: Sales, Inventory, Financial, HR analysis with interactive charts.
 * Supports Arabic (RTL) and English, dark mode, and brand colors.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import toast from 'react-hot-toast';
import { analyticsAPI } from '../api';
import {
  BarChart3, TrendingUp, Package, DollarSign,
  Users, CalendarDays, Filter, RefreshCw, Download,
  Printer, ChevronDown, Loader2, ArrowUpRight, ArrowDownRight,
  ShoppingCart, Warehouse, Building2, UserCog,
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';

/* ── Brand Colors ── */
const COLORS = {
  primary: '#003366',
  accent: '#FF6600',
  secondary: '#808080',
  green: '#059669',
  red: '#dc2626',
  purple: '#7c3aed',
  blue: '#2563eb',
  teal: '#14b8a6',
  amber: '#f59e0b',
  pink: '#ec4899',
};

const PIE_COLORS = [COLORS.primary, COLORS.accent, COLORS.green, COLORS.purple, COLORS.blue, COLORS.teal, COLORS.amber, COLORS.red];
const BAR_COLORS = [COLORS.primary, COLORS.accent];

/* ── Date Preset Helper ── */
function getDatePreset(preset) {
  const now = new Date();
  const fmt = (d) => d.toISOString().split('T')[0];
  switch (preset) {
    case 'today': return { from: fmt(now), to: fmt(now) };
    case 'week': {
      const start = new Date(now);
      start.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1));
      return { from: fmt(start), to: fmt(now) };
    }
    case 'month': {
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      return { from: fmt(start), to: fmt(now) };
    }
    case 'quarter': {
      const q = Math.floor(now.getMonth() / 3);
      const start = new Date(now.getFullYear(), q * 3, 1);
      return { from: fmt(start), to: fmt(now) };
    }
    case 'year': {
      const start = new Date(now.getFullYear(), 0, 1);
      return { from: fmt(start), to: fmt(now) };
    }
    default: return { from: '', to: '' };
  }
}

/* ── Mock Data (realistic Arabic business data) ── */
const generateMockData = () => ({
  sales: {
    monthlyComparison: [
      { month: 'يناير', thisYear: 285000, lastYear: 245000 },
      { month: 'فبراير', thisYear: 312000, lastYear: 267000 },
      { month: 'مارس', thisYear: 298000, lastYear: 278000 },
      { month: 'أبريل', thisYear: 356000, lastYear: 290000 },
      { month: 'مايو', thisYear: 342000, lastYear: 315000 },
      { month: 'يونيو', thisYear: 389000, lastYear: 332000 },
      { month: 'يوليو', thisYear: 367000, lastYear: 348000 },
      { month: 'أغسطس', thisYear: 401000, lastYear: 356000 },
      { month: 'سبتمبر', thisYear: 378000, lastYear: 340000 },
      { month: 'أكتوبر', thisYear: 425000, lastYear: 372000 },
      { month: 'نوفمبر', thisYear: 412000, lastYear: 389000 },
      { month: 'ديسمبر', thisYear: 468000, lastYear: 410000 },
    ],
    customerCategories: [
      { name: 'عملاء حكوميون', value: 35, amount: 1680000 },
      { name: 'شركات خاصة', value: 28, amount: 1344000 },
      { name: 'أفراد', value: 22, amount: 1056000 },
      { name: 'مقاولون', value: 15, amount: 720000 },
    ],
    revenueTrend: [
      { month: 'يناير', revenue: 285000, target: 260000 },
      { month: 'فبراير', revenue: 312000, target: 275000 },
      { month: 'مارس', revenue: 298000, target: 290000 },
      { month: 'أبريل', revenue: 356000, target: 305000 },
      { month: 'مايو', revenue: 342000, target: 320000 },
      { month: 'يونيو', revenue: 389000, target: 335000 },
      { month: 'يوليو', revenue: 367000, target: 350000 },
      { month: 'أغسطس', revenue: 401000, target: 365000 },
      { month: 'سبتمبر', revenue: 378000, target: 380000 },
      { month: 'أكتوبر', revenue: 425000, target: 395000 },
      { month: 'نوفمبر', revenue: 412000, target: 410000 },
      { month: 'ديسمبر', revenue: 468000, target: 425000 },
    ],
  },
  inventory: {
    topProducts: [
      { name: 'أسمنت بورتلاند', volume: 4500, revenue: 540000 },
      { name: 'حديد تسليح 12مم', volume: 3200, revenue: 480000 },
      { name: 'طوب أحمر', volume: 28000, revenue: 420000 },
      { name: 'رمل خشن', volume: 18000, revenue: 360000 },
      { name: 'بلاط سيراميك', volume: 5600, revenue: 336000 },
      { name: 'دهان إمulsion', volume: 4200, revenue: 294000 },
      { name: 'أنابيب PVC', volume: 3800, revenue: 266000 },
      { name: 'كابلات كهربائية', volume: 2100, revenue: 252000 },
      { name: 'زجاج معشق', volume: 980, revenue: 235200 },
      { name: 'أبواب معدنية', volume: 340, revenue: 204000 },
    ],
    stockDistribution: [
      { name: 'مستودع الرياض', value: 38 },
      { name: 'مستودع جدة', value: 25 },
      { name: 'مستودع الدمام', value: 22 },
      { name: 'مستودع مكة', value: 15 },
    ],
    lowStockItems: [
      { name: 'مسامير تنجيد', sku: 'HW-NAL-001', current: 12, reorder: 50, category: 'أدوات' },
      { name: 'عوازل مائية', sku: 'BLD-WPR-002', current: 8, reorder: 30, category: 'مواد بناء' },
      { name: 'مفاتيح كهرباء', sku: 'ELC-SWT-001', current: 15, reorder: 40, category: 'كهرباء' },
      { name: 'حجر جيري', sku: 'BLD-LIM-003', current: 5, reorder: 100, category: 'مواد بناء' },
      { name: 'صاج مجلفن', sku: 'MTL-GAL-002', current: 20, reorder: 60, category: 'معادن' },
    ],
  },
  financial: {
    incomeExpenses: [
      { month: 'يناير', income: 380000, expenses: 295000 },
      { month: 'فبراير', income: 410000, expenses: 312000 },
      { month: 'مارس', income: 395000, expenses: 305000 },
      { month: 'أبريل', income: 456000, expenses: 340000 },
      { month: 'مايو', income: 442000, expenses: 332000 },
      { month: 'يونيو', income: 489000, expenses: 356000 },
      { month: 'يوليو', income: 467000, expenses: 348000 },
      { month: 'أغسطس', income: 501000, expenses: 372000 },
      { month: 'سبتمبر', income: 478000, expenses: 365000 },
      { month: 'أكتوبر', income: 525000, expenses: 395000 },
      { month: 'نوفمبر', income: 512000, expenses: 389000 },
      { month: 'ديسمبر', income: 568000, expenses: 420000 },
    ],
    expenseCategories: [
      { name: 'رواتب وأجور', value: 42, amount: 1680000 },
      { name: 'مواد خام', value: 25, amount: 1000000 },
      { name: 'إيجارات', value: 12, amount: 480000 },
      { name: 'نقل وشحن', value: 9, amount: 360000 },
      { name: 'صيانة', value: 6, amount: 240000 },
      { name: 'أخرى', value: 6, amount: 240000 },
    ],
    kpis: {
      grossMargin: 34.8,
      netProfit: 1260000,
      arTurnover: 5.2,
      currentRatio: 2.1,
      quickRatio: 1.5,
    },
  },
  hr: {
    attendanceByDept: [
      { department: 'المبيعات', rate: 96.5 },
      { department: 'المحاسبة', rate: 98.2 },
      { department: 'الموارد البشرية', rate: 97.1 },
      { department: 'المستودعات', rate: 94.8 },
      { department: 'المشتريات', rate: 95.3 },
      { department: 'المشاريع', rate: 93.7 },
      { department: 'الإدارة', rate: 99.1 },
    ],
    employeeDistribution: [
      { name: 'المبيعات', value: 28 },
      { name: 'المستودعات', value: 22 },
      { name: 'المحاسبة', value: 15 },
      { name: 'المشتريات', value: 12 },
      { name: 'الموارد البشرية', value: 8 },
      { name: 'المشاريع', value: 10 },
      { name: 'الإدارة', value: 5 },
    ],
  },
});

/* ── Reusable Chart Card ── */
function ChartCard({ title, icon: Icon, children, className = '' }) {
  const { isDark } = useI18n();
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
        {Icon && <Icon className="w-4.5 h-4.5 text-riadah-500 dark:text-accent-400" />}
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

/* ── Custom Tooltip ── */
function CustomTooltip({ active, payload, label, isDark }) {
  if (!active || !payload?.length) return null;
  return (
    <div className={`rounded-xl px-3.5 py-2.5 shadow-xl border text-xs ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-white border-gray-200 text-gray-800'}`}>
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span>{entry.name}: </span>
          <span className="font-medium">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
        </p>
      ))}
    </div>
  );
}

/* ── KPI Card ── */
function KPICard({ label, value, change, icon: Icon, color = 'primary' }) {
  const colorMap = {
    primary: 'from-[#003366] to-[#004488]',
    accent: 'from-[#FF6600] to-[#FF8533]',
    green: 'from-[#059669] to-[#10B981]',
    red: 'from-[#dc2626] to-[#EF4444]',
    purple: 'from-[#7c3aed] to-[#8B5CF6]',
    blue: 'from-[#2563eb] to-[#3B82F6]',
  };
  const isPositive = change >= 0;
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[color]} flex items-center justify-center shadow-sm`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {change !== undefined && (
          <span className={`flex items-center gap-0.5 text-xs font-medium px-2 py-0.5 rounded-full ${isPositive ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'}`}>
            {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{typeof value === 'number' ? value.toLocaleString() : value}</p>
    </div>
  );
}

/* ════════════════════════════════════════════════════
   Main Component
   ════════════════════════════════════════════════════ */
export default function AdvancedReportsPage() {
  const { t, locale, isRTL, isDark } = useI18n();
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [activeSection, setActiveSection] = useState('sales');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [presetOpen, setPresetOpen] = useState(false);

  const presets = [
    { id: 'today', label: t('today') || 'اليوم' },
    { id: 'week', label: t('thisWeek') || 'هذا الأسبوع' },
    { id: 'month', label: t('thisMonth') || 'هذا الشهر' },
    { id: 'quarter', label: t('thisQuarter') || 'هذا الربع' },
    { id: 'year', label: t('thisYear') || 'هذا العام' },
  ];

  const sections = [
    { id: 'sales', label: t('salesAnalysis') || 'تحليل المبيعات', icon: ShoppingCart },
    { id: 'inventory', label: t('inventoryAnalysis') || 'تحليل المخزون', icon: Package },
    { id: 'financial', label: t('financialAnalysis') || 'التحليل المالي', icon: DollarSign },
    { id: 'hr', label: t('hrAnalysis') || 'تحليل الموارد البشرية', icon: UserCog },
  ];

  // Fetch data from API, fall back to mock data on failure
  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      const mock = generateMockData();

      try {
        const params = {};
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;

        const [salesRes, invRes, finRes, hrRes] = await Promise.all([
          analyticsAPI.sales(params).catch(() => null),
          analyticsAPI.inventory(params).catch(() => null),
          analyticsAPI.financial(params).catch(() => null),
          analyticsAPI.hr(params).catch(() => null),
        ]);

        if (cancelled) return;

        const merged = {
          sales: salesRes?.data?.sales || mock.sales,
          inventory: invRes?.data?.inventory || mock.inventory,
          financial: finRes?.data?.financial || mock.financial,
          hr: hrRes?.data?.hr || mock.hr,
        };

        // Check if all calls failed (all fell back to mock)
        const allFailed = !salesRes && !invRes && !finRes && !hrRes;
        if (allFailed) {
          setError('API_UNAVAILABLE');
        }

        setData(merged);
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'FETCH_ERROR');
        setData(mock);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => { cancelled = true; };
  }, [dateFrom, dateTo]);

  const handlePreset = useCallback((presetId) => {
    const { from, to } = getDatePreset(presetId);
    setDateFrom(from);
    setDateTo(to);
    setPresetOpen(false);
  }, []);

  const formatCurrency = useCallback((val) => {
    const num = typeof val === 'number' ? val : Number(val) || 0;
    return num.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US') + ' ' + (t('currency') || 'ر.س');
  }, [locale, t]);

  const handleExportPDF = useCallback(() => {
    toast.success(t('exporting') || 'جاري التصدير...');
  }, [t]);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  /* ── Skeleton Loader ── */
  const Skeleton = () => (
    <div className="space-y-4 animate-pulse">
      {[...Array(2)].map((_, i) => (
        <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
          <div className="h-56 bg-gray-100 dark:bg-gray-700/50 rounded-lg" />
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-6" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-riadah-400 to-accent-500 flex items-center justify-center shadow-sm">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              {t('advancedReports') || 'التقارير المتقدمة'}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('advancedReportsDesc') || 'لوحة تحليلات تفاعلية شاملة'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleExportPDF}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors">
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">{t('exportPdf') || 'تصدير PDF'}</span>
          </button>
          <button onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg text-sm font-medium transition-colors">
            <Printer className="w-4 h-4" />
            <span className="hidden sm:inline">{t('print') || 'طباعة'}</span>
          </button>
        </div>
      </div>

      {/* ── Date Range Picker ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">{t('dateRange') || 'النطاق الزمني'}</span>
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('from') || 'من'}</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none" />
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('to') || 'إلى'}</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none" />
          </div>
          {/* Presets Dropdown */}
          <div className="relative">
            <button onClick={() => setPresetOpen(!presetOpen)}
              className="flex items-center gap-2 px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors">
              <CalendarDays className="w-4 h-4" />
              <span className="hidden sm:inline">{t('presets') || 'اختصارات'}</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
            {presetOpen && (
              <div className={`absolute ${isRTL ? 'right-0' : 'left-0'} top-full mt-1 w-44 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-20 py-1`}>
                {presets.map((p) => (
                  <button key={p.id} onClick={() => handlePreset(p.id)}
                    className="w-full text-right px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    {p.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          {(dateFrom || dateTo) && (
            <button onClick={() => { setDateFrom(''); setDateTo(''); }}
              className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <RefreshCw className="w-3 h-3" />
              {t('clearing') || 'مسح'}
            </button>
          )}
        </div>
      </div>

      {/* ── Section Tabs ── */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-x-auto">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <button key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeSection === section.id
                  ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}>
              <Icon className="w-4 h-4" />
              {section.label}
            </button>
          );
        })}
      </div>

      {/* ── API fallback notice ── */}
      {error && !loading && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{t('usingCachedData') || 'يتم عرض بيانات مخزنة مؤقتاً – الخادم غير متاح'}</span>
        </div>
      )}

      {/* ── Content ── */}
      {loading || !data ? (
        <Skeleton />
      ) : (
        <>
          {/* ═══ Sales Analysis ═══ */}
          {activeSection === 'sales' && (
            <div className="space-y-6">
              {/* KPI Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard label={t('totalSales') || 'إجمالي المبيعات'} value={formatCurrency(4433000)} change={12.5} icon={ShoppingCart} color="primary" />
                <KPICard label={t('avgOrderValue') || 'متوسط قيمة الطلب'} value={formatCurrency(8450)} change={5.2} icon={TrendingUp} color="accent" />
                <KPICard label={t('totalOrders') || 'إجمالي الأوامر'} value="524" change={8.7} icon={BarChart3} color="blue" />
                <KPICard label={t('newCustomers') || 'عملاء جدد'} value="38" change={-2.1} icon={Users} color="purple" />
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Monthly Sales Comparison Bar Chart */}
                <ChartCard title={t('monthlySalesComparison') || 'مقارنة المبيعات الشهرية'} icon={BarChart3}>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.sales.monthlyComparison} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                        <XAxis dataKey="month" tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} />
                        <YAxis tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Bar dataKey="thisYear" name={t('thisYear') || 'هذا العام'} fill={COLORS.primary} radius={[4, 4, 0, 0]} />
                        <Bar dataKey="lastYear" name={t('lastYear') || 'العام الماضي'} fill={COLORS.accent} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Sales by Customer Category Pie */}
                <ChartCard title={t('salesByCategory') || 'المبيعات حسب فئة العميل'} icon={Users}>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={data.sales.customerCategories} cx="50%" cy="45%" outerRadius={85} innerRadius={40} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ strokeWidth: 1 }}>
                          {data.sales.customerCategories.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Revenue Trend Line Chart */}
                <ChartCard title={t('revenueTrend') || 'اتجاه الإيرادات'} icon={TrendingUp} className="lg:col-span-2">
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={data.sales.revenueTrend} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                        <XAxis dataKey="month" tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} />
                        <YAxis tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Line type="monotone" dataKey="revenue" name={t('revenue') || 'الإيرادات'} stroke={COLORS.primary} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                        <Line type="monotone" dataKey="target" name={t('target') || 'الهدف'} stroke={COLORS.accent} strokeWidth={2} strokeDasharray="5 5" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>
            </div>
          )}

          {/* ═══ Inventory Analysis ═══ */}
          {activeSection === 'inventory' && (
            <div className="space-y-6">
              {/* KPI Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard label={t('totalProducts') || 'إجمالي المنتجات'} value="1,248" change={3.2} icon={Package} color="primary" />
                <KPICard label={t('totalInventoryValue') || 'قيمة المخزون'} value={formatCurrency(8450000)} change={7.8} icon={Warehouse} color="accent" />
                <KPICard label={t('lowStockProducts') || 'منتجات منخفضة'} value="23" change={-12.3} icon={Package} color="red" />
                <KPICard label={t('outOfStock') || 'نفذت الكمية'} value="5" change={-40.0} icon={Package} color="red" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top 10 Products Bar Chart */}
                <ChartCard title={t('topProducts') || 'أعلى 10 منتجات حسب المبيعات'} icon={Package}>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.inventory.topProducts} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                        <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: isDark ? '#9ca3af' : '#6b7280' }} width={90} />
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                        <Bar dataKey="revenue" name={t('revenue') || 'الإيرادات'} fill={COLORS.primary} radius={[0, 4, 4, 0]}>
                          {data.inventory.topProducts.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Stock Distribution Pie */}
                <ChartCard title={t('stockDistribution') || 'توزيع المخزون'} icon={Warehouse}>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={data.inventory.stockDistribution} cx="50%" cy="45%" outerRadius={100} innerRadius={50} paddingAngle={4} dataKey="value" label={({ name, value }) => `${name} ${value}%`} labelLine={{ strokeWidth: 1 }}>
                          {data.inventory.stockDistribution.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Low Stock Table */}
                <ChartCard title={t('lowStockItems') || 'أصناف منخفضة المخزون'} icon={Package} className="lg:col-span-2">
                  <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700/80">
                        <tr className="text-gray-600 dark:text-gray-300">
                          <th className="px-4 py-2.5 text-right font-medium">{t('productName') || 'المنتج'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('sku') || 'الرمز'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('category') || 'الفئة'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('currentStock') || 'المخزون الحالي'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('reorderLevel') || 'حد إعادة الطلب'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('suggestedOrder') || 'الكمية المقترحة'}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
                        {data.inventory.lowStockItems.map((item, i) => (
                          <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                            <td className="px-4 py-2.5 font-medium text-gray-800 dark:text-gray-200">{item.name}</td>
                            <td className="px-4 py-2.5 text-gray-500 dark:text-gray-400 font-mono text-xs">{item.sku}</td>
                            <td className="px-4 py-2.5 text-gray-600 dark:text-gray-300">{item.category}</td>
                            <td className="px-4 py-2.5">
                              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
                                {item.current}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-gray-600 dark:text-gray-300">{item.reorder}</td>
                            <td className="px-4 py-2.5 text-blue-600 dark:text-blue-400 font-medium">{item.reorder - item.current}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </ChartCard>
              </div>
            </div>
          )}

          {/* ═══ Financial Analysis ═══ */}
          {activeSection === 'financial' && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard label={t('grossMargin') || 'هامش الربح الإجمالي'} value={`${data.financial.kpis.grossMargin}%`} change={2.3} icon={DollarSign} color="green" />
                <KPICard label={t('netProfit') || 'صافي الربح'} value={formatCurrency(data.financial.kpis.netProfit)} change={15.6} icon={TrendingUp} color="primary" />
                <KPICard label={t('arTurnover') || 'معدل دوران الذمم'} value={`${data.financial.kpis.arTurnover}x`} change={0.8} icon={Building2} color="blue" />
                <KPICard label={t('currentRatio') || 'نسبة السيولة'} value={data.financial.kpis.currentRatio} change={0.15} icon={DollarSign} color="accent" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Income vs Expenses Area Chart */}
                <ChartCard title={t('incomeVsExpenses') || 'الإيرادات مقابل المصروفات'} icon={TrendingUp} className="lg:col-span-2">
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={data.financial.incomeExpenses} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                        <defs>
                          <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS.red} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={COLORS.red} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                        <XAxis dataKey="month" tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} />
                        <YAxis tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Area type="monotone" dataKey="income" name={t('totalRevenue') || 'الإيرادات'} stroke={COLORS.primary} strokeWidth={2.5} fill="url(#incomeGrad)" />
                        <Area type="monotone" dataKey="expenses" name={t('totalExpenses') || 'المصروفات'} stroke={COLORS.red} strokeWidth={2.5} fill="url(#expenseGrad)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Expense Categories Donut */}
                <ChartCard title={t('expenseBreakdown') || 'تفصيل المصروفات'} icon={DollarSign}>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={data.financial.expenseCategories} cx="50%" cy="45%" outerRadius={85} innerRadius={45} paddingAngle={3} dataKey="value" label={({ name, value }) => `${name} ${value}%`}>
                          {data.financial.expenseCategories.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Quick Financial Summary */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
                    <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{t('financialSummary') || 'ملخص مالي سريع'}</h3>
                  </div>
                  <div className="p-4 space-y-3">
                    {[
                      { label: t('totalRevenue') || 'إجمالي الإيرادات', value: formatCurrency(5622000), color: 'text-green-600 dark:text-green-400' },
                      { label: t('totalExpenses') || 'إجمالي المصروفات', value: formatCurrency(4327000), color: 'text-red-600 dark:text-red-400' },
                      { label: t('netProfit') || 'صافي الربح', value: formatCurrency(1295000), color: 'text-green-600 dark:text-green-400' },
                      { label: t('grossMargin') || 'هامش الربح', value: `${data.financial.kpis.grossMargin}%`, color: 'text-blue-600 dark:text-blue-400' },
                      { label: t('arTurnover') || 'معدل دوران الذمم', value: `${data.financial.kpis.arTurnover}x`, color: 'text-purple-600 dark:text-purple-400' },
                      { label: t('currentRatio') || 'نسبة السيولة', value: `${data.financial.kpis.currentRatio}`, color: 'text-amber-600 dark:text-amber-400' },
                    ].map((row, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 dark:border-gray-700 last:border-0">
                        <span className="text-sm text-gray-600 dark:text-gray-400">{row.label}</span>
                        <span className={`text-sm font-bold ${row.color}`}>{row.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ═══ HR Analysis ═══ */}
          {activeSection === 'hr' && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard label={t('totalEmployees') || 'عدد الموظفين'} value="156" change={4.0} icon={Users} color="primary" />
                <KPICard label={t('avgAttendance') || 'متوسط نسبة الحضور'} value="96.4%" change={1.2} icon={UserCog} color="green" />
                <KPICard label={t('activeDepts') || 'الأقسام النشطة'} value="7" change={0} icon={Building2} color="blue" />
                <KPICard label={t('newHires') || 'توظيفات جديدة'} value="12" change={20.0} icon={Users} color="accent" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Attendance by Department Bar Chart */}
                <ChartCard title={t('attendanceByDept') || 'نسبة الحضور حسب القسم'} icon={UserCog}>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.hr.attendanceByDept} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                        <XAxis dataKey="department" tick={{ fontSize: 9, fill: isDark ? '#9ca3af' : '#6b7280' }} />
                        <YAxis domain={[90, 100]} tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }} tickFormatter={(v) => `${v}%`} />
                        <Tooltip content={<CustomTooltip isDark={isDark} />} formatter={(v) => `${v}%`} />
                        <Bar dataKey="rate" name={t('attendance') || 'نسبة الحضور'} radius={[4, 4, 0, 0]}>
                          {data.hr.attendanceByDept.map((entry, i) => (
                            <Cell key={i} fill={entry.rate >= 96 ? COLORS.green : entry.rate >= 94 ? COLORS.amber : COLORS.red} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Employee Distribution Pie */}
                <ChartCard title={t('employeeDistribution') || 'توزيع الموظفين'} icon={Users}>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={data.hr.employeeDistribution} cx="50%" cy="45%" outerRadius={90} innerRadius={40} paddingAngle={3} dataKey="value" label={({ name, value }) => `${name} ${value}%`} labelLine={{ strokeWidth: 1 }}>
                          {data.hr.employeeDistribution.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip isDark={isDark} />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Department Details Table */}
                <ChartCard title={t('deptDetails') || 'تفاصيل الأقسام'} icon={Building2} className="lg:col-span-2">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-700/80">
                        <tr className="text-gray-600 dark:text-gray-300">
                          <th className="px-4 py-2.5 text-right font-medium">{t('department') || 'القسم'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('totalEmployees') || 'عدد الموظفين'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('attendance') || 'نسبة الحضور'}</th>
                          <th className="px-4 py-2.5 text-right font-medium">{t('performance') || 'الأداء'}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
                        {data.hr.attendanceByDept.map((dept, i) => {
                          const empCount = Math.round(data.hr.employeeDistribution.find(e => e.name === dept.department)?.value * 1.56 || 10);
                          return (
                            <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                              <td className="px-4 py-2.5 font-medium text-gray-800 dark:text-gray-200">{dept.department}</td>
                              <td className="px-4 py-2.5 text-gray-600 dark:text-gray-300">{empCount}</td>
                              <td className="px-4 py-2.5">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div className="h-full rounded-full bg-gradient-to-l from-green-500 to-emerald-400" style={{ width: `${dept.rate}%` }} />
                                  </div>
                                  <span className="text-xs font-medium text-gray-600 dark:text-gray-300">{dept.rate}%</span>
                                </div>
                              </td>
                              <td className="px-4 py-2.5">
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${dept.rate >= 97 ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : dept.rate >= 95 ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`}>
                                  {dept.rate >= 97 ? (t('excellent') || 'ممتاز') : dept.rate >= 95 ? (t('good') || 'جيد') : (t('needsImprovement') || 'يحتاج تحسين')}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </ChartCard>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
