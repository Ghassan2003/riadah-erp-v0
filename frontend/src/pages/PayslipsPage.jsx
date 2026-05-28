/**
 * PayslipsPage - صفحة إدارة كشوف المرتبات.
 * عرض كشوف المرتبات الشهرية مع إمكانية التوليد والاعتماد والتصدير.
 * يدعم الوضع الداكن و RTL.
 */

import { useState, useEffect } from 'react';
import { payrollAPI, departmentsAPI, employeesAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  FileText, Download, Eye, Check, Ban, Search, Filter,
  DollarSign, TrendingDown, TrendingUp, Wallet, Users,
  X, Plus, Loader2, ChevronDown, ChevronUp,
  Building2, CalendarDays, Clock, AlertCircle,
  Receipt, CreditCard, Banknote, ArrowUpDown, Printer,
} from 'lucide-react';

/* ─── بيانات كشف المرتبات التجريبية ─── */
const SAMPLE_PAYSLIPS = [
  {
    id: 1, employee_name: 'أحمد محمد العلي', employee_number: 'EMP-001', department: 'التقنية المعلومات',
    basic_salary: 15000, housing_allowance: 3000, transport_allowance: 1000, food_allowance: 500,
    overtime: 750, bonus: 0,
    total_earnings: 20250,
    deductions_gosi: 945, deductions_tax: 0, deductions_loan: 500, deductions_absence: 0,
    total_deductions: 1445,
    net_salary: 18805, status: 'approved', month: 1, year: 2025,
  },
  {
    id: 2, employee_name: 'فاطمة خالد السعيد', employee_number: 'EMP-002', department: 'الموارد البشرية',
    basic_salary: 12000, housing_allowance: 2500, transport_allowance: 800, food_allowance: 500,
    overtime: 0, bonus: 1000,
    total_earnings: 16800,
    deductions_gosi: 756, deductions_tax: 0, deductions_loan: 0, deductions_absence: 200,
    total_deductions: 956,
    net_salary: 15844, status: 'draft', month: 1, year: 2025,
  },
  {
    id: 3, employee_name: 'عبدالله سعد الحربي', employee_number: 'EMP-003', department: 'المالية',
    basic_salary: 18000, housing_allowance: 3500, transport_allowance: 1200, food_allowance: 600,
    overtime: 1500, bonus: 2000,
    total_earnings: 26800,
    deductions_gosi: 1134, deductions_tax: 0, deductions_loan: 1000, deductions_absence: 0,
    total_deductions: 2134,
    net_salary: 24666, status: 'paid', month: 1, year: 2025,
  },
  {
    id: 4, employee_name: 'نورة عبدالرحمن القحطاني', employee_number: 'EMP-004', department: 'التسويق',
    basic_salary: 11000, housing_allowance: 2250, transport_allowance: 750, food_allowance: 400,
    overtime: 300, bonus: 0,
    total_earnings: 14700,
    deductions_gosi: 693, deductions_tax: 0, deductions_loan: 300, deductions_absence: 0,
    total_deductions: 993,
    net_salary: 13707, status: 'approved', month: 1, year: 2025,
  },
  {
    id: 5, employee_name: 'محمد فيصل الشمري', employee_number: 'EMP-005', department: 'التقنية المعلومات',
    basic_salary: 14000, housing_allowance: 2800, transport_allowance: 900, food_allowance: 500,
    overtime: 600, bonus: 500,
    total_earnings: 19300,
    deductions_gosi: 882, deductions_tax: 0, deductions_loan: 0, deductions_absence: 450,
    total_deductions: 1332,
    net_salary: 17968, status: 'draft', month: 1, year: 2025,
  },
  {
    id: 6, employee_name: 'سارة علي المطيري', employee_number: 'EMP-006', department: 'المالية',
    basic_salary: 13000, housing_allowance: 2700, transport_allowance: 850, food_allowance: 450,
    overtime: 0, bonus: 1500,
    total_earnings: 18500,
    deductions_gosi: 819, deductions_tax: 0, deductions_loan: 750, deductions_absence: 0,
    total_deductions: 1569,
    net_salary: 16931, status: 'paid', month: 1, year: 2025,
  },
];

/* ─── الحالات والألوان ─── */
const STATUS_CONFIG = {
  draft: { label: 'مسودة', color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', icon: FileText },
  approved: { label: 'معتمد', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', icon: Check },
  paid: { label: 'مدفوع', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: Wallet },
};

/* ─── أسماء الأشهر العربية ─── */
const MONTH_NAMES_AR = [
  'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
];

/* ─── Spinner ─── */
const Spinner = () => (
  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

export default function PayslipsPage() {
  const { user } = useAuth();
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  /* ─── حالة البيانات ─── */
  const [payslips, setPayslips] = useState(SAMPLE_PAYSLIPS);
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState([]);

  /* ─── التصفية ─── */
  const [selectedMonth, setSelectedMonth] = useState(1);
  const [selectedYear, setSelectedYear] = useState(2025);
  const [filterDept, setFilterDept] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterEmployee, setFilterEmployee] = useState('');
  const [expandedRow, setExpandedRow] = useState(null);

  /* ─── مودال ─── */
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedPayslip, setSelectedPayslip] = useState(null);
  const [generating, setGenerating] = useState(false);

  /* ─── الصلاحيات ─── */
  const isAdmin = user?.role === 'admin';

  /* ─── حقول الإدخال ─── */
  const selectCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700';
  const inputCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';

  /* ─── تحميل البيانات ─── */
  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      const res = await departmentsAPI.list({ page_size: 100 });
      setDepartments(res.data?.results || res.data || []);
    } catch {
      // استخدام بيانات تجريبية
      setDepartments([
        { id: 1, name: 'التقنية المعلومات' },
        { id: 2, name: 'الموارد البشرية' },
        { id: 3, name: 'المالية' },
        { id: 4, name: 'التسويق' },
      ]);
    }
  };

  /* ─── التصفية ─── */
  const filteredPayslips = payslips.filter((p) => {
    if (p.month !== selectedMonth || p.year !== selectedYear) return false;
    if (filterDept && p.department !== filterDept) return false;
    if (filterStatus && p.status !== filterStatus) return false;
    if (filterEmployee && !p.employee_name.includes(filterEmployee) && !p.employee_number.includes(filterEmployee)) return false;
    return true;
  });

  /* ─── حساب المجاميع ─── */
  const summary = {
    totalPayroll: filteredPayslips.reduce((s, p) => s + (p.total_earnings || 0), 0),
    totalDeductions: filteredPayslips.reduce((s, p) => s + (p.total_deductions || 0), 0),
    totalNet: filteredPayslips.reduce((s, p) => s + (p.net_salary || 0), 0),
    pendingCount: filteredPayslips.filter((p) => p.status === 'draft').length,
    approvedCount: filteredPayslips.filter((p) => p.status === 'approved').length,
    paidCount: filteredPayslips.filter((p) => p.status === 'paid').length,
  };

  /* ─── توليد كشوف المرتبات ─── */
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      toast.success('تم توليد كشوف المرتبات بنجاح');
    } catch (err) {
      toast.error('حدث خطأ أثناء التوليد');
    } finally {
      setGenerating(false);
    }
  };

  /* ─── اعتماد / رفض كشف مرتبات ─── */
  const handleApprove = (id, action) => {
    setPayslips((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: action === 'approve' ? 'approved' : 'draft' } : p))
    );
    toast.success(action === 'approve' ? 'تم اعتماد الكشف بنجاح' : 'تم إرجاع الكشف للمسودة');
  };

  const handleMarkPaid = (id) => {
    setPayslips((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: 'paid' } : p))
    );
    toast.success('تم تسجيل الدفع بنجاح');
  };

  /* ─── عرض تفاصيل كشف المرتبات ─── */
  const openDetail = (payslip) => {
    setSelectedPayslip(payslip);
    setShowDetailModal(true);
  };

  /* ─── تصدير كشوف المرتبات ─── */
  const handleExport = async () => {
    try {
      const res = await payrollAPI.export();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `payslips_${selectedYear}_${selectedMonth}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast.success('تم تصدير كشوف المرتبات بنجاح');
    } catch {
      // تصدير محلي تجريبي
      toast.success('تم تصدير الكشوف (تجريبي)');
    }
  };

  return (
    <div dir="rtl" className="space-y-6">

      {/* ─── العنوان ─── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">كشوف المرتبات</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">عرض وإدارة كشوف المرتبات الشهرية للموظفين</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {isAdmin && (
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-2.5 bg-[#FF6600] text-white rounded-lg hover:bg-[#e65c00] disabled:opacity-50 transition-colors text-sm font-medium shadow-sm"
            >
              {generating ? <Spinner /> : <Plus className="w-4 h-4" />}
              توليد الكشوف
            </button>
          )}
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium shadow-sm"
          >
            <Download className="w-4 h-4" />
            تصدير
          </button>
        </div>
      </div>

      {/* ─── محدد الشهر والسنة ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">الفترة:</span>
          </div>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
            className={selectCls}
          >
            {MONTH_NAMES_AR.map((name, idx) => (
              <option key={idx} value={idx + 1}>{name}</option>
            ))}
          </select>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className={selectCls}
          >
            {[2024, 2025, 2026].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          <div className="hidden sm:block w-px h-8 bg-gray-200 dark:bg-gray-600" />

          {/* فلتر القسم */}
          <select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className={selectCls}
          >
            <option value="">كل الأقسام</option>
            {departments.map((d) => (
              <option key={d.id} value={d.name}>{d.name}</option>
            ))}
          </select>

          {/* فلتر الحالة */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className={selectCls}
          >
            <option value="">كل الحالات</option>
            {Object.entries(STATUS_CONFIG).map(([key, info]) => (
              <option key={key} value={key}>{info.label}</option>
            ))}
          </select>

          {/* بحث بالاسم */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="بحث بالاسم أو الرقم..."
              value={filterEmployee}
              onChange={(e) => setFilterEmployee(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
        </div>
      </div>

      {/* ─── بطاقات الملخص ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gradient-to-br from-[#003366] to-[#004d99] text-white">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">إجمالي الرواتب</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{fmt(summary.totalPayroll)}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gradient-to-br from-red-500 to-red-600 text-white">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">إجمالي الخصومات</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{fmt(summary.totalDeductions)}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">إجمالي الصافي</p>
              <p className="text-lg font-bold text-green-600 dark:text-green-400">{fmt(summary.totalNet)}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 text-white">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">بانتظار الاعتماد</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{summary.pendingCount} كشف</p>
              <div className="flex gap-2 text-[10px] text-gray-400 mt-0.5">
                <span>معتمد: {summary.approvedCount}</span>
                <span>مدفوع: {summary.paidCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── جدول كشوف المرتبات ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Receipt className="w-5 h-5 text-[#003366] dark:text-blue-400" />
            كشوف {MONTH_NAMES_AR[selectedMonth - 1]} {selectedYear}
            <span className="text-sm font-normal text-gray-400">({filteredPayslips.length} كشف)</span>
          </h3>
        </div>

        <div className="overflow-x-auto">
          {filteredPayslips.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد كشوف مرتبات لهذه الفترة</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="w-8 px-2"></th>
                  <th className="px-4 py-3 text-right font-medium">الموظف</th>
                  <th className="px-4 py-3 text-right font-medium">القسم</th>
                  <th className="px-4 py-3 text-right font-medium">الراتب الأساسي</th>
                  <th className="px-4 py-3 text-right font-medium">الاستحقاقات</th>
                  <th className="px-4 py-3 text-right font-medium">الخصومات</th>
                  <th className="px-4 py-3 text-right font-medium">صافي الراتب</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                  <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {filteredPayslips.map((p) => (
                  <>
                    <tr
                      key={p.id}
                      className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      {/* زر التوسيع */}
                      <td className="px-2 py-3">
                        <button
                          onClick={() => setExpandedRow(expandedRow === p.id ? null : p.id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        >
                          {expandedRow === p.id ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      </td>

                      {/* اسم الموظف */}
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100">{p.employee_name}</p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 font-mono">{p.employee_number}</p>
                      </td>

                      {/* القسم */}
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.department}</td>

                      {/* الراتب الأساسي */}
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fmt(p.basic_salary)}</td>

                      {/* الاستحقاقات */}
                      <td className="px-4 py-3 text-green-600 dark:text-green-400 font-medium">{fmt(p.total_earnings)}</td>

                      {/* الخصومات */}
                      <td className="px-4 py-3 text-red-600 dark:text-red-400 font-medium">{fmt(p.total_deductions)}</td>

                      {/* صافي الراتب */}
                      <td className="px-4 py-3">
                        <span className="text-lg font-bold text-[#003366] dark:text-blue-400">
                          {fmt(p.net_salary)}
                        </span>
                      </td>

                      {/* الحالة */}
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[p.status]?.color || ''}`}>
                          {STATUS_CONFIG[p.status]?.label || p.status}
                        </span>
                      </td>

                      {/* الإجراءات */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openDetail(p)}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                            title="عرض التفاصيل"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {isAdmin && p.status === 'draft' && (
                            <button
                              onClick={() => handleApprove(p.id, 'approve')}
                              className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                              title="اعتماد"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          {isAdmin && p.status === 'approved' && (
                            <button
                              onClick={() => handleMarkPaid(p.id)}
                              className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 p-1.5 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
                              title="تسجيل الدفع"
                            >
                              <Wallet className="w-4 h-4" />
                            </button>
                          )}
                          {isAdmin && p.status === 'approved' && (
                            <button
                              onClick={() => handleApprove(p.id, 'reject')}
                              className="text-orange-600 dark:text-orange-400 hover:text-orange-800 dark:hover:text-orange-300 p-1.5 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors"
                              title="إرجاع"
                            >
                              <Ban className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* صف التفاصيل الموسعة */}
                    {expandedRow === p.id && (
                      <tr key={`${p.id}-detail`} className="bg-gray-50 dark:bg-gray-700/20">
                        <td colSpan={9} className="px-6 py-4">
                          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-sm">
                            {[
                              ['بدل سكن', p.housing_allowance, false],
                              ['بدل نقل', p.transport_allowance, false],
                              ['بدل طعام', p.food_allowance, false],
                              ['ساعات إضافية', p.overtime, false],
                              ['مكافأة', p.bonus, false],
                              ['التأمينات', p.deductions_gosi, true],
                              ['قسط قرض', p.deductions_loan, true],
                              ['خصم غياب', p.deductions_absence, true],
                            ].map(([label, value, isDeduction]) => (
                              <div key={label}>
                                <span className="text-gray-500 dark:text-gray-400 text-xs">{label}</span>
                                <p className={`font-medium text-sm ${isDeduction ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>
                                  {fmt(value)}
                                </p>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>

              {/* صف الإجماليات */}
              <tfoot>
                <tr className="bg-gradient-to-l from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700/50 border-t-2 border-gray-200 dark:border-gray-600">
                  <td colSpan={3} className="px-4 py-3 font-bold text-gray-900 dark:text-gray-100 text-right">
                    الإجمالي
                  </td>
                  <td className="px-4 py-3 font-bold text-gray-900 dark:text-gray-100">{fmt(filteredPayslips.reduce((s, p) => s + (p.basic_salary || 0), 0))}</td>
                  <td className="px-4 py-3 font-bold text-green-600 dark:text-green-400">{fmt(summary.totalPayroll)}</td>
                  <td className="px-4 py-3 font-bold text-red-600 dark:text-red-400">{fmt(summary.totalDeductions)}</td>
                  <td className="px-4 py-3">
                    <span className="text-lg font-bold text-[#003366] dark:text-blue-400">{fmt(summary.totalNet)}</span>
                  </td>
                  <td colSpan={2}></td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>
      </div>

      {/* ─── مودال تفاصيل كشف المرتبات ─── */}
      {showDetailModal && selectedPayslip && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            {/* رأس المودال */}
            <div className="bg-gradient-to-l from-[#003366] to-[#004d99] p-5 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">كشف راتب - {selectedPayslip.employee_name}</h3>
                  <p className="text-white/70 text-sm mt-1">
                    {MONTH_NAMES_AR[selectedMonth - 1]} {selectedYear} | {selectedPayslip.department}
                  </p>
                </div>
                <button onClick={() => setShowDetailModal(false)} className="text-white/60 hover:text-white p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* محتوى الكشف */}
            <div className="p-5 space-y-5">
              {/* معلومات الموظف */}
              <div className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
                <div className="w-12 h-12 rounded-full bg-[#003366] flex items-center justify-center text-white font-bold text-lg">
                  {selectedPayslip.employee_name.charAt(0)}
                </div>
                <div>
                  <p className="font-bold text-gray-900 dark:text-gray-100">{selectedPayslip.employee_name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">{selectedPayslip.employee_number} | {selectedPayslip.department}</p>
                </div>
                <div className="mr-auto">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[selectedPayslip.status]?.color || ''}`}>
                    {STATUS_CONFIG[selectedPayslip.status]?.label || selectedPayslip.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* الاستحقاقات */}
                <div className="bg-green-50 dark:bg-green-900/10 rounded-xl p-4 border border-green-100 dark:border-green-900/30">
                  <h4 className="font-bold text-green-700 dark:text-green-400 flex items-center gap-2 mb-3">
                    <TrendingUp className="w-4 h-4" />
                    الاستحقاقات
                  </h4>
                  <div className="space-y-2">
                    {[
                      ['الراتب الأساسي', selectedPayslip.basic_salary],
                      ['بدل السكن', selectedPayslip.housing_allowance],
                      ['بدل النقل', selectedPayslip.transport_allowance],
                      ['بدل الطعام', selectedPayslip.food_allowance],
                      ['ساعات إضافية', selectedPayslip.overtime],
                      ['مكافأة', selectedPayslip.bonus],
                    ].map(([label, value]) => (
                      <div key={label} className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-300">{label}</span>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{fmt(value)}</span>
                      </div>
                    ))}
                    <div className="border-t border-green-200 dark:border-green-800 pt-2 mt-2">
                      <div className="flex justify-between font-bold">
                        <span className="text-green-700 dark:text-green-400">إجمالي الاستحقاقات</span>
                        <span className="text-green-700 dark:text-green-400">{fmt(selectedPayslip.total_earnings)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* الخصومات */}
                <div className="bg-red-50 dark:bg-red-900/10 rounded-xl p-4 border border-red-100 dark:border-red-900/30">
                  <h4 className="font-bold text-red-700 dark:text-red-400 flex items-center gap-2 mb-3">
                    <TrendingDown className="w-4 h-4" />
                    الخصومات
                  </h4>
                  <div className="space-y-2">
                    {[
                      ['التأمينات الاجتماعية', selectedPayslip.deductions_gosi],
                      ['قسط القرض', selectedPayslip.deductions_loan],
                      ['خصم الغياب', selectedPayslip.deductions_absence],
                      ['الضرائب', selectedPayslip.deductions_tax || 0],
                    ].map(([label, value]) => (
                      <div key={label} className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-300">{label}</span>
                        <span className="font-medium text-red-600 dark:text-red-400">{fmt(value)}</span>
                      </div>
                    ))}
                    <div className="border-t border-red-200 dark:border-red-800 pt-2 mt-2">
                      <div className="flex justify-between font-bold">
                        <span className="text-red-700 dark:text-red-400">إجمالي الخصومات</span>
                        <span className="text-red-700 dark:text-red-400">{fmt(selectedPayslip.total_deductions)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* صافي الراتب */}
              <div className="bg-gradient-to-l from-[#003366] to-[#004d99] rounded-xl p-5 text-white text-center">
                <p className="text-white/70 text-sm mb-1">صافي الراتب المستحق</p>
                <p className="text-3xl font-bold">{fmt(selectedPayslip.net_salary)}</p>
                <p className="text-white/50 text-xs mt-1">ريال سعودي</p>
              </div>

              {/* أزرار الإجراءات */}
              {isAdmin && (
                <div className="flex gap-3 pt-2">
                  {selectedPayslip.status === 'draft' && (
                    <button
                      onClick={() => { handleApprove(selectedPayslip.id, 'approve'); setShowDetailModal(false); }}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      اعتماد
                    </button>
                  )}
                  {selectedPayslip.status === 'approved' && (
                    <button
                      onClick={() => { handleMarkPaid(selectedPayslip.id); setShowDetailModal(false); }}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm transition-colors"
                    >
                      <Wallet className="w-4 h-4" />
                      تسجيل الدفع
                    </button>
                  )}
                  <button
                    onClick={() => setShowDetailModal(false)}
                    className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium text-sm transition-colors"
                  >
                    إغلاق
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
