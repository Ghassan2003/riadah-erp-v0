/**
 * Accountant Dashboard - Role-specific dashboard for the accountant role.
 * Uses Recharts library for professional interactive charts.
 * Supports dark mode and i18n (Arabic / English).
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { useNavigate } from 'react-router-dom';
import { accountingAPI, invoicingAPI, paymentsAPI, payrollAPI, dashboardAPI, notificationsAPI } from '../api';
import {
  DollarSign, TrendingUp, TrendingDown, Check, Wallet, Landmark,
  Activity, AlertTriangle, Clock, Filter, RefreshCw, Loader2,
  Bell, BellOff, BookOpen, FileText, Receipt, CreditCard,
  PieChart as PieIcon, BarChart3, Building2, ArrowUpRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend,
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6'];

/* ── Custom Tooltip ── */
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

/* ── Custom Legend ── */
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

export default function AccountantDashboard() {
  const { user } = useAuth();
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [liveData, setLiveData] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const isDark = document.documentElement.classList.contains('dark');

  const fmt = useCallback((val) =>
    Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }),
    [locale],
  );

  const cur = t('currency');

  /* ── Fetch dashboard data ── */
  const fetchDashboard = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const [accRes, invRes, payRes, prRes, dashRes, notifRes] = await Promise.all([
        accountingAPI.getStats().catch(() => null),
        invoicingAPI.getStats().catch(() => null),
        paymentsAPI.getStats().catch(() => null),
        payrollAPI.getStats().catch(() => null),
        dashboardAPI.getStats(params).catch(() => null),
        notificationsAPI.list().catch(() => null),
      ]);
      setData({
        accounting: accRes?.data || {},
        invoicing: invRes?.data || {},
        payments: payRes?.data || {},
        payroll: prRes?.data || {},
        dashboard: dashRes?.data || {},
      });
      if (notifRes) setNotifications(notifRes.data.results || []);
    } catch {
      toast.error(t('loadFailed'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateFrom, dateTo, t]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  /* ── Auto-refresh: fetch live stats every 60 seconds ── */
  const fetchLiveStats = useCallback(async () => {
    try {
      const res = await dashboardAPI.liveStats();
      setLiveData(res.data);
      setLastUpdated(new Date());
    } catch {
      // silent fail for background refresh
    }
  }, []);

  useEffect(() => {
    fetchLiveStats();
    const interval = setInterval(fetchLiveStats, 60000);
    return () => clearInterval(interval);
  }, [fetchLiveStats]);

  /* ── Loading state ── */
  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-accent-500" />
        <p className="text-sm text-gray-500 dark:text-gray-400">{t('loading') || 'جاري التحميل...'}</p>
      </div>
    );
  }

  const d = data || {};
  const ld = liveData || {};

  /* ── Sparkline component (inline SVG bars) ── */
  const Sparkline = ({ data: sparkData, color = '#3b82f6', height = 28 }) => {
    if (!sparkData || sparkData.length === 0) return null;
    const maxVal = Math.max(...sparkData.map(d => d.count), 1);
    const barWidth = Math.max(100 / sparkData.length, 8);
    return (
      <svg viewBox={`0 0 ${sparkData.length * (barWidth + 3)} ${height}`} className='w-full' style={{ height }} preserveAspectRatio='none'>
        {sparkData.map((item, i) => {
          const barH = Math.max((item.count / maxVal) * (height - 2), 2);
          return (
            <rect
              key={i}
              x={i * (barWidth + 3)}
              y={height - barH}
              width={barWidth}
              height={barH}
              rx={2}
              fill={color}
              opacity={0.4 + (item.count / maxVal) * 0.6}
            />
          );
        })}
      </svg>
    );
  };

  const formatLastUpdated = () => {
    return lastUpdated.toLocaleTimeString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  /* ── Prepare chart data ── */
  const incomeExpenseData = useMemo(() => {
    const monthly = d.dashboard?.accounting?.monthly || d.accounting?.monthly_income_expense || [];
    if (monthly.length > 0) {
      return monthly.map(m => ({
        name: m.month?.slice(5) || m.name || '',
        [t('income')]: m.income || m.total_income || 0,
        [t('expenses')]: m.expenses || m.total_expenses || 0,
      }));
    }
    return [
      { name: t('income'), [t('income')]: d.accounting?.total_income || 0, [t('expenses')]: 0 },
      { name: t('expenses'), [t('income')]: 0, [t('expenses')]: d.accounting?.total_expenses || 0 },
    ];
  }, [d, t]);

  const revenueDistributionData = useMemo(() => [
    { name: t('income'), value: parseFloat(d.accounting?.total_income || 0) },
    { name: t('expenses'), value: parseFloat(d.accounting?.total_expenses || 0) },
    { name: t('netProfit'), value: Math.abs(parseFloat(d.accounting?.net_profit || 0)) },
  ].filter(s => s.value > 0), [d, t]);

  const invoiceStatusData = useMemo(() => {
    const items = [
      { name: t('paid') || 'مدفوعة', value: d.invoicing?.total_paid || 0 },
      { name: t('unpaid') || 'غير مدفوعة', value: d.invoicing?.total_unpaid || 0 },
      { name: t('overdue') || 'متأخرة', value: d.invoicing?.total_overdue || 0 },
    ].filter(s => s.value > 0);
    return items;
  }, [d, t]);

  const paymentDistributionData = useMemo(() => {
    const balance = parseFloat(d.payments?.total_balance || 0);
    const received = parseFloat(d.payments?.monthly_receipts_total || 0);
    const paid = parseFloat(d.payments?.monthly_payments_total || 0);
    return [
      { name: t('totalBalance') || 'الرصيد', value: balance },
      { name: t('receipts') || 'المقبوضات', value: received },
      { name: t('payments') || 'المدفوعات', value: paid },
    ].filter(s => s.value > 0);
  }, [d, t]);

  /* ── colorMap ── */
  const colorMap = {
    blue:    { bg: 'bg-riadah-50 dark:bg-riadah-900/20',    text: 'text-riadah-600 dark:text-riadah-400' },
    green:   { bg: 'bg-green-50 dark:bg-green-900/20',   text: 'text-green-600 dark:text-green-400' },
    yellow:  { bg: 'bg-yellow-50 dark:bg-yellow-900/20',  text: 'text-yellow-600 dark:text-yellow-400' },
    emerald: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400' },
    indigo:  { bg: 'bg-indigo-50 dark:bg-indigo-900/20',  text: 'text-indigo-600 dark:text-indigo-400' },
    cyan:    { bg: 'bg-cyan-50 dark:bg-cyan-900/20',     text: 'text-cyan-600 dark:text-cyan-400' },
    teal:    { bg: 'bg-teal-50 dark:bg-teal-900/20',     text: 'text-teal-600 dark:text-teal-400' },
    red:     { bg: 'bg-red-50 dark:bg-red-900/20',       text: 'text-red-600 dark:text-red-400' },
    violet:  { bg: 'bg-violet-50 dark:bg-violet-900/20',   text: 'text-violet-600 dark:text-violet-400' },
    purple:  { bg: 'bg-purple-50 dark:bg-purple-900/20',   text: 'text-purple-600 dark:text-purple-400' },
    rose:    { bg: 'bg-rose-50 dark:bg-rose-900/20',      text: 'text-rose-600 dark:text-rose-400' },
    amber:   { bg: 'bg-amber-50 dark:bg-amber-900/20',    text: 'text-amber-600 dark:text-amber-400' },
  };

  /* ── KPI Cards ── */
  const kpiCards = [
    { title: t('totalRevenue') || 'إجمالي الإيرادات', value: `${fmt(d.accounting?.total_income)} ${cur}`, icon: TrendingUp, color: 'green', sub: `${t('activeAccounts') || 'حسابات نشطة'}: ${d.accounting?.active_accounts ?? 0}`, path: '/accounts' },
    { title: t('totalExpenses') || 'إجمالي المصروفات', value: `${fmt(d.accounting?.total_expenses)} ${cur}`, icon: TrendingDown, color: 'red', sub: `${d.accounting?.posted_entries ?? 0} ${t('postedEntries') || 'قيود مرحلة'}`, path: '/reports' },
    { title: t('netProfit') || 'صافي الربح', value: `${fmt(d.accounting?.net_profit)} ${cur}`, icon: DollarSign, color: d.accounting?.net_profit >= 0 ? 'blue' : 'red', sub: d.accounting?.net_profit >= 0 ? '↑' : '↓', path: '/reports' },
    { title: t('totalPaid') || 'إجمالي المدفوع', value: `${fmt(d.invoicing?.total_paid)} ${cur}`, icon: Check, color: 'teal', sub: `${d.invoicing?.total_invoices ?? 0} ${t('totalInvoices') || 'فواتير'}`, path: '/invoices' },
    { title: t('payrollThisMonth') || 'رواتب الشهر', value: `${fmt(d.payroll?.total_paid_this_month)} ${cur}`, icon: Wallet, color: 'indigo', sub: `${d.payroll?.total_pending_records ?? 0} ${t('pending') || 'معلقة'}`, path: '/payroll' },
  ];

  const quickActions = [
    { title: t('chartOfAccounts') || 'الدليل المحاسبي', icon: BookOpen, path: '/accounts' },
    { title: t('journalEntries') || 'القيود اليومية', icon: FileText, path: '/journal-entries' },
    { title: t('financialReports') || 'التقارير المالية', icon: BarChart3, path: '/reports' },
    { title: t('payments') || 'المدفوعات', icon: CreditCard, path: '/payments' },
    { title: t('invoicing') || 'الفوترة', icon: Receipt, path: '/invoices' },
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2.5">
              {t('accountingDashboard') || 'لوحة تحكم المحاسبة'}
              {/* Live indicator */}
              <span className="relative flex items-center justify-center" title={`${t('liveStats')} - ${t('lastUpdated')}: ${formatLastUpdated()}`}>
                <span className="absolute inline-flex h-2.5 w-2.5 rounded-full bg-green-400 opacity-75 animate-ping" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
              </span>
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {t('accountingOverview') || 'نظرة عامة على المحاسبة والمالية'}
              <span className="mx-1.5 text-gray-300 dark:text-gray-600">•</span>
              <span className="text-xs">{t('lastUpdated')}: {formatLastUpdated()}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => fetchDashboard(true)} disabled={refreshing}
            className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <div className="flex items-center gap-1.5 bg-gray-50 dark:bg-gray-800 rounded-lg p-1">
            <Filter className="w-3.5 h-3.5 text-gray-400 mx-1" />
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
              className="px-2 py-1.5 border-0 bg-transparent dark:text-white rounded-md text-xs focus:ring-0" />
            <span className="text-gray-400 text-xs">-</span>
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
              className="px-2 py-1.5 border-0 bg-transparent dark:text-white rounded-md text-xs focus:ring-0" />
            {(dateFrom || dateTo) && (
              <button onClick={() => { setDateFrom(''); setDateTo(''); }}
                className="text-xs text-accent-500 dark:text-accent-400 hover:underline px-1">{t('clearing')}</button>
            )}
          </div>
        </div>
      </div>

      {/* ── Quick Stats Row (Live) ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[
          {
            title: t('revenueThisMonth') || 'إيرادات الشهر',
            value: `${fmt(ld.revenue_this_month ?? d.accounting?.total_income ?? 0)} ${cur}`,
            icon: TrendingUp,
            color: '#10b981',
            sparkData: ld.sparkline_orders,
            sparkColor: '#10b981',
            path: '/reports',
          },
          {
            title: t('totalExpenses') || 'إجمالي المصروفات',
            value: `${fmt(d.accounting?.total_expenses ?? 0)} ${cur}`,
            icon: TrendingDown,
            color: '#ef4444',
            sparkData: null,
            sparkColor: '#ef4444',
            path: '/reports',
          },
          {
            title: t('unpaidInvoices') || 'فواتير غير مدفوعة',
            value: d.invoicing?.total_unpaid ?? 0,
            icon: AlertTriangle,
            color: '#f59e0b',
            sparkData: null,
            sparkColor: '#f59e0b',
            path: '/invoices',
          },
          {
            title: t('pendingTransactions') || 'معاملات معلقة',
            value: d.payments?.pending_transactions ?? 0,
            icon: Clock,
            color: '#3b82f6',
            sparkData: null,
            sparkColor: '#3b82f6',
            path: '/payments',
          },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} onClick={() => navigate(card.path)}
              className="bg-white dark:bg-gray-800 rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md cursor-pointer transition-all active:scale-[0.98] group">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${card.color}15` }}
                  >
                    <Icon className="w-4 h-4 sm:w-4.5 sm:h-4.5" style={{ color: card.color }} />
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-gray-500 dark:text-gray-400">{card.title}</span>
                </div>
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                  style={{ backgroundColor: `${card.color}15`, color: card.color }}
                >
                  {t('liveStats')}
                </span>
              </div>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-gray-100 truncate">{card.value}</p>
              {card.sparkData && (
                <div className="mt-2 opacity-60 group-hover:opacity-100 transition-opacity">
                  <Sparkline data={card.sparkData} color={card.sparkColor} height={24} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {kpiCards.map((card, i) => {
          const Icon = card.icon;
          const c = colorMap[card.color] || colorMap.blue;
          return (
            <div key={i} onClick={() => navigate(card.path)}
              className="bg-white dark:bg-gray-800 rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md cursor-pointer transition-all active:scale-[0.98]">
              <div className="flex items-center justify-between mb-2">
                <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${c.text}`} />
                </div>
                {i === 2 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${d.accounting?.net_profit >= 0 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
                    {d.accounting?.net_profit >= 0 ? '↑' : '↓'}
                  </span>
                )}
              </div>
              <p className="text-base sm:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">{card.value}</p>
              <p className="text-[10px] sm:text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* ── Charts Row 1: Income vs Expenses + Revenue Distribution ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Income vs Expenses Area Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('incomeVsExpenses') || 'الإيرادات مقابل المصروفات'}</h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {incomeExpenseData.length > 0 ? (
                <AreaChart data={incomeExpenseData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="accIncomeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="accExpenseGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Legend content={<CustomLegend isDark={isDark} />} />
                  <Area type="monotone" dataKey={t('income')} stroke="#10b981" strokeWidth={2.5} fill="url(#accIncomeGrad)" dot={{ r: 3, fill: '#10b981' }} activeDot={{ r: 5, stroke: '#10b981', strokeWidth: 2 }} />
                  <Area type="monotone" dataKey={t('expenses')} stroke="#ef4444" strokeWidth={2} fill="url(#accExpenseGrad)" dot={{ r: 2.5, fill: '#ef4444' }} />
                </AreaChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Revenue Distribution Donut Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('revenueDistribution') || 'توزيع الإيرادات'}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {revenueDistributionData.length > 0 ? (
                  <PieChart>
                    <Pie data={revenueDistributionData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                      {revenueDistributionData.map((entry, i) => (
                        <Cell key={i} fill={['#10b981', '#ef4444', '#3b82f6'][i % 3]} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  </PieChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
                )}
              </ResponsiveContainer>
            </div>
            <div className="space-y-3 text-sm flex-1 min-w-0">
              {revenueDistributionData.map((entry, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: ['#10b981', '#ef4444', '#3b82f6'][i % 3] }} />
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1 text-xs sm:text-sm">{entry.name}</span>
                  <span className="text-gray-900 dark:text-gray-100 font-bold text-xs sm:text-sm" dir="ltr">{fmt(Math.round(entry.value))}</span>
                </div>
              ))}
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t('total')}</span>
                  <span className="font-bold text-sm text-gray-900 dark:text-gray-100" dir="ltr">{fmt(Math.round(revenueDistributionData.reduce((s, dd) => s + dd.value, 0)))}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Charts Row 2: Invoice Status + Budget Utilization ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Invoice Status Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('invoiceStatusDist') || 'توزيع حالة الفواتير'}</h3>
          <div className="h-52 sm:h-56">
            <ResponsiveContainer width="100%" height="100%">
              {invoiceStatusData.length > 0 ? (
                <BarChart data={invoiceStatusData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
                    <Cell fill="#10b981" />
                    <Cell fill="#f59e0b" />
                    <Cell fill="#ef4444" />
                  </Bar>
                </BarChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Payment Distribution Donut Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('paymentDistribution') || 'توزيع المدفوعات'}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {paymentDistributionData.length > 0 ? (
                  <PieChart>
                    <Pie data={paymentDistributionData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                      {paymentDistributionData.map((entry, i) => (
                        <Cell key={i} fill={['#3b82f6', '#10b981', '#f59e0b'][i % 3]} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  </PieChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
                )}
              </ResponsiveContainer>
            </div>
            <div className="space-y-3 text-sm flex-1 min-w-0">
              {[
                { label: t('totalBalance') || 'إجمالي الرصيد', value: fmt(d.payments?.total_balance || 0), color: '#3b82f6' },
                { label: t('monthlyReceipts') || 'إيصالات الشهر', value: fmt(d.payments?.monthly_receipts_total || 0), color: '#10b981' },
                { label: t('monthlyPayments') || 'مدفوعات الشهر', value: fmt(d.payments?.monthly_payments_total || 0), color: '#f59e0b' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1 text-xs sm:text-sm">{item.label}</span>
                  <span className="text-gray-900 dark:text-gray-100 font-bold text-xs sm:text-sm" dir="ltr">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Quick Summary Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[
          { label: t('totalBalance') || 'إجمالي الرصيد', value: d.payments?.total_balance || 0, color: 'purple', icon: CreditCard },
          { label: t('monthlyReceipts') || 'إيصالات الشهر', value: d.payments?.monthly_receipts_total || 0, color: 'green', icon: TrendingUp },
          { label: t('monthlyPayments') || 'مدفوعات الشهر', value: d.payments?.monthly_payments_total || 0, color: 'red', icon: TrendingDown },
          { label: t('totalInvoices') || 'إجمالي الفواتير', value: d.invoicing?.total_invoices || 0, color: 'blue', icon: Receipt },
        ].map((item, i) => {
          const colorClasses = {
            purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300',
            green: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300',
            red: 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300',
            blue: 'bg-riadah-50 dark:bg-riadah-900/20 text-riadah-700 dark:text-riadah-300',
          };
          return (
            <div key={i} className={`rounded-xl p-3 sm:p-4 border transition-all ${colorClasses[item.color]}`}>
              <div className="flex items-center gap-2 mb-1">
                <item.icon className="w-4 h-4" />
                <span className="text-xs font-medium">{item.label}</span>
              </div>
              <p className="text-lg sm:text-xl font-bold" dir="ltr">{fmt(item.value)} {cur}</p>
            </div>
          );
        })}
      </div>

      {/* ── Bottom Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Pending Journal Entries */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">{t('pendingEntries') || 'قيود يومية معلقة'}</h3>
            <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-medium px-2 py-0.5 rounded-full">
              {d.accounting?.pending_entries ?? 0}
            </span>
          </div>
          <div className="p-6 text-center">
            <div className="flex items-center justify-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="text-left">
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{d.accounting?.pending_entries ?? 0}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('pending') || 'معلقة'}</p>
              </div>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
              <span>{t('postedEntries') || 'مرحلة'}: <strong className="text-gray-700 dark:text-gray-300">{d.accounting?.posted_entries ?? 0}</strong></span>
              <span>{t('totalEntries') || 'إجمالي'}: <strong className="text-gray-700 dark:text-gray-300">{d.accounting?.total_journal_entries ?? 0}</strong></span>
            </div>
            <button onClick={() => navigate('/journal-entries')}
              className="text-xs text-accent-500 dark:text-accent-400 hover:text-accent-600 font-medium flex items-center gap-1 mx-auto">
              {t('viewAll')} <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm flex items-center gap-1.5">
              <Bell className="w-4 h-4 text-gray-500 dark:text-gray-400" /> {t('notifications')}
            </h3>
            {notifications.filter(n => !n.is_read).length > 0 && (
              <span className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs font-medium px-2 py-0.5 rounded-full">
                {notifications.filter(n => !n.is_read).length} {t('newNotifications')}
              </span>
            )}
          </div>
          {notifications.length > 0 ? (
            <div className="divide-y divide-gray-50 dark:divide-gray-700/50 max-h-72 overflow-y-auto">
              {notifications.slice(0, 8).map((notif, i) => (
                <div key={notif.id || i} className={`px-4 py-2.5 transition-colors ${!notif.is_read ? 'bg-riadah-50/30 dark:bg-riadah-900/10' : ''}`}>
                  <p className={`text-sm ${notif.is_read ? 'text-gray-600 dark:text-gray-400' : 'font-medium text-gray-900 dark:text-gray-100'}`}>
                    {notif.title || notif.message || t('notifications')}
                  </p>
                  <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{notif.created_at}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <BellOff className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-400 dark:text-gray-500">{t('noNotifications')}</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm mb-3">{t('quickAccess')}</h3>
          <div className="grid grid-cols-2 gap-2">
            {quickActions.map((action, i) => {
              const Icon = action.icon;
              return (
                <button key={i} onClick={() => navigate(action.path)}
                  className="flex items-center gap-2 p-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:text-accent-500 dark:hover:text-accent-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all text-xs font-medium active:scale-95">
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate">{action.title}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Footer ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-3 flex-wrap">
          <span>{t('erpSystem')} v5.0</span>
          <span className="hidden sm:inline">{t('user')}: {user?.username}</span>
          <span className="hidden sm:inline">{t('status')}: {user?.role_display}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-green-600 dark:text-green-400">{t('systemOnline')}</span>
        </div>
      </div>
    </div>
  );
}
