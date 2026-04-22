/**
 * Dashboard - Interactive with Recharts charts, date filtering, and stats.
 * Uses Recharts library for professional interactive charts.
 * Supports dark mode and i18n (Arabic / English).
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { useNavigate } from 'react-router-dom';
import { dashboardAPI, notificationsAPI, warehouseAPI, assetsAPI, contractsAPI, paymentsAPI, payrollAPI, invoicingAPI } from '../api';
import {
  Shield, User, Package, ShoppingCart, DollarSign, Users,
  Activity, AlertTriangle, TrendingUp, TrendingDown,
  BookOpen, FileText, UserCog, PieChart as PieIcon, BarChart3,
  Bell, BellOff, Truck, FolderKanban, Check, Loader2,
  ArrowUpRight, ArrowDownRight, Minus, Filter, RefreshCw,
  Building2, Landmark, FileSignature, CreditCard, Warehouse as WarehouseIcon, Calendar, Receipt, Wallet,
  Clock, Plus, Edit, Trash2, LogIn, LogOut, Download, Upload,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, ComposedChart, Line,
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

export default function DashboardPage() {
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
      const [statsRes, notifRes, whRes, astRes, conRes, payRes, prRes, invRes] = await Promise.all([
        dashboardAPI.getStats(params),
        notificationsAPI.list().catch(() => null),
        warehouseAPI.getStats().catch(() => null),
        assetsAPI.getStats().catch(() => null),
        contractsAPI.getStats().catch(() => null),
        paymentsAPI.getStats().catch(() => null),
        payrollAPI.getStats().catch(() => null),
        invoicingAPI.getStats().catch(() => null),
      ]);
      setData(prev => ({
        ...statsRes.data,
        warehouse: whRes?.data || {},
        assets: astRes?.data || {},
        contracts: conRes?.data || {},
        payments: payRes?.data || {},
        payroll: prRes?.data || {},
        invoicing: invRes?.data || {},
      }));
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
  const salesData = useMemo(() => {
    const monthly = data?.sales?.monthly_sales || [];
    return monthly.map(d => ({
      name: d.month?.slice(5) || '',
      [t('sales')]: d.total || 0,
      [t('profit')]: d.profit || 0,
    }));
  }, [data, t]);

  const purchaseData = useMemo(() => {
    const monthly = data?.purchases?.monthly_purchases || [];
    return monthly.map(d => ({
      name: d.month?.slice(5) || '',
      [t('purchases')]: d.total || 0,
    }));
  }, [data, t]);

  const statusData = useMemo(() => {
    return (data?.sales?.status_distribution || []).map(s => {
      const info = STATUS_COLORS[s.status] || { label: s.status };
      return { name: info.label, value: s.count };
    }).filter(s => s.value > 0);
  }, [data, STATUS_COLORS]);

  const revenueData = useMemo(() => [
    { name: t('revenue'), value: parseFloat(data?.accounting?.total_revenue || 0) },
    { name: t('expenses'), value: parseFloat(data?.accounting?.total_expenses || 0) },
    { name: t('netProfit'), value: Math.abs(parseFloat(data?.accounting?.net_profit || 0)) },
  ].filter(s => s.value > 0), [data, t]);

  const expenseCategories = useMemo(() => {
    const expenses = data?.accounting?.expense_categories || [];
    return expenses.map(e => ({
      name: e.category || e.name || t('other'),
      value: e.total || e.amount || 0,
    }));
  }, [data, t]);

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

  /* ── Activity icon mapper ── */
  const activityIcon = (action) => {
    const map = {
      create: Plus,
      update: Edit,
      delete: Trash2,
      soft_delete: Trash2,
      restore: RefreshCw,
      status_change: Activity,
      login: LogIn,
      logout: LogOut,
      export: Download,
      import: Upload,
    };
    return map[action] || Activity;
  };

  const activityColor = (action) => {
    const map = {
      create: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
      update: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
      delete: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
      soft_delete: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
      restore: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
      status_change: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
      login: 'bg-riadah-100 text-riadah-600 dark:bg-riadah-900/30 dark:text-riadah-400',
      logout: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
      export: 'bg-teal-100 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400',
      import: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/30 dark:text-cyan-400',
    };
    return map[action] || 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
  };

  const formatTime = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString(locale === 'ar' ? 'ar-SA' : 'en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  const formatLastUpdated = () => {
    return lastUpdated.toLocaleTimeString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  /* ── KPI Cards ── */
  const kpiCards = [
    { title: t('totalProducts'), value: d.inventory?.total_products ?? 0, icon: Package, color: 'blue', sub: `${d.inventory?.low_stock ?? 0} ${t('lowStockItems')}`, path: '/products' },
    { title: t('salesOrders'), value: d.sales?.total_orders ?? 0, icon: ShoppingCart, color: 'green', sub: `${d.sales?.confirmed_orders ?? 0} ${t('confirmedOrders')}`, path: '/orders' },
    { title: t('totalSales'), value: `${fmt(d.sales?.total_sales)} ${cur}`, icon: DollarSign, color: 'yellow', sub: d.sales?.total_sales > 0 ? t('ordersTotal') : '-', path: '/orders' },
    { title: t('netProfit'), value: `${fmt(d.accounting?.net_profit)} ${cur}`, icon: d.accounting?.net_profit >= 0 ? TrendingUp : TrendingDown, color: d.accounting?.net_profit >= 0 ? 'emerald' : 'red', sub: `${fmt(d.accounting?.total_revenue)} ${t('totalRevenue')}`, path: '/reports' },
    { title: t('totalEmployees'), value: d.hr?.total_employees ?? 0, icon: Users, color: 'indigo', sub: `${t('totalSalaries')}: ${fmt(d.hr?.total_salary)} ${cur}`, path: '/employees' },
    { title: t('activeProjects'), value: d.projects?.active_projects ?? 0, icon: FolderKanban, color: 'cyan', sub: `${t('of')} ${d.projects?.total_projects ?? 0} ${t('total')}`, path: '/projects' },
    { title: t('purchases'), value: `${fmt(d.purchases?.total_purchases)} ${cur}`, icon: Truck, color: 'teal', sub: t('ordersTotal'), path: '/purchases' },
    { title: t('totalExpenses'), value: `${fmt(d.accounting?.total_expenses)} ${cur}`, icon: TrendingDown, color: 'red', sub: t('totalExpenses'), path: '/reports' },
    { title: t('warehouses'), value: d.warehouse?.total_warehouses ?? 0, icon: Building2, color: 'violet', sub: `${d.warehouse?.low_stock_items ?? 0} ${t('lowStockItems')}`, path: '/warehouse' },
    { title: t('totalAssets'), value: d.assets?.total_assets ?? 0, icon: Landmark, color: 'purple', sub: `${t('active')}: ${d.assets?.active_assets ?? 0}`, path: '/assets' },
    { title: t('activeContracts'), value: d.contracts?.active_contracts ?? 0, icon: FileSignature, color: 'rose', sub: `${t('totalValue')}: ${fmt(d.contracts?.total_value)} ${cur}`, path: '/contracts' },
    { title: t('pendingPayments'), value: d.payments?.pending_transactions ?? 0, icon: CreditCard, color: 'amber', sub: `${t('totalBalance')}: ${fmt(d.payments?.total_balance)} ${cur}`, path: '/payments' },
  ];

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

  const quickActions = [
    { title: t('products'), icon: Package, path: '/products' },
    { title: t('salesOrders'), icon: ShoppingCart, path: '/orders' },
    { title: t('customers'), icon: Users, path: '/customers' },
    { title: t('purchases'), icon: Truck, path: '/purchases' },
    { title: t('documents'), icon: FileText, path: '/documents' },
    { title: t('projects'), icon: FolderKanban, path: '/projects' },
    { title: t('reportsCenter'), icon: BarChart3, path: '/reports-center' },
    { title: t('chartOfAccounts'), icon: BookOpen, path: '/accounts', roles: ['admin', 'accountant'] },
    { title: t('financialReports'), icon: DollarSign, path: '/reports', roles: ['admin', 'accountant'] },
    { title: t('employees'), icon: UserCog, path: '/employees', roles: ['admin'] },
  ];
  const filteredActions = quickActions.filter(a => !a.roles || a.roles.includes(user?.role));
  const recentOrders = d.sales?.recent_orders || [];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2.5">
              {t('dashboard')}
              {/* Live indicator */}
              <span className="relative flex items-center justify-center" title={`${t('liveStats')} - ${t('lastUpdated')}: ${formatLastUpdated()}`}>
                <span className="absolute inline-flex h-2.5 w-2.5 rounded-full bg-green-400 opacity-75 animate-ping" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
              </span>
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {t('dashboardWelcome')}
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
            title: t('ordersToday'),
            value: ld.orders_today ?? d.sales?.total_orders ?? 0,
            icon: ShoppingCart,
            color: '#FF6600',
            sparkData: ld.sparkline_orders,
            sparkColor: '#FF6600',
            path: '/orders',
          },
          {
            title: t('revenueThisMonth'),
            value: `${fmt(ld.revenue_this_month ?? d.accounting?.total_revenue ?? 0)} ${cur}`,
            icon: DollarSign,
            color: '#10b981',
            sparkData: ld.sparkline_orders,
            sparkColor: '#10b981',
            path: '/reports',
          },
          {
            title: t('lowStockAlerts'),
            value: ld.low_stock ?? d.inventory?.low_stock ?? 0,
            icon: AlertTriangle,
            color: '#ef4444',
            sparkData: null,
            sparkColor: '#ef4444',
            path: '/products',
          },
          {
            title: t('pendingTasks'),
            value: ld.pending_orders ?? d.sales?.pending_orders ?? 0,
            icon: Clock,
            color: '#3b82f6',
            sparkData: null,
            sparkColor: '#3b82f6',
            path: '/orders',
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
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
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
                {(i === 0 || i === 3) && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${i === 0 && (d.inventory?.low_stock ?? 0) > 0 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'}`}>
                    {i === 0 ? (d.inventory?.low_stock ?? 0) > 0 ? `${d.inventory.low_stock} ⚠` : '✓' : d.accounting?.net_profit >= 0 ? '↑' : '↓'}
                  </span>
                )}
              </div>
              <p className="text-base sm:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">{card.value}</p>
              <p className="text-[10px] sm:text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* ── Charts Row 1: Sales + Revenue ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sales Area Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('monthlySales')}</h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              {salesData.length > 0 ? (
                <AreaChart data={salesData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Legend content={<CustomLegend isDark={isDark} />} />
                  <Area type="monotone" dataKey={t('sales')} stroke="#3b82f6" strokeWidth={2.5} fill="url(#salesGrad)" dot={{ r: 3, fill: '#3b82f6' }} activeDot={{ r: 5, stroke: '#3b82f6', strokeWidth: 2 }} />
                  <Area type="monotone" dataKey={t('profit')} stroke="#10b981" strokeWidth={2} fill="url(#profitGrad)" dot={{ r: 2.5, fill: '#10b981' }} />
                </AreaChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Revenue Donut Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('revenueDistribution')}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {revenueData.length > 0 ? (
                  <PieChart>
                    <Pie data={revenueData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                      {revenueData.map((entry, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />
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
              {revenueData.map((entry, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1 text-xs sm:text-sm">{entry.name}</span>
                  <span className="text-gray-900 dark:text-gray-100 font-bold text-xs sm:text-sm" dir="ltr">{fmt(Math.round(entry.value))}</span>
                </div>
              ))}
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t('total')}</span>
                  <span className="font-bold text-sm text-gray-900 dark:text-gray-100" dir="ltr">{fmt(Math.round(revenueData.reduce((s, d) => s + d.value, 0)))}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Charts Row 2: Status + Purchases ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Order Status Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('orderStatusDist')}</h3>
          <div className="h-52 sm:h-56">
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

        {/* Purchases Area Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('purchases')}</h3>
          <div className="h-52 sm:h-56">
            <ResponsiveContainer width="100%" height="100%">
              {purchaseData.length > 0 ? (
                <AreaChart data={purchaseData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="purchaseGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                  <Area type="monotone" dataKey={t('purchases')} stroke="#06b6d4" strokeWidth={2.5} fill="url(#purchaseGrad)" dot={{ r: 3, fill: '#06b6d4' }} activeDot={{ r: 5 }} />
                </AreaChart>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Charts Row 3: Warehouse Stock + Contract Status ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Warehouse Stock Distribution Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('warehouseStock') || 'توزيع المخزون'}</h3>
          <div className="h-52 sm:h-56">
            <ResponsiveContainer width="100%" height="100%">
              {(() => {
                const whData = (d.warehouse?.low_stock_items || d.warehouse?.products_in_stock) ? [
                  { name: t('inStock') || 'في المخزون', value: d.warehouse?.products_in_stock || 0 },
                  { name: t('lowStock') || 'مخزون منخفض', value: d.warehouse?.low_stock_items || 0 },
                  { name: t('pendingTransfers') || 'تحويلات معلقة', value: d.warehouse?.pending_transfers || 0 },
                ] : [];
                return whData.length > 0 ? (
                  <BarChart data={whData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
                      <Cell fill="#8b5cf6" />
                      <Cell fill="#f59e0b" />
                      <Cell fill="#06b6d4" />
                    </Bar>
                  </BarChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
                );
              })()}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Contract Status Pie Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{t('contractStatus') || 'حالة العقود'}</h3>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                {(() => {
                  const cData = d.contracts ? [
                    { name: t('activeContracts') || 'نشطة', value: d.contracts.active_contracts || 0 },
                    { name: t('expiredContracts') || 'منتهية', value: d.contracts.expired_contracts || 0 },
                    { name: t('expiringSoon') || 'تنتهي قريباً', value: d.contracts.expiring_soon || 0 },
                  ].filter(s => s.value > 0) : [];
                  return cData.length > 0 ? (
                    <PieChart>
                      <Pie data={cData} cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" paddingAngle={4} dataKey="value" animationBegin={0} animationDuration={800}>
                        {cData.map((entry, i) => <Cell key={i} fill={['#10b981', '#ef4444', '#f59e0b'][i % 3]} stroke="none" />)}
                      </Pie>
                      <Tooltip content={<ChartTooltip isDark={isDark} locale={locale} fmt={fmt} />} />
                    </PieChart>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">{t('noData')}</div>
                  );
                })()}
              </ResponsiveContainer>
            </div>
            <div className="space-y-3 text-sm flex-1 min-w-0">
              {d.contracts ? [
                { label: t('activeContracts') || 'عقود نشطة', value: d.contracts.active_contracts, color: '#10b981' },
                { label: t('expiredContracts') || 'عقود منتهية', value: d.contracts.expired_contracts, color: '#ef4444' },
                { label: t('expiringSoon') || 'تنتهي قريباً', value: d.contracts.expiring_soon, color: '#f59e0b' },
                { label: t('totalValue') || 'إجمالي القيمة', value: fmt(Math.round(d.contracts.total_value || 0)), color: '#3b82f6' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1 text-xs sm:text-sm">{item.label}</span>
                  <span className="text-gray-900 dark:text-gray-100 font-bold text-xs sm:text-sm" dir="ltr">{typeof item.value === 'number' ? item.value : item.value}</span>
                </div>
              )) : <div className="flex items-center justify-center h-full text-gray-400 text-sm">{t('noData')}</div>}
            </div>
          </div>
        </div>
      </div>

      {/* ── Quick Summary Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[
          { label: t('revenue'), value: d.accounting?.total_revenue || 0, color: 'green', icon: TrendingUp },
          { label: t('expenses'), value: d.accounting?.total_expenses || 0, color: 'red', icon: TrendingDown },
          { label: t('netProfit'), value: d.accounting?.net_profit || 0, color: 'blue', icon: DollarSign },
          { label: t('totalSalaries'), value: d.hr?.total_salary || 0, color: 'indigo', icon: Users },
        ].map((item, i) => {
          const colorClasses = {
            green: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300',
            red: 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300',
            blue: 'bg-riadah-50 dark:bg-riadah-900/20 text-riadah-700 dark:text-riadah-300',
            indigo: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300',
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

      {/* ── Module Stats Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[
          { label: t('warehouseStock') || 'إجمالي المخزون', value: d.warehouse?.total_stock_value || 0, color: 'purple', icon: WarehouseIcon },
          { label: t('assetsValue') || 'قيمة الأصول', value: d.assets?.total_current_value || 0, color: 'violet', icon: Landmark },
          { label: t('totalInvoices') || 'إجمالي الفواتير', value: d.invoicing?.total_invoices || 0, color: 'rose', icon: Receipt },
          { label: t('totalPayroll') || 'إجمالي الرواتب', value: d.payroll?.total_paid_this_month || 0, color: 'amber', icon: Wallet },
        ].map((item, i) => {
          const colorClasses = {
            purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300',
            violet: 'bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300',
            rose: 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-300',
            amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300',
          };
          return (
            <div key={i} onClick={() => navigate(['warehouse', 'assets', 'invoices', 'payroll'][i])}
              className={`rounded-xl p-3 sm:p-4 border transition-all cursor-pointer hover:shadow-md ${colorClasses[item.color]}`}>
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
            <div className="p-8 text-center text-gray-400 dark:text-gray-500 text-sm">{t('noRecentOrders')}</div>
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
            {filteredActions.map((action, i) => {
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

      {/* ── Recent Activity Timeline ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent-500" />
            {t('recentActivity')}
          </h3>
          <div className="flex items-center gap-1.5">
            <span className="relative flex items-center justify-center">
              <span className="absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-[10px] text-gray-400">{t('liveStats')}</span>
          </div>
        </div>
        {ld.recent_activity && ld.recent_activity.length > 0 ? (
          <div className="divide-y divide-gray-50 dark:divide-gray-700/50 max-h-80 overflow-y-auto">
            {ld.recent_activity.map((entry, i) => {
              const AIcon = activityIcon(entry.action);
              const aColor = activityColor(entry.action);
              return (
                <div key={entry.id || i} className="px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${aColor}`}>
                    <AIcon className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{entry.user}</span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">{formatTime(entry.created_at)}</span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                      {entry.action} {entry.model}{entry.object_repr ? ` — ${entry.object_repr}` : ''}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center">
            <Activity className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="text-sm text-gray-400 dark:text-gray-500">{t('noData')}</p>
          </div>
        )}
      </div>

      {/* ── Low Stock Alert ── */}
      {(d.inventory?.low_stock ?? 0) > 0 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-3 sm:p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-orange-800 dark:text-orange-200">{t('lowStockAlert')}</p>
            <p className="text-xs text-orange-600 dark:text-orange-300 mt-0.5">{d.inventory.low_stock} {t('lowStockMsg')}</p>
            <button onClick={() => navigate('/products')} className="text-xs font-medium text-orange-700 dark:text-orange-300 hover:underline mt-1">{t('reviewProducts')}</button>
          </div>
        </div>
      )}

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
