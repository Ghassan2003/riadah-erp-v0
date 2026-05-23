/**
 * Financial Reports page — income statement, balance sheet, trial balance,
 * general ledger, cash flow statement, VAT return, and AR/AP aging.
 * Available to accountant, admin, and sales roles.
 */

import { useState, useEffect } from 'react';
import { reportsAPI, accountsAPI, pdfAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import {
  FileText, TrendingUp, TrendingDown, BarChart3,
  Download, RefreshCw, CalendarDays, Loader2,
  BookOpen, DollarSign, Receipt, Users,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Months helper for VAT Return filter                               */
/* ------------------------------------------------------------------ */
const MONTH_OPTIONS = [
  { value: 1, label: 'january', ar: 'يناير' },
  { value: 2, label: 'february', ar: 'فبراير' },
  { value: 3, label: 'march', ar: 'مارس' },
  { value: 4, label: 'april', ar: 'أبريل' },
  { value: 5, label: 'may', ar: 'مايو' },
  { value: 6, label: 'june', ar: 'يونيو' },
  { value: 7, label: 'july', ar: 'يوليو' },
  { value: 8, label: 'august', ar: 'أغسطس' },
  { value: 9, label: 'september', ar: 'سبتمبر' },
  { value: 10, label: 'october', ar: 'أكتوبر' },
  { value: 11, label: 'november', ar: 'نوفمبر' },
  { value: 12, label: 'december', ar: 'ديسمبر' },
];

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */
export default function FinancialReportsPage() {
  const { t, locale } = useI18n();

  /* ---- shared state ---- */
  const [activeTab, setActiveTab] = useState('income');
  const [loading, setLoading] = useState(false);

  /* ---- date filters ---- */
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [trialDateTo, setTrialDateTo] = useState('');
  const [cashflowFrom, setCashflowFrom] = useState('');
  const [cashflowTo, setCashflowTo] = useState('');

  /* ---- report data ---- */
  const [incomeReport, setIncomeReport] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [trialBalance, setTrialBalance] = useState(null);
  const [ledgerData, setLedgerData] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [vatReturn, setVatReturn] = useState(null);
  const [arAging, setArAging] = useState(null);
  const [apAging, setApAging] = useState(null);

  /* ---- general ledger extras ---- */
  const [accountsList, setAccountsList] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');

  /* ---- VAT filter ---- */
  const [vatMonth, setVatMonth] = useState(new Date().getMonth() + 1);
  const [vatYear, setVatYear] = useState(new Date().getFullYear());

  /* ---- PDF ---- */
  const [pdfLoading, setPdfLoading] = useState('');

  /* ---- helpers ---- */
  const formatAmount = (val) =>
    Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      minimumFractionDigits: 2,
    });

  const inputClass =
    'px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-sm';

  /* ================================================================ */
  /*  FETCH FUNCTIONS                                                  */
  /* ================================================================ */

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

  const fetchTrialBalance = async () => {
    setLoading(true);
    try {
      const params = {};
      if (trialDateTo) params.date_to = trialDateTo;
      const res = await reportsAPI.trialBalance(params);
      setTrialBalance(res.data);
    } catch {
      toast.error(t('errorLoadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await accountsAPI.list({ page_size: 500 });
      setAccountsList(res.data?.results || res.data || []);
    } catch {
      /* silent — dropdown will just be empty */
    }
  };

  const fetchGeneralLedger = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedAccount) params.account = selectedAccount;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await reportsAPI.generalLedger(params);
      setLedgerData(res.data);
    } catch {
      toast.error(t('errorLoadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setLoading(false);
    }
  };

  const fetchCashFlow = async () => {
    setLoading(true);
    try {
      const params = {};
      if (cashflowFrom) params.date_from = cashflowFrom;
      if (cashflowTo) params.date_to = cashflowTo;
      const res = await reportsAPI.cashFlowStatement(params);
      setCashFlow(res.data);
    } catch {
      toast.error(t('errorLoadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setLoading(false);
    }
  };

  const fetchVatReturn = async () => {
    setLoading(true);
    try {
      const res = await reportsAPI.vatReturn({ month: vatMonth, year: vatYear });
      setVatReturn(res.data);
    } catch {
      toast.error(t('errorLoadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setLoading(false);
    }
  };

  const fetchAging = async () => {
    setLoading(true);
    try {
      const [arRes, apRes] = await Promise.all([
        reportsAPI.arAging(),
        reportsAPI.apAging(),
      ]);
      setArAging(arRes.data);
      setApAging(apRes.data);
    } catch {
      toast.error(t('errorLoadingReport') || 'خطأ في تحميل التقرير');
    } finally {
      setLoading(false);
    }
  };

  /* load accounts list once when ledger tab is activated */
  useEffect(() => {
    if (activeTab === 'ledger' && accountsList.length === 0) {
      fetchAccounts();
    }
  }, [activeTab]);

  /* auto-load aging on tab switch */
  useEffect(() => {
    if (activeTab === 'aging' && !arAging && !apAging) {
      fetchAging();
    }
  }, [activeTab]);

  /* ---- refresh dispatcher ---- */
  const handleRefresh = () => {
    switch (activeTab) {
      case 'income': fetchIncomeStatement(); break;
      case 'balance': fetchBalanceSheet(); break;
      case 'trial': fetchTrialBalance(); break;
      case 'ledger': fetchGeneralLedger(); break;
      case 'cashflow': fetchCashFlow(); break;
      case 'vat': fetchVatReturn(); break;
      case 'aging': fetchAging(); break;
      default: break;
    }
  };

  /* ---- PDF download ---- */
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

  /* ================================================================ */
  /*  TABS CONFIG                                                      */
  /* ================================================================ */
  const tabs = [
    { id: 'income', name: t('incomeStatement'), icon: TrendingUp, row: 1 },
    { id: 'balance', name: t('balanceSheet'), icon: BarChart3, row: 1 },
    { id: 'trial', name: t('trialBalance'), icon: BookOpen, row: 1 },
    { id: 'ledger', name: t('generalLedger'), icon: FileText, row: 1 },
    { id: 'cashflow', name: t('cashFlowStatement'), icon: DollarSign, row: 2 },
    { id: 'vat', name: t('vatReturn'), icon: Receipt, row: 2 },
    { id: 'aging', name: t('arApAging'), icon: Users, row: 2 },
  ];

  const row1Tabs = tabs.filter((tb) => tb.row === 1);
  const row2Tabs = tabs.filter((tb) => tb.row === 2);

  /* ================================================================ */
  /*  SHARED RENDER HELPERS                                            */
  /* ================================================================ */

  const LoadingSpinner = () => (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="w-8 h-8 animate-spin text-riadah-500" />
      <span className="mr-3 text-gray-500 dark:text-gray-400">{t('loading')}</span>
    </div>
  );

  const EmptyState = ({ icon: Icon, message, action, onAction }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-12 shadow-sm border border-gray-100 dark:border-gray-700 text-center">
      <Icon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
      <p className="text-gray-500 dark:text-gray-400 mb-3">{message}</p>
      {action && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors"
        >
          <CalendarDays className="w-4 h-4" /> {action}
        </button>
      )}
    </div>
  );

  const GenerateButton = ({ onClick, extraClass = '' }) => (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 ${extraClass}`}
    >
      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
      {t('generateReport')}
    </button>
  );

  const PdfButton = ({ type }) => (
    <button
      onClick={() => downloadPdf(type)}
      disabled={pdfLoading === type}
      className="flex items-center gap-2 px-4 py-2.5 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors disabled:opacity-50"
    >
      {pdfLoading === type ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
      PDF
    </button>
  );

  const DateRangeFilter = ({ from, to, setFrom, setTo, children }) => (
    <div className="flex flex-col sm:flex-row items-end gap-3">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodFrom')}</label>
        <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className={inputClass} />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodTo')}</label>
        <input type="date" value={to} onChange={(e) => setTo(e.target.value)} className={inputClass} />
      </div>
      {children}
    </div>
  );

  const FilterCard = ({ children }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
      {children}
    </div>
  );

  /* ================================================================ */
  /*  INCOME STATEMENT                                                 */
  /* ================================================================ */
  const renderIncomeStatement = () => {
    if (loading) return <LoadingSpinner />;
    if (!incomeReport) {
      return (
        <EmptyState
          icon={FileText}
          message={t('clickToViewIncomeStatement')}
          action={t('viewReport')}
          onAction={fetchIncomeStatement}
        />
      );
    }
    return (
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
                  : <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />}
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
              <div className="overflow-x-auto">
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
              </div>
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
              <div className="overflow-x-auto">
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
              </div>
            ) : (
              <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noExpenseData')}</div>
            )}
          </div>
        </div>
      </div>
    );
  };

  /* ================================================================ */
  /*  BALANCE SHEET                                                    */
  /* ================================================================ */
  const renderBalanceSheet = () => {
    if (loading) return <LoadingSpinner />;
    if (!balanceSheet) {
      return (
        <EmptyState
          icon={BarChart3}
          message={t('viewReport')}
          action={t('generateReport')}
          onAction={fetchBalanceSheet}
        />
      );
    }
    return (
      <div className="space-y-4">
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
      </div>
    );
  };

  /* ================================================================ */
  /*  TRIAL BALANCE                                                    */
  /* ================================================================ */
  const renderTrialBalance = () => {
    if (loading) return <LoadingSpinner />;
    if (!trialBalance) {
      return (
        <EmptyState
          icon={BookOpen}
          message={t('viewReport')}
          action={t('generateReport')}
          onAction={fetchTrialBalance}
        />
      );
    }

    const accounts = trialBalance.accounts || [];
    const totalDebit = accounts.reduce((s, a) => s + Number(a.debit_balance || 0), 0);
    const totalCredit = accounts.reduce((s, a) => s + Number(a.credit_balance || 0), 0);
    const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

    return (
      <div className="space-y-4">
        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-blue-100 dark:border-blue-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalDebit')}</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{formatAmount(totalDebit)} {t('currency')}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-red-100 dark:border-red-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalCredit')}</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{formatAmount(totalCredit)} {t('currency')}</p>
          </div>
          <div className={`bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border ${isBalanced ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'}`}>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('status')}</p>
            <p className={`text-2xl font-bold mt-1 ${isBalanced ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {isBalanced ? '✓' : '✗'} {t('isEqual')}
            </p>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="bg-blue-50 dark:bg-blue-900/20 px-5 py-3 border-b border-blue-100 dark:border-blue-800">
            <h3 className="font-semibold text-blue-800 dark:text-blue-300">{t('trialBalance')}</h3>
          </div>
          {accounts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                    <th className="px-4 py-2.5 text-right font-medium">{t('accountCode')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('accountName')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('debitBalance')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('creditBalance')}</th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.map((acc, i) => (
                    <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500 dark:text-gray-400">{acc.account_code}</td>
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{acc.account_name}</td>
                      <td className="px-4 py-2.5 text-blue-600 dark:text-blue-400 font-medium">{formatAmount(acc.debit_balance)}</td>
                      <td className="px-4 py-2.5 text-red-600 dark:text-red-400 font-medium">{formatAmount(acc.credit_balance)}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/70 font-bold">
                    <td className="px-4 py-3" colSpan={2}>{t('total')}</td>
                    <td className="px-4 py-3 text-blue-600 dark:text-blue-400">{formatAmount(totalDebit)}</td>
                    <td className="px-4 py-3 text-red-600 dark:text-red-400">{formatAmount(totalCredit)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
          )}
        </div>
      </div>
    );
  };

  /* ================================================================ */
  /*  GENERAL LEDGER                                                   */
  /* ================================================================ */
  const renderGeneralLedger = () => {
    if (loading) return <LoadingSpinner />;
    if (!ledgerData) {
      return (
        <EmptyState
          icon={FileText}
          message={t('viewReport')}
          action={t('generateReport')}
          onAction={fetchGeneralLedger}
        />
      );
    }

    const entries = ledgerData.entries || [];
    const accountInfo = ledgerData.account || {};

    return (
      <div className="space-y-4">
        {/* Account info header */}
        {accountInfo.account_code && (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('account')}</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                    <span className="font-mono text-blue-600 dark:text-blue-400">{accountInfo.account_code}</span> — {accountInfo.account_name}
                  </p>
                </div>
              </div>
              <div className="sm:mr-auto">
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('balance')}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{formatAmount(accountInfo.current_balance)} {t('currency')}</p>
              </div>
            </div>
          </div>
        )}

        {/* Entries table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="bg-blue-50 dark:bg-blue-900/20 px-5 py-3 border-b border-blue-100 dark:border-blue-800">
            <h3 className="font-semibold text-blue-800 dark:text-blue-300">{t('generalLedger')}</h3>
          </div>
          {entries.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                    <th className="px-4 py-2.5 text-right font-medium">{t('date')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('entryNumber')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('description')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('debit')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('credit')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('runningBalance')}</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry, i) => (
                    <tr key={i} className="border-t border-gray-50 dark:border-gray-700 hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">{entry.date}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500 dark:text-gray-400">{entry.entry_number}</td>
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{entry.description}</td>
                      <td className="px-4 py-2.5 text-blue-600 dark:text-blue-400 font-medium">{entry.debit ? formatAmount(entry.debit) : '-'}</td>
                      <td className="px-4 py-2.5 text-red-600 dark:text-red-400 font-medium">{entry.credit ? formatAmount(entry.credit) : '-'}</td>
                      <td className="px-4 py-2.5 font-semibold text-gray-900 dark:text-gray-100">{formatAmount(entry.running_balance)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
          )}
        </div>
      </div>
    );
  };

  /* ================================================================ */
  /*  CASH FLOW STATEMENT                                              */
  /* ================================================================ */
  const renderCashFlow = () => {
    if (loading) return <LoadingSpinner />;
    if (!cashFlow) {
      return (
        <EmptyState
          icon={DollarSign}
          message={t('viewReport')}
          action={t('generateReport')}
          onAction={fetchCashFlow}
        />
      );
    }

    const operating = cashFlow.operating_activities || [];
    const investing = cashFlow.investing_activities || [];
    const financing = cashFlow.financing_activities || [];

    const netOperating = operating.reduce((s, a) => s + Number(a.amount || 0), 0);
    const netInvesting = investing.reduce((s, a) => s + Number(a.amount || 0), 0);
    const netFinancing = financing.reduce((s, a) => s + Number(a.amount || 0), 0);
    const netChange = netOperating + netInvesting + netFinancing;

    const renderSection = (items, title, headerBg, headerText, textColor, borderClr) => (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className={`${headerBg} px-5 py-3 border-b ${borderClr}`}>
          <h3 className={`font-semibold ${headerText}`}>{title}</h3>
        </div>
        {items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                  <th className="px-4 py-2.5 text-right font-medium">{t('account')}</th>
                  <th className="px-4 py-2.5 text-right font-medium">{t('amount')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => (
                  <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                    <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{item.account_name || item.description}</td>
                    <td className={`px-4 py-2.5 font-medium ${textColor}`}>{formatAmount(item.amount)}</td>
                  </tr>
                ))}
                <tr className={`border-t-2 ${borderClr} ${headerBg} font-bold`}>
                  <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{t('total')}</td>
                  <td className={`px-4 py-2.5 ${textColor}`}>{formatAmount(items.reduce((s, a) => s + Number(a.amount || 0), 0))}</td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
        )}
      </div>
    );

    return (
      <div className="space-y-4">
        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-blue-100 dark:border-blue-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('netOperating')}</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{formatAmount(netOperating)} {t('currency')}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-purple-100 dark:border-purple-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('netInvesting')}</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{formatAmount(netInvesting)} {t('currency')}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-green-100 dark:border-green-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('netFinancing')}</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{formatAmount(netFinancing)} {t('currency')}</p>
          </div>
          <div className={`bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border ${netChange >= 0 ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'}`}>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('netChange')}</p>
            <p className={`text-2xl font-bold mt-1 ${netChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {formatAmount(netChange)} {t('currency')}
            </p>
          </div>
        </div>

        {/* Three sections */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {renderSection(
            operating, t('operatingActivities'),
            'bg-blue-50 dark:bg-blue-900/20', 'text-blue-800 dark:text-blue-300',
            'text-blue-600 dark:text-blue-400', 'border-blue-200 dark:border-blue-800',
          )}
          {renderSection(
            investing, t('investingActivities'),
            'bg-purple-50 dark:bg-purple-900/20', 'text-purple-800 dark:text-purple-300',
            'text-purple-600 dark:text-purple-400', 'border-purple-200 dark:border-purple-800',
          )}
          {renderSection(
            financing, t('financingActivities'),
            'bg-green-50 dark:bg-green-900/20', 'text-green-800 dark:text-green-300',
            'text-green-600 dark:text-green-400', 'border-green-200 dark:border-green-800',
          )}
        </div>
      </div>
    );
  };

  /* ================================================================ */
  /*  VAT RETURN                                                       */
  /* ================================================================ */
  const renderVatReturn = () => {
    if (loading) return <LoadingSpinner />;
    if (!vatReturn) {
      return (
        <EmptyState
          icon={Receipt}
          message={t('viewReport')}
          action={t('generateReport')}
          onAction={fetchVatReturn}
        />
      );
    }

    const outputVat = vatReturn.output_vat || [];
    const inputVat = vatReturn.input_vat || [];
    const totalSales = outputVat.reduce((s, a) => s + Number(a.amount || 0), 0);
    const totalPurchases = inputVat.reduce((s, a) => s + Number(a.amount || 0), 0);
    const totalOutputVat = outputVat.reduce((s, a) => s + Number(a.vat_amount || 0), 0);
    const totalInputVat = inputVat.reduce((s, a) => s + Number(a.vat_amount || 0), 0);
    const netVatDue = totalOutputVat - totalInputVat;

    return (
      <div className="space-y-4">
        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-green-100 dark:border-green-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalSales')}</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{formatAmount(totalSales)} {t('currency')}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-red-100 dark:border-red-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalPurchases')}</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{formatAmount(totalPurchases)} {t('currency')}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-blue-100 dark:border-blue-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('outputVat')}</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{formatAmount(totalOutputVat)} {t('currency')}</p>
          </div>
          <div className={`bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border ${netVatDue >= 0 ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'}`}>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('netVatDue')}</p>
            <p className={`text-2xl font-bold mt-1 ${netVatDue >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {formatAmount(netVatDue)} {t('currency')}
            </p>
          </div>
        </div>

        {/* Output VAT table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="bg-green-50 dark:bg-green-900/20 px-5 py-3 border-b border-green-100 dark:border-green-800">
            <h3 className="font-semibold text-green-800 dark:text-green-300">{t('outputVat')} ({t('totalSales')})</h3>
          </div>
          {outputVat.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                    <th className="px-4 py-2.5 text-right font-medium">{t('description')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('amount')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('vatRate')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('vatAmount')}</th>
                  </tr>
                </thead>
                <tbody>
                  {outputVat.map((item, i) => (
                    <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{item.description}</td>
                      <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">{formatAmount(item.amount)}</td>
                      <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">{item.vat_rate || '15%'}</td>
                      <td className="px-4 py-2.5 text-green-600 dark:text-green-400 font-medium">{formatAmount(item.vat_amount)}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 font-bold">
                    <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100" colSpan={3}>{t('total')}</td>
                    <td className="px-4 py-2.5 text-green-600 dark:text-green-400">{formatAmount(totalOutputVat)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
          )}
        </div>

        {/* Input VAT table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="bg-red-50 dark:bg-red-900/20 px-5 py-3 border-b border-red-100 dark:border-red-800">
            <h3 className="font-semibold text-red-800 dark:text-red-300">{t('inputVat')} ({t('totalPurchases')})</h3>
          </div>
          {inputVat.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                    <th className="px-4 py-2.5 text-right font-medium">{t('description')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('amount')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('vatRate')}</th>
                    <th className="px-4 py-2.5 text-right font-medium">{t('vatAmount')}</th>
                  </tr>
                </thead>
                <tbody>
                  {inputVat.map((item, i) => (
                    <tr key={i} className="border-t border-gray-50 dark:border-gray-700">
                      <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100">{item.description}</td>
                      <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">{formatAmount(item.amount)}</td>
                      <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">{item.vat_rate || '15%'}</td>
                      <td className="px-4 py-2.5 text-red-600 dark:text-red-400 font-medium">{formatAmount(item.vat_amount)}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 font-bold">
                    <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100" colSpan={3}>{t('total')}</td>
                    <td className="px-4 py-2.5 text-red-600 dark:text-red-400">{formatAmount(totalInputVat)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
          )}
        </div>

        {/* Net VAT due highlight */}
        <div className={`bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border-2 ${netVatDue >= 0 ? 'border-green-300 dark:border-green-700' : 'border-red-300 dark:border-red-700'}`}>
          <div className="flex items-center justify-between">
            <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('netVatDue')}</p>
            <p className={`text-3xl font-bold ${netVatDue >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {formatAmount(netVatDue)} {t('currency')}
            </p>
          </div>
        </div>
      </div>
    );
  };

  /* ================================================================ */
  /*  AR / AP AGING                                                    */
  /* ================================================================ */
  const agingColorMap = {
    current: 'text-green-600 dark:text-green-400',
    d1_30: 'text-blue-600 dark:text-blue-400',
    d31_60: 'text-yellow-600 dark:text-yellow-400',
    d61_90: 'text-orange-600 dark:text-orange-400',
    d90_plus: 'text-red-600 dark:text-red-400',
  };

  const renderAgingTable = (data, title, entityKey, headerBg, headerText, borderClr) => {
    const items = data?.items || data || [];
    if (!items || items.length === 0) {
      return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className={`${headerBg} px-5 py-3 border-b ${borderClr}`}>
            <h3 className={`font-semibold ${headerText}`}>{title}</h3>
          </div>
          <div className="p-8 text-center text-gray-400 dark:text-gray-500">{t('noData')}</div>
        </div>
      );
    }

    const totals = items.reduce(
      (acc, item) => ({
        total: acc.total + Number(item.total_outstanding || item.total || 0),
        current: acc.current + Number(item.current || 0),
        d1_30: acc.d1_30 + Number(item.days_1_30 || 0),
        d31_60: acc.d31_60 + Number(item.days_31_60 || 0),
        d61_90: acc.d61_90 + Number(item.days_61_90 || 0),
        d90_plus: acc.d90_plus + Number(item.days_90_plus || 0),
      }),
      { total: 0, current: 0, d1_30: 0, d31_60: 0, d61_90: 0, d90_plus: 0 },
    );

    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className={`${headerBg} px-5 py-3 border-b ${borderClr}`}>
          <h3 className={`font-semibold ${headerText}`}>{title}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300">
                <th className="px-4 py-2.5 text-right font-medium">{entityKey}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('totalOutstanding')}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('current')}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('days130')}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('days3160')}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('days6190')}</th>
                <th className="px-4 py-2.5 text-right font-medium">{t('days90Plus')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i} className="border-t border-gray-50 dark:border-gray-700 hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-2.5 text-gray-900 dark:text-gray-100 font-medium">{item.name || item.customer_name || item.supplier_name}</td>
                  <td className="px-4 py-2.5 font-semibold text-gray-900 dark:text-gray-100">{formatAmount(item.total_outstanding || item.total)}</td>
                  <td className={`px-4 py-2.5 ${agingColorMap.current}`}>{formatAmount(item.current)}</td>
                  <td className={`px-4 py-2.5 ${agingColorMap.d1_30}`}>{formatAmount(item.days_1_30)}</td>
                  <td className={`px-4 py-2.5 ${agingColorMap.d31_60}`}>{formatAmount(item.days_31_60)}</td>
                  <td className={`px-4 py-2.5 ${agingColorMap.d61_90}`}>{formatAmount(item.days_61_90)}</td>
                  <td className={`px-4 py-2.5 ${agingColorMap.d90_plus}`}>{formatAmount(item.days_90_plus)}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/70 font-bold">
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{t('total')}</td>
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{formatAmount(totals.total)}</td>
                <td className={`px-4 py-3 ${agingColorMap.current}`}>{formatAmount(totals.current)}</td>
                <td className={`px-4 py-3 ${agingColorMap.d1_30}`}>{formatAmount(totals.d1_30)}</td>
                <td className={`px-4 py-3 ${agingColorMap.d31_60}`}>{formatAmount(totals.d31_60)}</td>
                <td className={`px-4 py-3 ${agingColorMap.d61_90}`}>{formatAmount(totals.d61_90)}</td>
                <td className={`px-4 py-3 ${agingColorMap.d90_plus}`}>{formatAmount(totals.d90_plus)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderAging = () => {
    if (loading) return <LoadingSpinner />;
    return (
      <div className="space-y-6">
        {/* AR Aging */}
        {renderAgingTable(
          arAging,
          t('accountsReceivable'),
          t('customer'),
          'bg-green-50 dark:bg-green-900/20',
          'text-green-800 dark:text-green-300',
          'border-green-100 dark:border-green-800',
        )}
        {/* AP Aging */}
        {renderAgingTable(
          apAging,
          t('accountsPayable'),
          t('supplier'),
          'bg-orange-50 dark:bg-orange-900/20',
          'text-orange-800 dark:text-orange-300',
          'border-orange-100 dark:border-orange-800',
        )}
      </div>
    );
  };

  /* ================================================================ */
  /*  FILTER SECTIONS PER TAB                                          */
  /* ================================================================ */
  const renderFilterSection = () => {
    switch (activeTab) {
      /* ---------- Income Statement ---------- */
      case 'income':
        return (
          <FilterCard>
            <DateRangeFilter from={dateFrom} to={dateTo} setFrom={setDateFrom} setTo={setDateTo}>
              <div className="flex gap-2">
                <GenerateButton onClick={fetchIncomeStatement} />
                <PdfButton type="incomeStatement" />
              </div>
            </DateRangeFilter>
          </FilterCard>
        );

      /* ---------- Balance Sheet ---------- */
      case 'balance':
        return (
          <FilterCard>
            <div className="flex justify-end gap-2">
              <GenerateButton onClick={fetchBalanceSheet} />
              <PdfButton type="balanceSheet" />
            </div>
          </FilterCard>
        );

      /* ---------- Trial Balance ---------- */
      case 'trial':
        return (
          <FilterCard>
            <div className="flex flex-col sm:flex-row items-end gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodTo')}</label>
                <input type="date" value={trialDateTo} onChange={(e) => setTrialDateTo(e.target.value)} className={inputClass} />
              </div>
              <GenerateButton onClick={fetchTrialBalance} />
            </div>
          </FilterCard>
        );

      /* ---------- General Ledger ---------- */
      case 'ledger':
        return (
          <FilterCard>
            <div className="flex flex-col sm:flex-row items-end gap-3 flex-wrap">
              <div className="w-full sm:w-auto">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('selectAccount')}</label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className={inputClass + ' min-w-[200px]'}
                >
                  <option value="">{t('allAccounts')}</option>
                  {accountsList.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.account_code} — {acc.account_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodFrom')}</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className={inputClass} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('periodTo')}</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className={inputClass} />
              </div>
              <GenerateButton onClick={fetchGeneralLedger} />
            </div>
          </FilterCard>
        );

      /* ---------- Cash Flow Statement ---------- */
      case 'cashflow':
        return (
          <FilterCard>
            <DateRangeFilter from={cashflowFrom} to={cashflowTo} setFrom={setCashflowFrom} setTo={setCashflowTo}>
              <GenerateButton onClick={fetchCashFlow} />
            </DateRangeFilter>
          </FilterCard>
        );

      /* ---------- VAT Return ---------- */
      case 'vat':
        return (
          <FilterCard>
            <div className="flex flex-col sm:flex-row items-end gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('month')}</label>
                <select value={vatMonth} onChange={(e) => setVatMonth(Number(e.target.value))} className={inputClass + ' min-w-[140px]'}>
                  {MONTH_OPTIONS.map((m) => (
                    <option key={m.value} value={m.value}>{locale === 'ar' ? m.ar : t(m.label)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('year')}</label>
                <input
                  type="number"
                  value={vatYear}
                  onChange={(e) => setVatYear(Number(e.target.value))}
                  min={2020}
                  max={2035}
                  className={inputClass + ' w-[120px]'}
                />
              </div>
              <GenerateButton onClick={fetchVatReturn} />
            </div>
          </FilterCard>
        );

      /* ---------- AR/AP Aging ---------- */
      case 'aging':
        return (
          <FilterCard>
            <div className="flex justify-end">
              <GenerateButton onClick={fetchAging} />
            </div>
          </FilterCard>
        );

      default:
        return null;
    }
  };

  /* ================================================================ */
  /*  REPORT RENDER DISPATCHER                                          */
  /* ================================================================ */
  const renderActiveReport = () => {
    switch (activeTab) {
      case 'income': return renderIncomeStatement();
      case 'balance': return renderBalanceSheet();
      case 'trial': return renderTrialBalance();
      case 'ledger': return renderGeneralLedger();
      case 'cashflow': return renderCashFlow();
      case 'vat': return renderVatReturn();
      case 'aging': return renderAging();
      default: return null;
    }
  };

  /* ================================================================ */
  /*  MAIN RENDER                                                      */
  /* ================================================================ */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('financialReports')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('financialReportsDesc')}</p>
        </div>
      </div>

      {/* Tabs — 2-row layout */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-1">
        <div className="flex gap-1.5 flex-wrap">
          {row1Tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {row2Tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Per-tab filters */}
      {renderFilterSection()}

      {/* Active report content */}
      {renderActiveReport()}
    </div>
  );
}
