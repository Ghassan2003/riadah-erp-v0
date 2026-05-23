/**
 * Reports Center - Comprehensive PDF/Excel reports page for all ERP modules.
 * Features: 8 report categories, date filtering, PDF generation, Excel export,
 * accordion-style expand/collapse, dark mode, RTL Arabic layout.
 */

import { useState, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  pdfAPI,
  exportAPI,
  assetsAPI,
  contractsAPI,
  payrollAPI,
} from '../api';
import {
  FileText, Filter, Calendar, Loader2,
  ChevronDown, ChevronUp, Package, ShoppingCart,
  Users, Truck, Warehouse, Building2,
  Landmark, FileSignature, Receipt, ClipboardList,
  RefreshCw, BarChart3, FileSpreadsheet, TrendingUp,
  Briefcase, UserCog, Wallet, Calculator, CreditCard,
  Printer, ArrowUpDown, Archive, AlertTriangle,
} from 'lucide-react';
import toast from 'react-hot-toast';

/* ── Report Categories ── */
const REPORT_CATEGORIES = [
  {
    id: 'sales',
    icon: ShoppingCart,
    color: 'emerald',
    titleKey: 'sales',
    titleAr: 'المبيعات',
    descKey: 'totalSales',
    descAr: 'تقارير المبيعات وأوامر البيع والعملاء',
    reports: [
      {
        key: 'monthly_sales',
        titleAr: 'تقرير المبيعات الشهري',
        descAr: 'ملخص المبيعات الشهرية مع التفاصيل والأرقام',
        icon: BarChart3,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.moduleReport('sales', params),
        filename: 'monthly_sales_report.pdf',
      },
      {
        key: 'sales_orders',
        titleAr: 'تقرير أوامر البيع',
        descAr: 'تفاصيل جميع أوامر البيع وحالاتها',
        icon: Receipt,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.moduleReport('sales', params),
        filename: 'sales_orders_report.pdf',
      },
      {
        key: 'customers_report',
        titleAr: 'تقرير العملاء',
        descAr: 'قائمة العملاء وتفاصيل حساباتهم',
        icon: Users,
        apiType: 'excel',
        apiFn: () => exportAPI.customers(),
        filename: 'customers_report.xlsx',
      },
    ],
  },
  {
    id: 'purchases',
    icon: Truck,
    color: 'teal',
    titleKey: 'purchases',
    titleAr: 'المشتريات',
    descKey: 'totalPurchases',
    descAr: 'تقارير المشتريات والموردين',
    reports: [
      {
        key: 'monthly_purchases',
        titleAr: 'تقرير المشتريات الشهري',
        descAr: 'ملخص المشتريات الشهرية وتكلفتها',
        icon: TrendingUp,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.moduleReport('purchases', params),
        filename: 'monthly_purchases_report.pdf',
      },
      {
        key: 'suppliers_report',
        titleAr: 'تقرير الموردين',
        descAr: 'قائمة الموردين وتفاصيل حساباتهم',
        icon: Truck,
        apiType: 'excel',
        apiFn: () => exportAPI.suppliers(),
        filename: 'suppliers_report.xlsx',
      },
    ],
  },
  {
    id: 'inventory',
    icon: Warehouse,
    color: 'blue',
    titleKey: 'inventoryManagement',
    titleAr: 'المخزون',
    descKey: 'inventoryValue',
    descAr: 'تقارير المنتجات والمخزون وحركة البضاعة',
    reports: [
      {
        key: 'products_report',
        titleAr: 'تقرير المنتجات',
        descAr: 'قائمة جميع المنتجات وتفاصيلها ومواصفاتها',
        icon: Package,
        apiType: 'excel',
        apiFn: () => exportAPI.products(),
        filename: 'products_report.xlsx',
      },
      {
        key: 'low_stock_report',
        titleAr: 'تقرير المخزون المنخفض',
        descAr: 'المنتجات التي وصلت لحد أدنى المخزون',
        icon: AlertTriangle,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.moduleReport('inventory', params),
        filename: 'low_stock_report.pdf',
      },
      {
        key: 'stock_movement',
        titleAr: 'تقرير حركة المخزون',
        descAr: 'تتبع حركة الدخول والخروج للمخزون',
        icon: ArrowUpDown,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.moduleReport('inventory', params),
        filename: 'stock_movement_report.pdf',
      },
    ],
  },
  {
    id: 'hr',
    icon: UserCog,
    color: 'indigo',
    titleKey: 'hr',
    titleAr: 'الموارد البشرية',
    descKey: 'manageEmployees',
    descAr: 'تقارير الموظفين والحضور والإجازات',
    reports: [
      {
        key: 'employees_report',
        titleAr: 'تقرير الموظفين',
        descAr: 'قائمة الموظفين وبياناتهم الوظيفية',
        icon: Users,
        apiType: 'excel',
        apiFn: () => exportAPI.employees(),
        filename: 'employees_report.xlsx',
      },
      {
        key: 'attendance_report',
        titleAr: 'تقرير الحضور',
        descAr: 'سجل الحضور والانصراف لجميع الموظفين',
        icon: ClipboardList,
        apiType: 'excel',
        apiFn: (params) => exportAPI.attendance(params),
        filename: 'attendance_report.xlsx',
      },
      {
        key: 'leaves_report',
        titleAr: 'تقرير الإجازات',
        descAr: 'تفاصيل إجازات الموظفين وحالاتها',
        icon: FileSignature,
        apiType: 'excel',
        apiFn: () => exportAPI.leaves(),
        filename: 'leaves_report.xlsx',
      },
    ],
  },
  {
    id: 'accounting',
    icon: Landmark,
    color: 'yellow',
    titleKey: 'financialReports',
    titleAr: 'المالية',
    descKey: 'finance',
    descAr: 'قائمة الدخل والميزانية والتدفقات النقدية',
    reports: [
      {
        key: 'income_statement',
        titleAr: 'قائمة الدخل',
        descAr: 'الإيرادات والمصروفات وصافي الربح',
        icon: TrendingUp,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.enhancedIncome(params),
        filename: 'income_statement.pdf',
      },
      {
        key: 'balance_sheet',
        titleAr: 'الميزانية العمومية',
        descAr: 'الأصول والالتزامات وحقوق الملكية',
        icon: Calculator,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.enhancedBalance(params),
        filename: 'balance_sheet.pdf',
      },
      {
        key: 'cash_flow',
        titleAr: 'تقرير التدفقات النقدية',
        descAr: 'التدفقات النقدية التشغيلية والاستثمارية',
        icon: Wallet,
        apiType: 'pdf',
        apiFn: (params) => pdfAPI.cashFlow(params),
        filename: 'cash_flow_statement.pdf',
      },
    ],
  },
  {
    id: 'contracts',
    icon: FileSignature,
    color: 'purple',
    titleKey: 'contracts',
    titleAr: 'عقود',
    descKey: 'contracts',
    descAr: 'تقارير العقود والمراحل الزمنية',
    reports: [
      {
        key: 'contracts_report',
        titleAr: 'تقرير العقود',
        descAr: 'ملخص العقود وحالاتها وقيمها',
        icon: FileText,
        apiType: 'excel',
        apiFn: () => contractsAPI.export(),
        filename: 'contracts_report.xlsx',
      },
      {
        key: 'milestones_report',
        titleAr: 'تقرير المراحل',
        descAr: 'حالة مراحل تنفيذ العقود والإنجاز',
        icon: ClipboardList,
        apiType: 'excel',
        apiFn: () => contractsAPI.export(),
        filename: 'milestones_report.xlsx',
      },
    ],
  },
  {
    id: 'assets',
    icon: Building2,
    color: 'cyan',
    titleKey: 'assets',
    titleAr: 'الأصول',
    descKey: 'totalAssets',
    descAr: 'تقارير الأصول الثابتة والإهلاك',
    reports: [
      {
        key: 'fixed_assets',
        titleAr: 'تقرير الأصول الثابتة',
        descAr: 'قائمة الأصول الثابتة وتفاصيلها',
        icon: Archive,
        apiType: 'excel',
        apiFn: () => assetsAPI.export(),
        filename: 'fixed_assets_report.xlsx',
      },
      {
        key: 'depreciation',
        titleAr: 'تقرير الإهلاك',
        descAr: 'جدول إهلاك الأصول الثابتة',
        icon: CreditCard,
        apiType: 'excel',
        apiFn: () => assetsAPI.export(),
        filename: 'depreciation_report.xlsx',
      },
    ],
  },
  {
    id: 'payroll',
    icon: Briefcase,
    color: 'rose',
    titleKey: 'payroll',
    titleAr: 'الرواتب',
    descKey: 'totalSalaries',
    descAr: 'كشوف الرواتب والسلف والقروض',
    reports: [
      {
        key: 'payroll_sheet',
        titleAr: 'كشف الرواتب',
        descAr: 'تفاصيل رواتب الموظفين والخصومات',
        icon: Receipt,
        apiType: 'excel',
        apiFn: () => payrollAPI.export(),
        filename: 'payroll_sheet.xlsx',
      },
      {
        key: 'advances_loans',
        titleAr: 'تقرير السلف والقروض',
        descAr: 'سجل السلف والقروض والاقتطاعات',
        icon: CreditCard,
        apiType: 'excel',
        apiFn: () => payrollAPI.export(),
        filename: 'advances_loans_report.xlsx',
      },
    ],
  },
];

/* ── Color Map for category cards ── */
const colorMap = {
  emerald: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    text: 'text-emerald-600 dark:text-emerald-400',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-emerald-600',
    border: 'border-emerald-200 dark:border-emerald-800',
    hoverBorder: 'hover:border-emerald-300 dark:hover:border-emerald-700',
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  },
  teal: {
    bg: 'bg-teal-50 dark:bg-teal-900/20',
    text: 'text-teal-600 dark:text-teal-400',
    iconBg: 'bg-gradient-to-br from-teal-500 to-teal-600',
    border: 'border-teal-200 dark:border-teal-800',
    hoverBorder: 'hover:border-teal-300 dark:hover:border-teal-700',
    badge: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
  },
  blue: {
    bg: 'bg-riadah-50 dark:bg-riadah-900/20',
    text: 'text-accent-500 dark:text-accent-400',
    iconBg: 'bg-gradient-to-br from-riadah-400 to-riadah-500',
    border: 'border-riadah-200 dark:border-riadah-800',
    hoverBorder: 'hover:border-riadah-300 dark:hover:border-blue-700',
    badge: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300',
  },
  indigo: {
    bg: 'bg-indigo-50 dark:bg-indigo-900/20',
    text: 'text-indigo-600 dark:text-indigo-400',
    iconBg: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
    border: 'border-indigo-200 dark:border-indigo-800',
    hoverBorder: 'hover:border-indigo-300 dark:hover:border-indigo-700',
    badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
  },
  yellow: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    text: 'text-amber-600 dark:text-amber-400',
    iconBg: 'bg-gradient-to-br from-amber-500 to-amber-600',
    border: 'border-amber-200 dark:border-amber-800',
    hoverBorder: 'hover:border-amber-300 dark:hover:border-amber-700',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    text: 'text-purple-600 dark:text-purple-400',
    iconBg: 'bg-gradient-to-br from-purple-500 to-purple-600',
    border: 'border-purple-200 dark:border-purple-800',
    hoverBorder: 'hover:border-purple-300 dark:hover:border-purple-700',
    badge: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  },
  cyan: {
    bg: 'bg-cyan-50 dark:bg-cyan-900/20',
    text: 'text-cyan-600 dark:text-cyan-400',
    iconBg: 'bg-gradient-to-br from-cyan-500 to-cyan-600',
    border: 'border-cyan-200 dark:border-cyan-800',
    hoverBorder: 'hover:border-cyan-300 dark:hover:border-cyan-700',
    badge: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
  },
  rose: {
    bg: 'bg-rose-50 dark:bg-rose-900/20',
    text: 'text-rose-600 dark:text-rose-400',
    iconBg: 'bg-gradient-to-br from-rose-500 to-rose-600',
    border: 'border-rose-200 dark:border-rose-800',
    hoverBorder: 'hover:border-rose-300 dark:hover:border-rose-700',
    badge: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300',
  },
};

export default function ReportsCenterPage() {
  const { t, locale } = useI18n();
  const { user } = useAuth();

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [expandedCategory, setExpandedCategory] = useState('sales');
  const [loadingReport, setLoadingReport] = useState(null);

  const isDark = document.documentElement.classList.contains('dark');

  /* ── Toggle category accordion ── */
  const toggleCategory = useCallback((id) => {
    setExpandedCategory((prev) => (prev === id ? null : id));
  }, []);

  /* ── Get date params for API calls ── */
  const getDateParams = useCallback(() => {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    return params;
  }, [dateFrom, dateTo]);

  /* ── Generic download handler (blob) ── */
  const downloadReport = useCallback(async (report) => {
    const loadingKey = `${report.key}_${Date.now()}`;
    setLoadingReport(loadingKey);
    try {
      const params = getDateParams();
      let response;

      if (report.apiType === 'pdf') {
        response = await report.apiFn(params);
      } else {
        // Excel exports typically don't use date params (except attendance)
        response = await report.apiFn(params);
      }

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers?.['content-disposition'];
      let filename = report.filename;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=(?:UTF-8''|"?)([^";\n]+)/i);
        if (match) filename = decodeURIComponent(match[1].replace(/"/g, ''));
      }

      const mimeType = report.apiType === 'pdf'
        ? 'application/pdf'
        : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

      const blob = new Blob([response.data], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('تم تحميل التقرير بنجاح');
    } catch (error) {
      console.error('Report download error:', error);
      toast.error('فشل تحميل التقرير، يرجى المحاولة لاحقاً');
    } finally {
      setLoadingReport(null);
    }
  }, [getDateParams]);

  /* ── Count total reports ── */
  const totalReports = REPORT_CATEGORIES.reduce((sum, cat) => sum + cat.reports.length, 0);

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* ── Loading Overlay ── */}
      {loadingReport && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4 min-w-[280px]">
            <div className="relative">
              <Loader2 className="w-12 h-12 animate-spin text-accent-500" />
              <div className="absolute inset-0 w-12 h-12 rounded-full border-4 border-riadah-200 dark:border-riadah-800 animate-ping opacity-20" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-gray-800 dark:text-gray-100 text-sm">{t('reportGenerating') || 'جاري إنشاء التقرير...'}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('pleaseWait') || 'يرجى الانتظار'}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2.5">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-riadah-400 to-indigo-600 flex items-center justify-center shadow-sm">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            {t('reportsCenterTitle') || 'مركز التقارير'}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('reportsCenterDesc') || 'إنشاء وتصدير التقارير المتنوعة'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
            {REPORT_CATEGORIES.length} {t('categories') || 'أقسام'}
          </span>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
            {totalReports} {t('reports') || 'تقارير'}
          </span>
        </div>
      </div>

      {/* ── Date Filter Bar ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div className="flex flex-wrap items-end gap-3 sm:gap-4">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">{t('dateRange') || 'النطاق الزمني'}</span>
          </div>
          <div className="flex-1 min-w-[160px] sm:min-w-[180px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('from') || 'من'}</label>
            <div className="relative">
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full pl-3 pr-10 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 text-sm transition-colors"
              />
            </div>
          </div>
          <div className="flex-1 min-w-[160px] sm:min-w-[180px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('to') || 'إلى'}</label>
            <div className="relative">
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full pl-3 pr-10 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 text-sm transition-colors"
              />
            </div>
          </div>
          {(dateFrom || dateTo) && (
            <button
              onClick={() => { setDateFrom(''); setDateTo(''); }}
              className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3 h-3" />
              {t('clearing') || 'مسح'}
            </button>
          )}
        </div>
      </div>

      {/* ── Report Categories Grid ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {REPORT_CATEGORIES.map((category) => {
          const colors = colorMap[category.color] || colorMap.blue;
          const isExpanded = expandedCategory === category.id;
          const CategoryIcon = category.icon;

          return (
            <div
              key={category.id}
              className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border transition-all duration-200 ${
                isExpanded
                  ? `${colors.border} shadow-md ring-1 ring-offset-1 ${isDark ? 'ring-offset-gray-900 ring-gray-700' : 'ring-offset-white ring-gray-200'}`
                  : 'border-gray-100 dark:border-gray-700 hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600'
              }`}
            >
              {/* Category Header (Accordion Toggle) */}
              <button
                onClick={() => toggleCategory(category.id)}
                className="w-full flex items-center justify-between p-4 text-right transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30 rounded-t-xl"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl ${colors.iconBg} flex items-center justify-center text-white shadow-sm flex-shrink-0`}>
                    <CategoryIcon className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">
                      {t(category.titleKey) || category.titleAr}
                    </h3>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                      {category.descAr}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 mr-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${colors.badge}`}>
                    {category.reports.length}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  )}
                </div>
              </button>

              {/* Expanded: Report Items */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2.5">
                  <div className="border-t border-gray-100 dark:border-gray-700 pt-3" />
                  {category.reports.map((report) => {
                    const ReportIcon = report.icon || FileText;
                    const isLoading = loadingReport && loadingReport.startsWith(report.key);
                    const isPDF = report.apiType === 'pdf';

                    return (
                      <div
                        key={report.key}
                        className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-150 group ${
                          colors.border
                        } hover:shadow-sm ${colors.hoverBorder} bg-gray-50/50 dark:bg-gray-700/20`}
                      >
                        {/* Report Icon */}
                        <div className={`w-9 h-9 rounded-lg ${colors.bg} flex items-center justify-center flex-shrink-0 transition-colors group-hover:scale-105`}>
                          <ReportIcon className={`w-4 h-4 ${colors.text}`} />
                        </div>

                        {/* Report Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                            {report.titleAr}
                          </h4>
                          <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate mt-0.5">
                            {report.descAr}
                          </p>
                        </div>

                        {/* Download Button */}
                        <button
                          onClick={() => downloadReport(report)}
                          disabled={isLoading}
                          className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all active:scale-95 ${
                            isPDF
                              ? 'bg-riadah-50 dark:bg-riadah-900/20 hover:bg-riadah-100 dark:hover:bg-riadah-900/40 text-riadah-700 dark:text-accent-400 disabled:opacity-50'
                              : 'bg-emerald-50 dark:bg-emerald-900/20 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 disabled:opacity-50'
                          }`}
                          title={isPDF ? 'تحميل PDF' : 'تحميل Excel'}
                        >
                          {isLoading ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <>
                              {isPDF ? (
                                <FileText className="w-3.5 h-3.5" />
                              ) : (
                                <FileSpreadsheet className="w-3.5 h-3.5" />
                              )}
                            </>
                          )}
                          <span className="hidden sm:inline">{isPDF ? 'PDF' : 'Excel'}</span>
                          {isLoading && (
                            <span className="hidden sm:inline mr-1">...</span>
                          )}
                        </button>
                      </div>
                    );
                  })}

                  {/* Download All Hint */}
                  <div className="flex items-center justify-center pt-1">
                    <p className="text-[10px] text-gray-400 dark:text-gray-500">
                      {isDark ? '☀' : '🌙'} {category.reports.length} {t('generatedReports') || 'تقرير متاح'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Quick Stats Footer ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: t('sales') || 'المبيعات', count: REPORT_CATEGORIES.find(c => c.id === 'sales')?.reports.length || 0, color: colorMap.emerald, icon: ShoppingCart },
            { label: t('purchases') || 'المشتريات', count: REPORT_CATEGORIES.find(c => c.id === 'purchases')?.reports.length || 0, color: colorMap.teal, icon: Truck },
            { label: t('financialReports') || 'المالية', count: REPORT_CATEGORIES.find(c => c.id === 'accounting')?.reports.length || 0, color: colorMap.yellow, icon: Landmark },
            { label: t('payroll') || 'الرواتب', count: REPORT_CATEGORIES.find(c => c.id === 'payroll')?.reports.length || 0, color: colorMap.rose, icon: Briefcase },
          ].map((stat, i) => {
            const StatIcon = stat.icon;
            return (
              <div key={i} className={`rounded-xl p-3 border transition-all ${stat.color.bg} ${stat.color.border}`}>
                <div className="flex items-center gap-2 mb-1">
                  <StatIcon className={`w-4 h-4 ${stat.color.text}`} />
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{stat.label}</span>
                </div>
                <p className={`text-lg font-bold ${stat.color.text}`}>{stat.count} {t('reports') || 'تقرير'}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Footer Info ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs text-gray-400 dark:text-gray-500 px-1">
        <div className="flex items-center gap-3 flex-wrap">
          <span>{t('erpSystem') || 'نظام ERP'} v5.0</span>
          <span className="hidden sm:inline">{t('user') || 'المستخدم'}: {user?.username}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Printer className="w-3.5 h-3.5" />
          <span>{t('reportsCenterDesc') || 'تقارير PDF و Excel متاحة للتحميل'}</span>
        </div>
      </div>
    </div>
  );
}
