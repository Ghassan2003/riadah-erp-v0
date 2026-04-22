/**
 * Financial Reports page - income statement and balance sheet.
 * Available to accountant, admin, and sales roles.
 */

import { useState } from 'react';
import { reportsAPI, pdfAPI } from '../api';
import toast from 'react-hot-toast';
import {
  FileText, TrendingUp, TrendingDown, BarChart3,
  Download, RefreshCw, CalendarDays, Loader2,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export default function FinancialReportsPage() {
  const { t, locale } = useI18n();
  const [activeTab, setActiveTab] = useState('income');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [incomeReport, setIncomeReport] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [loading, setLoading] = useState(false);

  const ACCOUNT_TYPE_LABELS = {
    asset: t('assets') || 'أصول',
    liability: t('liabilities') || 'خصوم',
    equity: t('equity') || 'حقوق ملكية',
    income: t('income') || 'إيرادات',
    expense: t('expenses') || 'مصروفات',
  };

  const ACCOUNT_TYPE_COLORS = {
    asset: 'text-accent-500 dark:text-accent-400',
    liability: 'text-red-600 dark:text-red-400',
    equity: 'text-purple-600 dark:text-purple-400',
    income: 'text-green-600 dark:text-green-400',
    expense: 'text-orange-600 dark:text-orange-400',
  };

  const fetchIncomeStatement = async () => {
    setLoading(true);
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await reportsAPI.incomeStatement(params);
      setIncomeReport(res.data);
    } catch {
      toast.error(t('errorLoadingIncomeReport') || 'خطأ في تحميل تقرير الأرباح والخسائر');
    } finally {
      setLoading(false);
    }
  };

  const fetchBalanceSheet = async () => {
    setLoading(true);
    try {
      const res = await reportsAPI.balanceSheet();
      setBalanceSheet(res.data);
    } catch {
      toast.error(t('errorLoadingBalanceSheet') || 'خطأ في تحميل الميزانية العمومية');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (activeTab === 'income') fetchIncomeStatement();
    else fetchBalanceSheet();
  };

  const formatAmount = (val) => Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 });

  // PDF download state
  const [pdfLoading, setPdfLoading] = useState('');

  const downloadPdf = async (type) => {
    setPdfLoading(type);
    try {
      const params = {};
      if (type === 'incomeStatement') {
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
      }
      const response = await pdfAPI[type](type === 'incomeStatement' ? params : undefined);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type === 'incomeStatement' ? t('incomeStatement') : t('balanceSheet')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(t('reportDownloaded') || 'تم تحميل التقرير بنجاح');
    } catch {
      toast.error(t('errorDownloadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setPdfLoading('');
    }
  };

  const tabs = [
    { id: 'income', name: t('incomeStatement'), icon: TrendingUp },
    { id: 'balance', name: t('balanceSheet'), icon: BarChart3 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('financialReports')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('financialReportsDesc')}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}>
              <Icon className="w-4 h-4" />
              {tab.name}
            </button>
          );
        })}
      </div>

      {/* Date filter (for income statement) */}
      {activeTab === 'income' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row items-end gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodFrom')}</label>
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
                className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodTo')}</label>
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
            </div>
            <div className="flex gap-2">
              <button onClick={fetchIncomeStatement} disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50">
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {t('generateReport')}
              </button>
              <button onClick={() => downloadPdf('incomeStatement')} disabled={pdfLoading === 'incomeStatement'}
                className="flex items-center gap-2 px-4 py-2.5 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors disabled:opacity-50">
                {pdfLoading === 'incomeStatement' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Income Statement */}
      {activeTab === 'income' && incomeReport && (
        <div className="space-y-4">
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalRevenue')}</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{formatAmount(incomeReport.total_income)}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalExpenses')}</p>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{formatAmount(incomeReport.total_expenses)}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-red-50 dark:bg-red-900/30 flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
              </div>
            </div>
            <div className={`bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border ${incomeReport.net_profit >= 0 ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('netIncome')}</p>
                  <p className={`text-2xl font-bold mt-1 ${incomeReport.net_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {formatAmount(incomeReport.net_profit)} {t('currency')}
                  </p>
                </div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${incomeReport.net_profit >= 0 ? 'bg-green-50 dark:bg-green-900/30' : 'bg-red-50 dark:bg-red-900/30'}`}>
                  {incomeReport.net_profit >= 0
                    ? <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                    : <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />
                  }
                </div>
              </div>
            </div>
          </div>

          {/* Detailed tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Income */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="bg-green-50 dark:bg-green-900/20 px-5 py-3 border-b border-green-100 dark:border-green-800">
                <h3 className="font-semibold text-green-800 dark:text-green-300">{t('income')}</h3>
              </div>
              {incomeReport.income_accounts?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                      <th className="px-4 py-2.5 text-right font-medium">{t('account')}</th>
                      <th className="px-4 py-2.5 text-right font-medium">{t('amount')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incomeReport.income_accounts.map((acc, i) => (
                      <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                        <td className="px-4 py-2.5">
                          <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{acc.account_code}</span>{' '}
                          <span className="text-gray-900 dark:text-gray-100">{acc.account_name}</span>
                        </td>
                        <td className="px-4 py-2.5 text-green-700 dark:text-green-300 font-medium">{formatAmount(acc.balance)}</td>
                      </tr>
                    ))}
                    <tr className="border-t-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 font-bold">
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('totalRevenue')}</td>
                      <td className="px-4 py-2.5 text-green-700 dark:text-green-300">{formatAmount(incomeReport.total_income)}</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noIncomeData')}</div>
              )}
            </div>

            {/* Expenses */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="bg-red-50 dark:bg-red-900/20 px-5 py-3 border-b border-red-100 dark:border-red-800">
                <h3 className="font-semibold text-red-800 dark:text-red-300">{t('expenses')}</h3>
              </div>
              {incomeReport.expense_accounts?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                      <th className="px-4 py-2.5 text-right font-medium">{t('account')}</th>
                      <th className="px-4 py-2.5 text-right font-medium">{t('amount')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incomeReport.expense_accounts.map((acc, i) => (
                      <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                        <td className="px-4 py-2.5">
                          <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{acc.account_code}</span>{' '}
                          <span className="text-gray-900 dark:text-gray-100">{acc.account_name}</span>
                        </td>
                        <td className="px-4 py-2.5 text-red-700 dark:text-red-300 font-medium">{formatAmount(acc.balance)}</td>
                      </tr>
                    ))}
                    <tr className="border-t-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 font-bold">
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('totalExpenses')}</td>
                      <td className="px-4 py-2.5 text-red-700 dark:text-red-300">{formatAmount(incomeReport.total_expenses)}</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noExpenseData')}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Balance Sheet */}
      {activeTab === 'balance' && (
        <div className="space-y-4">
          <div className="flex justify-end gap-2">
            <button onClick={fetchBalanceSheet} disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {t('generateReport')}
            </button>
            <button onClick={() => downloadPdf('balanceSheet')} disabled={pdfLoading === 'balanceSheet'}
              className="flex items-center gap-2 px-4 py-2.5 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors disabled:opacity-50">
              {pdfLoading === 'balanceSheet' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              PDF
            </button>
          </div>

          {balanceSheet ? (
            <>
              {/* Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-riadah-100 dark:border-riadah-800">
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalAssets')}</p>
                  <p className="text-2xl font-bold text-accent-500 dark:text-accent-400 mt-1">{formatAmount(balanceSheet.total_assets)} {t('currency')}</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-red-100 dark:border-red-800">
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalLiabilities')}</p>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{formatAmount(balanceSheet.total_liabilities)} {t('currency')}</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-purple-100 dark:border-purple-800">
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalEquity')}</p>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{formatAmount(balanceSheet.total_equity)} {t('currency')}</p>
                </div>
              </div>

              {/* Detailed tables */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Assets */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="bg-riadah-50 dark:bg-riadah-900/20 px-5 py-3 border-b border-riadah-100 dark:border-riadah-800">
                    <h3 className="font-semibold text-riadah-800 dark:text-accent-300">{t('assets')}</h3>
                  </div>
                  {balanceSheet.asset_accounts?.length > 0 ? (
                    <table className="w-full text-sm">
                      <tbody>
                        {balanceSheet.asset_accounts.map((acc, i) => (
                          <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                            <td className="px-4 py-2.5">
                              <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{acc.account_code}</span>{' '}
                              <span className="text-gray-900 dark:text-gray-100">{acc.account_name}</span>
                            </td>
                            <td className="px-4 py-2.5 text-riadah-700 dark:text-accent-300 font-medium">{formatAmount(acc.balance)}</td>
                          </tr>
                        ))}
                        <tr className="border-t-2 border-riadah-200 dark:border-riadah-800 bg-riadah-50 dark:bg-riadah-900/20 font-bold">
                          <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('total')}</td>
                          <td className="px-4 py-2.5 text-riadah-700 dark:text-accent-300">{formatAmount(balanceSheet.total_assets)}</td>
                        </tr>
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noAssetsData')}</div>
                  )}
                </div>

                {/* Liabilities */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="bg-red-50 dark:bg-red-900/20 px-5 py-3 border-b border-red-100 dark:border-red-800">
                    <h3 className="font-semibold text-red-800 dark:text-red-300">{t('liabilities')}</h3>
                  </div>
                  {balanceSheet.liability_accounts?.length > 0 ? (
                    <table className="w-full text-sm">
                      <tbody>
                        {balanceSheet.liability_accounts.map((acc, i) => (
                          <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                            <td className="px-4 py-2.5">
                              <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{acc.account_code}</span>{' '}
                              <span className="text-gray-900 dark:text-gray-100">{acc.account_name}</span>
                            </td>
                            <td className="px-4 py-2.5 text-red-700 dark:text-red-300 font-medium">{formatAmount(acc.balance)}</td>
                          </tr>
                        ))}
                        <tr className="border-t-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 font-bold">
                          <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('total')}</td>
                          <td className="px-4 py-2.5 text-red-700 dark:text-red-300">{formatAmount(balanceSheet.total_liabilities)}</td>
                        </tr>
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noLiabilitiesData')}</div>
                  )}
                </div>

                {/* Equity */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="bg-purple-50 dark:bg-purple-900/20 px-5 py-3 border-b border-purple-100 dark:border-purple-800">
                    <h3 className="font-semibold text-purple-800 dark:text-purple-300">{t('equity')}</h3>
                  </div>
                  {balanceSheet.equity_accounts?.length > 0 ? (
                    <table className="w-full text-sm">
                      <tbody>
                        {balanceSheet.equity_accounts.map((acc, i) => (
                          <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                            <td className="px-4 py-2.5">
                              <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{acc.account_code}</span>{' '}
                              <span className="text-gray-900 dark:text-gray-100">{acc.account_name}</span>
                            </td>
                            <td className="px-4 py-2.5 text-purple-700 dark:text-purple-300 font-medium">{formatAmount(acc.balance)}</td>
                          </tr>
                        ))}
                        <tr className="border-t-2 border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20 font-bold">
                          <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('total')}</td>
                          <td className="px-4 py-2.5 text-purple-700 dark:text-purple-300">{formatAmount(balanceSheet.total_equity)}</td>
                        </tr>
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noEquityData')}</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-12 shadow-sm border border-gray-100 dark:border-gray-700 text-center">
              <BarChart3 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">{t('clickToViewBalanceSheet')}</p>
            </div>
          )}
        </div>
      )}

      {/* Empty state for income statement */}
      {activeTab === 'income' && !incomeReport && !loading && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-12 shadow-sm border border-gray-100 dark:border-gray-700 text-center">
          <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 mb-3">{t('clickToViewIncomeStatement')}</p>
          <button onClick={fetchIncomeStatement}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors">
            <CalendarDays className="w-4 h-4" /> {t('viewReport')}
          </button>
        </div>
      )}
    </div>
  );
}
