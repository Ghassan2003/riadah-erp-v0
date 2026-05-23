/**
 * Sales Dashboard - Role-specific dashboard for the sales role.
 * Displays sales orders, revenue, CRM pipeline, invoicing, and notifications.
 * Uses Recharts library for professional interactive charts.
 * Supports dark mode and i18n (Arabic / English).
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { useNavigate } from 'react-router-dom';
import { salesAPI, dashboardAPI, invoicingAPI, crmAPI, notificationsAPI } from '../api';
import {
  ShoppingCart, DollarSign, Users, TrendingUp,
  AlertTriangle, Filter, RefreshCw, Check, Loader2,
  Receipt, Bell, ArrowUpRight, Clock, Package,
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

export default function SalesDashboard() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [salesStats, setSalesStats] = useState({});
  const [dashboardData, setDashboardData] = useState(null);
  const [invoicingStats, setInvoicingStats] = useState({});
  const [crmStats, setCrmStats] = useState({});
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

  const STATUS_COLORS = useMemo(() => ({
    pending:    { bg: 'bg-yellow-100 dark:bg-yellow-900/30',  text: 'text-yellow-700 dark:text-yellow-300',  label: t('onHold') },
    confirmed:  { bg: 'bg-riadah-100 dark:bg-riadah-900/30',     text: 'text-riadah-700 dark:text-accent-300',     label: t('confirmedOrders') },
    processing: { bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-700 dark:text-indigo-300', label: t('processing') },
    shipped:    { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', label: t('shipped') },
    delivered:  { bg: 'bg-green-100 dark:bg-green-900/30',   text: 'text-green-700 dark:text-green-300',   label: t('received') },
    cancelled:  { bg: 'bg-red-100 dark:bg-red-900/30',       text: 'text-red-700 dark:text-red-300',       label: t('cancel') },
  }), [t]);

  /* ── Fetch dashboard data ── */
  const fetchDashboard = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const [salesRes, dashRes, liveRes, invRes, crmRes, notifRes] = await Promise.all([
        salesAPI.getStats().catch(() => null),
        dashboardAPI.getStats(params).catch(() => null),
        dashboardAPI.liveStats().catch(() => null),
        invoicingAPI.getStats().catch(() => null),
        crmAPI.getStats().catch(() => null),
        notificationsAPI.list().catch(() => null),
      ]);
      if (salesRes) setSalesStats(salesRes.data || {});
      if (dashRes) setDashboardData(dashRes.data || {});
      if (liveRes) { setLiveData(liveRes.data); setLastUpdated(new Date()); }
      if (invRes) setInvoicingStats(invRes.data || {});
      if (crmRes) setCrmStats(crmRes.data || {});
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

  /* ── Prepare chart data ── */
  const salesChartData = useMemo(() => {
    const monthly = dashboardData?.sales?.monthly_sales || [];
    return monthly.map(d => ({
      name: d.month?.slice(5) || '',
      [t('sales')]: d.total || 0,
      [t('profit')]: d.profit || 0,
    }));
  }, [dashboardData, t]);

  const statusData = useMemo(() => {
    return (dashboardData?.sales?.status_distribution || []).map(s => {
      const info = STATUS_COLORS[s.status] || { label: s.status };
      return { name: info.label, value: s.count };
    }).filter(s => s.value > 0);
  }, [dashboardData, STATUS_COLORS]);

  const crmPipelineData = useMemo(() => {
    return [
      { name: t('activeLeads') || 'عملاء محتملون نشط', value: crmStats.active_leads || 0 },
      { name: t('wonDeals') || 'صفقات رابحة', value: crmStats.won_leads || 0 },
    ].filter(s => s.value > 0);
  }, [crmStats, t]);

  const invoicingStatusData = useMemo(() => {
    return [
      { name: t('paid') || 'مدفوعة', value: invoicingStats.total_paid || 0 },
      { name: t('unpaid') || 'غير مدفوعة', value: invoicingStats.total_unpaid || 0 },
      { name: t('overdue') || 'متأخرة', value: invoicingStats.total_overdue || 0 },
    ].filter(s => s.value > 0);
  }, [invoicingStats, t]);

  /* ── Loading state ── */
  if (loading && !dashboardData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-accent-500" />
        <p className="text-sm text-gray-500 dark:text-gray-400">{t('loading') || 'جاري التحميل...'}</p>
      </div>
    );
  }

  const ld = liveData || {};
  const ss = salesStats || {};
  const inv = invoicingStats || {};
  const crm = crmStats || {};

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

  const recentOrders = dashboardData?.sales?.recent_orders || [];

  const colorMap = {
    blue:    { bg: 'bg-riadah-50 dark:bg-riadah-900/20',    text: 'text-riadah-600 dark:text-riadah-400' },
    green:   { bg: 'bg-green-50 dark:bg-green-900/20',   text: 'text-green-600 dark:text-green-400' },
    yellow:  { bg: 'bg-yellow-50 dark:bg-yellow-900/20',  text: 'text-yellow-600 dark:text-yellow-400' },
    emerald: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400' },
    teal:    { bg: 'bg-teal-50 dark:bg-teal-900/20',     text: 'text-teal-600 dark:text-teal-400' },
    red:     { bg: 'bg-red-50 dark:bg-red-900/20',       text: 'text-red-600 dark:text-red-400' },
    violet:  { bg: 'bg-violet-50 dark:bg-violet-900/20',   text: 'text-violet-600 dark:text-violet-400' },
    cyan:    { bg: 'bg-cyan-50 dark:bg-cyan-900/20',     text: 'text-cyan-600 dark:text-cyan-400' },
  };

  /* ── KPI Cards ── */
  const kpiCards = [
    { title: t('totalProducts') || 'إجمالي الطلبات', value: ss.total_orders ?? 0, icon: ShoppingCart, color: 'blue', sub: `${ss.confirmed_orders ?? 0} ${t('confirmedOrders')}`, path: '/orders' },
    { title: t('totalSales') || 'إجمالي المبيعات', value: `${fmt(ss.total_sales)} ${cur}`, icon: DollarSign, color: 'green', sub: ss.this_month_sales > 0 ? `${t('thisMonth')}: ${fmt(ss.this_month_sales)} ${cur}` : '-', path: '/orders' },
    { title: t('confirmedOrders') || 'الطلبات المؤكدة', value: ss.confirmed_orders ?? 0, icon: Check, color: 'teal', sub: `${t('of')} ${ss.total_orders ?? 0} ${t('total')}`, path: '/orders' },
    { title: t('todaySales') || 'مبيعات اليوم', value: `${fmt(ss.today_sales)} ${cur}`, icon: TrendingUp, color: 'yellow', sub: t('today'), path: '/orders' },
    { title: t('unpaidInvoices') || 'فواتير غير مدفوعة', value: fmt(inv.total_unpaid || 0), icon: Receipt, color: 'red', sub: `${t('total')}: ${fmt(inv.total_invoices || 0)}`, path: '/invoices' },
    { title: t('activeLeads') || 'عملاء محتملون نشط', value: crm.active_leads ?? 0, icon: Users, color: 'violet', sub: `${t('pipeline')}: ${fmt(crm.total_pipeline_value || 0)} ${cur}`, path: '/crm/leads' },
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2.5">
              {t('salesDashboard') || 'لوحة تحكم المبيعات'}
              {/* Live indicator */}
              <span className="relative flex items-center justify-center" title={`${t('liveStats')} - ${t('lastUpdated')}: ${formatLastUpdated()}`}>
                <span className="absolute inline-flex h-2.5 w-2.5 rounded-full bg-green-400 opacity-75 animate-ping" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
              </span>
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {t('salesDashboard') || 'نظرة شاملة على المبيعات والإيرادات'}
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
            title: t('ordersToday') || 'طلبات اليوم',
            value: ld.orders_today ?? ss.total_orders ?? 0,
            icon: ShoppingCart,
            color: '#FF6600',
            sparkData: ld.sparkline_orders,
            sparkColor: '#FF6600',
            path: '/orders',
          },
          {
            title: t('revenueThisMonth') || 'إيرادات الشهر',
            value: `${fmt(ld.revenue_this_month ?? ss.this_month_sales ?? 0)} ${cur}`,
            icon: DollarSign,
            color: '#10b981',
            sparkData: ld.sparkline_orders,
            sparkColor: '#10b981',
            path: '/reports',
          },
          {
            title: t('pendingOrders') || 'طلبات معلقة',
            value: ss.pending_orders ?? ld.pending_orders ?? 0,
            icon: Clock,
            color: '#ef4444',
            sparkData: null,
            sparkColor: '#ef4444',
            path: '/orders',
          },
          {
            title: t('crmPipeline') || 'خط أنابيب المبيعات',
            value: `${fmt(crm.total_pipeline_value || 0)} ${cur}`,
            icon: TrendingUp,
            color: '#3b82f6',
            sparkData: null,
            sparkColor: '#3b82f6',
            path: '/crm/leads',
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
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
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
                {(i === 0) && (ss.pending_orders ?? 0) > 0 && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
                    {ss.pending_orders} ⚠
                  </span>
                )}
                {(i === 4) && (inv.total_overdue ?? 0) > 0 && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
                    {inv.total_overdue} !
                  </span>
                )}
              </div>
              <p className="text-base sm:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">{card.value}</p>
              <p className="text-[10px] sm:text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* ── Charts Row 1: Monthly Sales + Order Status ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Monthly Sales Area Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('monthlySales')}</h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {salesChartData.length > 0 ? (
                <AreaChart data={salesChartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="salesGradSD" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="profitGradSD" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Legend content={<CustomLegend isDark={isDark} />} />
                  <Area type="monotone" dataKey={t('sales')} stroke="#3b82f6" strokeWidth={2.5} fill="url(#salesGradSD)" dot={{ r: 3, fill: '#3b82f6' }} activeDot={{ r: 5, stroke: '#3b82f6', strokeWidth: 2 }} />
                  <Area type="monotone" dataKey={t('profit')} stroke="#10b981" strokeWidth={2} fill="url(#profitGradSD)" dot={{ r: 2.5, fill: '#10b981' }} />
                </AreaChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Order Status Distribution Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('orderStatusDist')}</h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {statusData.length > 0 ? (
                <BarChart data={statusData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
                    {statusData.map((entry, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Charts Row 2: CRM Pipeline + Invoicing Status ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* CRM Pipeline Donut */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('crmPipeline') || 'خط أنابيب المبيعات'}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {crmPipelineData.length > 0 ? (
                  <PieChart>
                    <Pie data={crmPipelineData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                      {crmPipelineData.map((entry, i) => (
                        <Cell key={i} fill={['#3b82f6', '#10b981'][i % 2]} stroke="none" />
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
                { label: t('activeLeads') || 'عملاء محتملون نشط', value: crm.active_leads || 0, color: '#3b82f6' },
                { label: t('wonDeals') || 'صفقات رابحة', value: crm.won_leads || 0, color: '#10b981' },
                { label: t('totalContacts') || 'إجمالي جهات الاتصال', value: crm.total_contacts || 0, color: '#8b5cf6' },
                { label: t('totalLeads') || 'إجمالي العملاء المحتملين', value: crm.total_leads || 0, color: '#f59e0b' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1 text-xs sm:text-sm">{item.label}</span>
                  <span className="text-gray-900 dark:text-gray-100 font-bold text-xs sm:text-sm" dir="ltr">{item.value}</span>
                </div>
              ))}
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t('pipeline') || 'خط الأنابيب'}</span>
                  <span className="font-bold text-sm text-gray-900 dark:text-gray-100" dir="ltr">{fmt(crm.total_pipeline_value || 0)} {cur}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Invoicing Status Donut */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('invoicingStatus') || 'حالة الفواتير'}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {invoicingStatusData.length > 0 ? (
                  <PieChart>
                    <Pie data={invoicingStatusData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                      {invoicingStatusData.map((entry, i) => (
                        <Cell key={i} fill={['#10b981', '#f59e0b', '#ef4444'][i % 3]} stroke="none" />
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
                { label: t('totalRevenue') || 'إجمالي الإيرادات', value: fmt(inv.total_revenue || 0), color: '#10b981' },
                { label: t('totalInvoices') || 'إجمالي الفواتير', value: inv.total_invoices || 0, color: '#3b82f6' },
                { label: t('unpaid') || 'غير مدفوعة', value: inv.total_unpaid || 0, color: '#f59e0b' },
                { label: t('overdue') || 'متأخرة', value: inv.total_overdue || 0, color: '#ef4444' },
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
          { label: t('totalRevenue') || 'إجمالي الإيرادات', value: inv.total_revenue || 0, color: 'green', icon: DollarSign },
          { label: t('unpaidInvoices') || 'فواتير غير مدفوعة', value: inv.total_unpaid || 0, color: 'red', icon: Receipt },
          { label: t('totalContacts') || 'جهات الاتصال', value: crm.total_contacts || 0, color: 'blue', icon: Users },
          { label: t('wonDeals') || 'صفقات رابحة', value: crm.won_leads || 0, color: 'emerald', icon: ArrowUpRight },
        ].map((item, i) => {
          const colorClasses = {
            green: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300',
            red: 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300',
            blue: 'bg-riadah-50 dark:bg-riadah-900/20 text-riadah-700 dark:text-riadah-300',
            emerald: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300',
          };
          return (
            <div key={i} className={`rounded-xl p-3 sm:p-4 border transition-all ${colorClasses[item.color]}`}>
              <div className="flex items-center gap-2 mb-1">
                <item.icon className="w-4 h-4" />
                <span className="text-xs font-medium">{item.label}</span>
              </div>
              <p className="text-lg sm:text-xl font-bold" dir="ltr">{i < 2 ? `${fmt(item.value)} ${cur}` : fmt(item.value)}</p>
            </div>
          );
        })}
      </div>

      {/* ── Bottom Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Orders */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">{t('recentOrders')}</h3>
            <button onClick={() => navigate('/orders')} className="text-xs text-accent-500 dark:text-accent-400 hover:text-accent-600 font-medium">{t('viewAll')}</button>
          </div>
          {recentOrders.length > 0 ? (
            <div className="divide-y divide-gray-50 dark:divide-gray-700/50 max-h-72 overflow-y-auto">
              {recentOrders.map((order, i) => {
                const sc = STATUS_COLORS[order.status] || STATUS_COLORS.pending;
                return (
                  <div key={i} className="px-4 py-2.5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{order.order_number}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{order.customer}{order.date && ` | ${order.date}`}</p>
                    </div>
                    <div className="text-left mr-3 flex-shrink-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{Number(order.total || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{sc.label}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400 dark:text-gray-500 text-sm">{t('noRecentOrders') || 'لا توجد طلبات حديثة'}</div>
          )}
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
            <div className="p-8 text-center text-gray-400 dark:text-gray-500 text-sm">{t('noNotifications') || 'لا توجد إشعارات'}</div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">{t('quickActions') || 'إجراءات سريعة'}</h3>
          </div>
          <div className="p-4 grid grid-cols-2 gap-2">
            {[
              { title: t('salesOrders') || 'أوامر البيع', icon: ShoppingCart, path: '/orders', color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' },
              { title: t('customers') || 'العملاء', icon: Users, path: '/customers', color: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' },
              { title: t('invoicing') || 'الفوترة', icon: Receipt, path: '/invoices', color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400' },
              { title: t('crm') || 'إدارة العملاء', icon: Users, path: '/crm/leads', color: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400' },
            ].map((action, i) => {
              const Icon = action.icon;
              return (
                <button key={i} onClick={() => navigate(action.path)}
                  className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all active:scale-[0.97] group">
                  <div className={`w-10 h-10 rounded-xl ${action.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{action.title}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
