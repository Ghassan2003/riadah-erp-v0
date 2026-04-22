/**
 * Final Comprehensive Reports page - Phase 5.
 * Executive overview combining all modules: inventory, sales, accounting, HR.
 */

import { useState, useEffect } from 'react';
import { productsAPI, ordersAPI, accountingAPI, hrAPI, reportsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Package, ShoppingCart, DollarSign, Users, TrendingUp, TrendingDown,
  BarChart3, Building2, Clock, AlertTriangle, RefreshCw,
  FileText, PieChart, ArrowUp, ArrowDown,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export default function FinalReportPage() {
  const { t, locale } = useI18n();
  const [inventoryStats, setInventoryStats] = useState(null);
  const [salesStats, setSalesStats] = useState(null);
  const [accountingStats, setAccountingStats] = useState(null);
  const [hrStats, setHrStats] = useState(null);
  const [incomeReport, setIncomeReport] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [inv, sales, acc, hrP, income, balance] = await Promise.all([
        productsAPI.getStats(),
        ordersAPI.getStats(),
        accountingAPI.getStats(),
        hrAPI.getStats(),
        reportsAPI.incomeStatement(),
        reportsAPI.balanceSheet(),
      ]);
      setInventoryStats(inv.data);
      setSalesStats(sales.data);
      setAccountingStats(acc.data);
      setHrStats(hrP.data);
      setIncomeReport(income.data);
      setBalanceSheet(balance.data);
    } catch {
      toast.error(t('error') || 'خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const formatAmount = (val) => Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const sections = [
    { id: 'overview', name: t('overview'), icon: BarChart3 },
    { id: 'operations', name: t('operations'), icon: Package },
    { id: 'finance', name: t('finance'), icon: DollarSign },
    { id: 'hr', name: t('hr'), icon: Users },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-accent-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('comprehensiveTitle')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('comprehensiveDesc')}</p>
        </div>
        <button onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm">
          <RefreshCw className="w-5 h-5" /> {t('generateComprehensive')}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {sections.map((sec) => {
          const Icon = sec.icon;
          return (
            <button key={sec.id} onClick={() => setActiveSection(sec.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeSection === sec.id ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>
              <Icon className="w-4 h-4" /> {sec.name}
            </button>
          );
        })}
      </div>

      {/* ====== Overview Section ====== */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Executive KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalSales')}</p>
                  <p className="text-2xl font-bold text-accent-500 dark:text-accent-400 mt-1">{formatAmount(salesStats?.total_sales)}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-riadah-50 dark:bg-riadah-900/30 flex items-center justify-center"><ShoppingCart className="w-6 h-6 text-accent-500 dark:text-accent-400" /></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('netProfit')}</p>
                  <p className={`text-2xl font-bold mt-1 ${(accountingStats?.net_profit || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>{formatAmount(accountingStats?.net_profit)}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-green-50 dark:bg-green-900/30 flex items-center justify-center"><TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" /></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalEmployees')}</p>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{hrStats?.total_employees || 0}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center"><Users className="w-6 h-6 text-purple-600 dark:text-purple-400" /></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('salaryExpenses')}</p>
                  <p className="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{formatAmount(hrStats?.total_salary_expense)}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-orange-50 dark:bg-orange-900/30 flex items-center justify-center"><DollarSign className="w-6 h-6 text-orange-600 dark:text-orange-400" /></div>
              </div>
            </div>
          </div>

          {/* Summary cards row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><Package className="w-4 h-4 text-accent-500 dark:text-accent-400" /> {t('inventory')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('totalProducts')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{inventoryStats?.total_products || 0}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('inventoryValue')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(inventoryStats?.inventory_value)} {t('currency')}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('lowStockProducts')}:</span><span className={`font-medium ${(inventoryStats?.low_stock_products || 0) > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>{inventoryStats?.low_stock_products || 0}</span></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><ShoppingCart className="w-4 h-4 text-green-500 dark:text-green-400" /> {t('sales')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('activeOrders')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{salesStats?.total_orders || 0}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('todaySales')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(salesStats?.today_sales)} {t('currency')}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('monthSales')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(salesStats?.this_month_sales)} {t('currency')}</span></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><Users className="w-4 h-4 text-purple-500 dark:text-purple-400" /> {t('hr')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('departments')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{hrStats?.total_departments || 0}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('onLeave')}:</span><span className="font-medium text-yellow-600 dark:text-yellow-400">{hrStats?.on_leave_employees || 0}</span></div>
                <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('pendingLeaves')}:</span><span className="font-medium text-orange-600 dark:text-orange-400">{hrStats?.pending_leaves || 0}</span></div>
              </div>
            </div>
          </div>

          {/* Alerts */}
          {(inventoryStats?.low_stock_products > 0 || hrStats?.pending_leaves > 0) && (
            <div className="space-y-3">
              {inventoryStats?.low_stock_products > 0 && (
                <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-4 flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0" />
                  <p className="text-sm text-orange-700 dark:text-orange-300"><strong>{t('alert')}:</strong> {t('lowStockAlert', { count: inventoryStats.low_stock_products })}</p>
                </div>
              )}
              {hrStats?.pending_leaves > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4 flex items-center gap-3">
                  <Clock className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                  <p className="text-sm text-yellow-700 dark:text-yellow-300"><strong>{t('alert')}:</strong> {t('pendingLeaveAlert', { count: hrStats.pending_leaves })}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ====== Operations Section ====== */}
      {activeSection === 'operations' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><Package className="w-5 h-5 text-accent-500 dark:text-accent-400" /> {t('inventoryStats')}</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('totalProducts')}</span><span className="text-xl font-bold text-riadah-700 dark:text-accent-300">{inventoryStats?.total_products || 0}</span></div>
              <div className="flex justify-between items-center p-3 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('totalInventoryValue')}</span><span className="text-xl font-bold text-riadah-700 dark:text-accent-300">{formatAmount(inventoryStats?.inventory_value)} {t('currency')}</span></div>
              <div className="flex justify-between items-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('lowStockProducts')}</span><span className="text-xl font-bold text-orange-700 dark:text-orange-300">{inventoryStats?.low_stock_products || 0}</span></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><ShoppingCart className="w-5 h-5 text-green-500 dark:text-green-400" /> {t('salesStats')}</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('totalOrders')}</span><span className="text-xl font-bold text-green-700 dark:text-green-300">{salesStats?.total_orders || 0}</span></div>
              <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('todaySales')}</span><span className="text-xl font-bold text-green-700 dark:text-green-300">{formatAmount(salesStats?.today_sales)} {t('currency')}</span></div>
              <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('monthSales')}</span><span className="text-xl font-bold text-green-700 dark:text-green-300">{formatAmount(salesStats?.this_month_sales)} {t('currency')}</span></div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('totalSales')}</span><span className="text-xl font-bold text-gray-900 dark:text-gray-100">{formatAmount(salesStats?.total_sales)} {t('currency')}</span></div>
            </div>
          </div>
        </div>
      )}

      {/* ====== Finance Section ====== */}
      {activeSection === 'finance' && (
        <div className="space-y-6">
          {/* Accounting KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalRevenue')}</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{formatAmount(accountingStats?.total_income)}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalExpenses')}</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{formatAmount(accountingStats?.total_expenses)}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('netProfit')}</p>
              <p className={`text-2xl font-bold mt-1 ${(accountingStats?.net_profit || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>{formatAmount(accountingStats?.net_profit)}</p>
            </div>
          </div>

          {/* Income Statement Summary */}
          {incomeReport && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><FileText className="w-5 h-5 text-green-500 dark:text-green-400" /> {t('incomeStatement')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-green-700 dark:text-green-400 mb-2">{t('income')}</h4>
                  {incomeReport.income_accounts?.length > 0 ? incomeReport.income_accounts.map((acc, i) => (
                    <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-50 dark:border-gray-700">
                      <span className="text-gray-600 dark:text-gray-400">{acc.account_code} - {acc.account_name}</span>
                      <span className="font-medium text-green-600 dark:text-green-400">{formatAmount(acc.balance)}</span>
                    </div>
                  )) : <p className="text-sm text-gray-400 dark:text-gray-500">{t('noIncomeData')}</p>}
                  <div className="flex justify-between text-sm font-bold mt-2 pt-2 border-t-2 border-green-200 dark:border-green-800">
                    <span className="text-gray-900 dark:text-gray-100">{t('total')}</span><span className="text-green-700 dark:text-green-300">{formatAmount(incomeReport.total_income)}</span>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-red-700 dark:text-red-400 mb-2">{t('expenses')}</h4>
                  {incomeReport.expense_accounts?.length > 0 ? incomeReport.expense_accounts.map((acc, i) => (
                    <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-50 dark:border-gray-700">
                      <span className="text-gray-600 dark:text-gray-400">{acc.account_code} - {acc.account_name}</span>
                      <span className="font-medium text-red-600 dark:text-red-400">{formatAmount(acc.balance)}</span>
                    </div>
                  )) : <p className="text-sm text-gray-400 dark:text-gray-500">{t('noExpenseData')}</p>}
                  <div className="flex justify-between text-sm font-bold mt-2 pt-2 border-t-2 border-red-200 dark:border-red-800">
                    <span className="text-gray-900 dark:text-gray-100">{t('total')}</span><span className="text-red-700 dark:text-red-300">{formatAmount(incomeReport.total_expenses)}</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg flex justify-between items-center">
                <span className="font-semibold text-gray-700 dark:text-gray-300">{t('netProfit')}</span>
                <span className={`text-xl font-bold ${(incomeReport.net_profit || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {formatAmount(incomeReport.net_profit)} {t('currency')}
                </span>
              </div>
            </div>
          )}

          {/* Balance Sheet Summary */}
          {balanceSheet && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><PieChart className="w-5 h-5 text-accent-500 dark:text-accent-400" /> {t('balanceSheet')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-riadah-700 dark:text-accent-400 mb-2">{t('assets')} ({formatAmount(balanceSheet.total_assets)})</h4>
                  {balanceSheet.asset_accounts?.map((acc, i) => (
                    <div key={i} className="flex justify-between text-sm py-1"><span className="text-gray-600 dark:text-gray-400">{acc.account_code} - {acc.account_name}</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(acc.balance)}</span></div>
                  ))}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-red-700 dark:text-red-400 mb-2">{t('liabilities')} ({formatAmount(balanceSheet.total_liabilities)})</h4>
                  {balanceSheet.liability_accounts?.map((acc, i) => (
                    <div key={i} className="flex justify-between text-sm py-1"><span className="text-gray-600 dark:text-gray-400">{acc.account_code} - {acc.account_name}</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(acc.balance)}</span></div>
                  ))}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-purple-700 dark:text-purple-400 mb-2">{t('equity')} ({formatAmount(balanceSheet.total_equity)})</h4>
                  {balanceSheet.equity_accounts?.map((acc, i) => (
                    <div key={i} className="flex justify-between text-sm py-1"><span className="text-gray-600 dark:text-gray-400">{acc.account_code} - {acc.account_name}</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(acc.balance)}</span></div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ====== HR Section ====== */}
      {activeSection === 'hr' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalEmployees')}</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{hrStats?.total_employees || 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('activeEmployees')}</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{hrStats?.active_employees || 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('onLeave')}</p>
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">{hrStats?.on_leave_employees || 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('monthlySalaryExpense')}</p>
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{formatAmount(hrStats?.total_salary_expense)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><Building2 className="w-5 h-5 text-accent-500 dark:text-accent-400" /> {t('departments')}</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('totalDepartments')}</span><span className="text-xl font-bold text-riadah-700 dark:text-accent-300">{hrStats?.total_departments || 0}</span></div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><Clock className="w-5 h-5 text-yellow-500 dark:text-yellow-400" /> {t('attendanceLeaves')}</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('todayAttendance')}</span><span className="text-xl font-bold text-green-700 dark:text-green-300">{hrStats?.today_attendance || 0}</span></div>
                <div className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('todayAbsent')}</span><span className="text-xl font-bold text-red-700 dark:text-red-300">{hrStats?.today_absent || 0}</span></div>
                <div className="flex justify-between items-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"><span className="text-gray-700 dark:text-gray-300">{t('pendingLeaves')}</span><span className="text-xl font-bold text-yellow-700 dark:text-yellow-300">{hrStats?.pending_leaves || 0}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
