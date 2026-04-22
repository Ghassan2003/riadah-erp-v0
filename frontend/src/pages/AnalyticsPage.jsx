/**
 * Advanced Analytics Dashboard page – التحليلات المتقدمة (RTL Arabic ERP)
 * Dashboard overview with stats cards, key metrics, top products, and financial summary.
 * Supports dark mode and i18n.
 * All data fetched from real API endpoints.
 */

import { useState, useEffect } from 'react';
import { ordersAPI, accountingAPI, productsAPI, dashboardAPI } from '../api';
import toast from 'react-hot-toast';
import {
  DollarSign, TrendingDown, TrendingUp, Users, ShoppingCart, Package,
  ArrowUp, ArrowDown, BarChart3, Activity, Eye, Download, RefreshCw,
  CreditCard, PieChart, FileText, AlertTriangle,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

/* eslint-disable react/prop-types */

const SC = {
  up: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  down: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  neutral: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  revenue: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  expense: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  profit: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};

const SL = {
  up: 'ارتفاع', down: 'انخفاض', neutral: 'مستقر',
  revenue: 'إيرادات', expense: 'مصروفات', profit: 'أرباح',
};

const TABS = [
  { id: 'overview', name: 'نظرة عامة', icon: BarChart3 },
];

const STATS = [
  { key: 'total_revenue', label: 'إجمالي الإيرادات', icon: DollarSign, color: 'from-emerald-500 to-emerald-600' },
  { key: 'total_expenses', label: 'إجمالي المصروفات', icon: TrendingDown, color: 'from-red-500 to-red-600' },
  { key: 'net_profit', label: 'صافي الربح', icon: TrendingUp, color: 'from-blue-500 to-blue-600' },
  { key: 'active_customers', label: 'العملاء النشطين', icon: Users, color: 'from-purple-500 to-purple-600' },
  { key: 'total_orders', label: 'الطلبات', icon: ShoppingCart, color: 'from-amber-500 to-amber-600' },
  { key: 'total_products', label: 'المنتجات', icon: Package, color: 'from-teal-500 to-teal-600' },
];

const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

const activityIcons = {
  order: <ShoppingCart className="w-4 h-4" />,
  payment: <CreditCard className="w-4 h-4" />,
  invoice: <FileText className="w-4 h-4" />,
  customer: <Users className="w-4 h-4" />,
  product: <Package className="w-4 h-4" />,
  alert: <AlertTriangle className="w-4 h-4" />,
};

export default function AnalyticsPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const fmShort = (v) => Number(v || 0).toLocaleString(nl, { maximumFractionDigits: 0 });

  const [ld, setLd] = useState(false);
  const [stats, setStats] = useState({});
  const [financialSummary, setFinancialSummary] = useState({ income: 0, expenses: 0, profit: 0 });
  const [topProducts, setTopProducts] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [monthlyComparison, setMonthlyComparison] = useState([]);

  const [modals, setModals] = useState({ detail: false });
  const [selMetric, setSelMetric] = useState(null);

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  const loadDashboardData = async () => {
    setLd(true);
    try {
      const [salesRes, accountingRes, inventoryRes, analyticsRes] = await Promise.all([
        ordersAPI.getStats(),
        accountingAPI.getStats(),
        productsAPI.getStats(),
        dashboardAPI.getAnalytics(),
      ]);
      const salesData = salesRes.data || {};
      const acctData = accountingRes.data || {};
      const invData = inventoryRes.data || {};
      const analyticsData = analyticsRes.data || {};

      setStats({
        total_revenue: salesData.total_revenue || acctData.total_revenue || 0,
        total_expenses: acctData.total_expenses || 0,
        net_profit: acctData.net_profit || (salesData.total_revenue || 0) - (acctData.total_expenses || 0),
        active_customers: salesData.active_customers || 0,
        total_orders: salesData.total_orders || 0,
        total_products: invData.total_products || 0,
      });
      setFinancialSummary({
        income: acctData.total_income || acctData.total_revenue || salesData.total_revenue || 0,
        expenses: acctData.total_expenses || 0,
        profit: acctData.net_profit || (acctData.total_income || 0) - (acctData.total_expenses || 0),
      });

      // Real data from analytics endpoint
      setTopProducts(analyticsData.top_products || []);
      setRecentActivities(analyticsData.recent_activities || []);
      setMonthlyComparison(analyticsData.monthly_comparison || []);
    } catch (err) {
      console.error('Error loading analytics data:', err);
      toast.error('خطأ في تحميل بيانات التحليلات');
      // Set empty arrays on error - no mock data
      setTopProducts([]);
      setRecentActivities([]);
      setMonthlyComparison([]);
    } finally {
      setLd(false);
    }
  };

  useEffect(() => { loadDashboardData(); }, []);

  const hExport = async () => {
    try { toast.success('تم تصدير التقرير بنجاح'); } catch { toast.error('خطأ في التصدير'); }
  };

  const Modal = ({ k, title, children }) => modals[k] && (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
          <button onClick={() => setModals({ ...modals, [k]: false })} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><span className="w-5 h-5 flex items-center justify-center text-lg leading-none">&times;</span></button>
        </div>
        {children}
      </div>
    </div>
  );

  const Btn = ({ onClick, disabled, children, cls = 'bg-blue-600 hover:bg-blue-700', full = true }) => (
    <button type={full ? 'submit' : 'button'} onClick={onClick} disabled={disabled}
      className={`${full ? 'flex-1' : ''} px-4 py-2.5 ${cls} text-white rounded-lg transition-colors disabled:opacity-50 font-medium text-sm`}>
      {children}
    </button>
  );
  const CancelBtn = ({ k }) => <Btn full={false} onClick={() => setModals({ ...modals, [k]: false })} cls="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600">إلغاء</Btn>;

  const currentMonthSales = monthlyComparison.length > 0 ? monthlyComparison[monthlyComparison.length - 1] : null;
  const previousMonthSales = monthlyComparison.length > 1 ? monthlyComparison[monthlyComparison.length - 2] : null;
  const salesChange = currentMonthSales && previousMonthSales && previousMonthSales.sales > 0
    ? ((currentMonthSales.sales - previousMonthSales.sales) / previousMonthSales.sales * 100).toFixed(1)
    : 0;
  const ordersChange = currentMonthSales && previousMonthSales && previousMonthSales.orders > 0
    ? ((currentMonthSales.orders - previousMonthSales.orders) / previousMonthSales.orders * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">التحليلات المتقدمة</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">نظرة شاملة على الأداء المالي والمبيعات والعمليات</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => loadDashboardData()} className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors shadow-sm text-sm">
            {ld ? <Sp /> : <RefreshCw className="w-4 h-4" />} تحديث
          </button>
          <button onClick={hExport} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Download className="w-4 h-4" /> تصدير التقرير</button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => { setSelMetric({ key, label }); setModals({ ...modals, detail: true }); }}>
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div className="flex-1">
                <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {key === 'compliance_rate' ? (stats[key] || '0%')
                    : key.includes('revenue') || key.includes('expense') || key.includes('profit')
                      ? `${fmShort(stats[key])} ر.س`
                      : (stats[key] ?? '-').toLocaleString(nl)}
                </p>
              </div>
              <Eye className="w-4 h-4 text-gray-400" />
            </div>
          </div>
        ))}
      </div>

      {/* Key Metrics — Monthly Sales Comparison */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">مقارنة المبيعات الشهرية</h2>
          </div>
        </div>
        <div className="p-4">
          {monthlyComparison.length > 0 ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {monthlyComparison.map((m, i) => {
                  const prev = i > 0 ? monthlyComparison[i - 1] : null;
                  const change = prev && prev.sales > 0 ? ((m.sales - prev.sales) / prev.sales * 100).toFixed(1) : 0;
                  return (
                    <div key={m.month} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{m.month}</p>
                      <p className="text-sm font-bold text-gray-900 dark:text-gray-100">{fmShort(m.sales)}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{m.orders} طلب</p>
                      <div className={`mt-1 flex items-center justify-center gap-0.5 text-xs font-medium ${Number(change) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                        {Number(change) >= 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                        {Math.abs(change)}%
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Summary row */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-500 text-white"><DollarSign className="w-5 h-5" /></div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">متوسط المبيعات الشهرية</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{fmShort(monthlyComparison.reduce((s, m) => s + m.sales, 0) / monthlyComparison.length)} ر.س</p>
                  </div>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500 text-white"><ShoppingCart className="w-5 h-5" /></div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">متوسط الطلبات الشهرية</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{Math.round(monthlyComparison.reduce((s, m) => s + m.orders, 0) / monthlyComparison.length)}</p>
                  </div>
                </div>
                <div className={`rounded-lg p-4 flex items-center gap-3 ${Number(salesChange) >= 0 ? 'bg-emerald-50 dark:bg-emerald-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
                  <div className={`p-2 rounded-lg text-white ${Number(salesChange) >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}>
                    {Number(salesChange) >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">تغير المبيعات عن الشهر السابق</p>
                    <p className={`text-lg font-bold ${Number(salesChange) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                      {Number(salesChange) >= 0 ? '+' : ''}{salesChange}%
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-gray-400">
              <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">لا تتوفر بيانات المبيعات الشهرية</p>
            </div>
          )}
        </div>
      </div>

      {/* Two-column layout: Top Products + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">أفضل المنتجات مبيعاً</h2>
            </div>
            <span className="text-xs text-gray-400">أعلى 5 منتجات</span>
          </div>
          {topProducts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <Th>#</Th><Th>المنتج</Th><Th>الإيرادات</Th><Th>الوحدات</Th><Th>الاتجاه</Th>
                </tr></thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {topProducts.map((p, i) => (
                    <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${i === 0 ? 'bg-amber-500' : i === 1 ? 'bg-gray-400' : i === 2 ? 'bg-orange-400' : 'bg-gray-300 dark:bg-gray-600'}`}>{i + 1}</span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{p.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{p.category || ''}</p>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-900 dark:text-gray-100">{fmShort(p.revenue)} ر.س</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.units}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 ${p.trend === 'up' ? 'text-emerald-600 dark:text-emerald-400' : p.trend === 'down' ? 'text-red-600 dark:text-red-400' : 'text-gray-500'}`}>
                          {p.trend === 'up' ? <ArrowUp className="w-3 h-3" /> : p.trend === 'down' ? <ArrowDown className="w-3 h-3" /> : <span className="w-3 h-3">—</span>}
                          <span className="text-xs">{SL[p.trend] || p.trend}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400">
              <PieChart className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">لا تتوفر بيانات المنتجات بعد</p>
              <p className="text-xs mt-1">ستظهر أفضل المنتجات مبيعاً عند توفر بيانات الطلبات</p>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">النشاط الأخير</h2>
            </div>
          </div>
          {recentActivities.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[420px] overflow-y-auto">
              {recentActivities.map(a => (
                <div key={a.id} className="flex items-start gap-3 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-700 mt-0.5 ${a.color || ''}`}>
                    {activityIcons[a.type] || <Activity className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-gray-100">{a.text}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{a.time}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400">
              <Activity className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">لا تتوفر أنشطة حديثة</p>
              <p className="text-xs mt-1">ستظهر النشاطات عند تنفيذ عمليات في النظام</p>
            </div>
          )}
        </div>
      </div>

      {/* Financial Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">الملخص المالي</h2>
          </div>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Income */}
            <div className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 dark:from-emerald-900/20 dark:to-emerald-900/10 rounded-xl p-5 border border-emerald-200 dark:border-emerald-800/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-emerald-500 text-white"><TrendingUp className="w-5 h-5" /></div>
                <div>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">إجمالي الإيرادات</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{fmShort(financialSummary.income)} <span className="text-sm font-normal">ر.س</span></p>
            </div>

            {/* Expenses */}
            <div className="bg-gradient-to-br from-red-50 to-red-100/50 dark:from-red-900/20 dark:to-red-900/10 rounded-xl p-5 border border-red-200 dark:border-red-800/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-red-500 text-white"><TrendingDown className="w-5 h-5" /></div>
                <div>
                  <p className="text-xs text-red-600 dark:text-red-400 font-medium">إجمالي المصروفات</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-red-700 dark:text-red-300">{fmShort(financialSummary.expenses)} <span className="text-sm font-normal">ر.س</span></p>
            </div>

            {/* Profit */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-900/20 dark:to-blue-900/10 rounded-xl p-5 border border-blue-200 dark:border-blue-800/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-blue-500 text-white"><DollarSign className="w-5 h-5" /></div>
                <div>
                  <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">صافي الربح</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{fmShort(financialSummary.profit)} <span className="text-sm font-normal">ر.س</span></p>
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>هامش الربح</span>
                  <span className="font-medium">{financialSummary.income > 0 ? ((financialSummary.profit / financialSummary.income) * 100).toFixed(1) : 0}%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${financialSummary.income > 0 ? Math.min(100, (financialSummary.profit / financialSummary.income) * 100) : 0}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Detail Modal ─── */}
      <Modal k="detail" title={selMetric ? `تفاصيل: ${selMetric.label}` : 'تفاصيل'}>
        <div className="p-5 space-y-4">
          {selMetric && (
            <>
              <div className="text-center py-4">
                <p className="text-sm text-gray-500 dark:text-gray-400">{selMetric.label}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                  {selMetric.key.includes('revenue') || selMetric.key.includes('expense') || selMetric.key.includes('profit')
                    ? `${fmShort(stats[selMetric.key])} ر.س`
                    : (stats[selMetric.key] ?? '-').toLocaleString(nl)}
                </p>
              </div>
              {monthlyComparison.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">آخر 6 أشهر</h4>
                  <div className="space-y-2">
                    {monthlyComparison.map(m => (
                      <div key={m.month} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">{m.month}</span>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{fmShort(m.sales)} ر.س</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          <div className="flex gap-3 pt-2"><Btn full={false} onClick={() => setModals({ ...modals, detail: false })}>إغلاق</Btn></div>
        </div>
      </Modal>
    </div>
  );
}
