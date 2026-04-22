/**
 * Payroll Management page - HR module.
 * Manage payroll periods, payslips, advances/loans, and end-of-service benefits.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { payrollAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Download, CalendarDays,
  Wallet, Banknote, Gift, FileText, ChevronDown, ChevronUp,
  Calculator, Users, TrendingUp, Clock, RefreshCw,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  paid: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  closed: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  unpaid: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  partially_paid: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
};
const SL = {
  draft: 'مسودة', processing: 'قيد المعالجة', paid: 'مدفوع', closed: 'مقفل',
  pending: 'معلّق', approved: 'معتمد', rejected: 'مرفوض', active: 'نشط',
  unpaid: 'غير مدفوع', partially_paid: 'مدفوع جزئياً',
};

const TABS = [
  { id: 'periods', name: 'فترات الرواتب', icon: CalendarDays },
  { id: 'payslips', name: 'كشف الرواتب', icon: FileText },
  { id: 'advances', name: 'السلف والقروض', icon: Banknote },
  { id: 'endofservice', name: 'مكافآت نهاية الخدمة', icon: Gift },
];
const STATS = [
  { key: 'total_periods', label: 'إجمالي الفترات', icon: CalendarDays, color: 'from-riadah-400 to-riadah-500' },
  { key: 'active_period_name', label: 'الفترة النشطة', icon: Clock, color: 'from-emerald-500 to-emerald-600' },
  { key: 'total_paid_this_month', label: 'إجمالي المدفوعات', icon: TrendingUp, color: 'from-purple-500 to-purple-600' },
  { key: 'employees_count', label: 'عدد الموظفين', icon: Users, color: 'from-amber-500 to-amber-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function PayrollPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('periods');
  const [sub, setSub] = useState('adv');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [periods, setPeriods] = useState([]);
  const [records, setRecords] = useState([]);
  const [selPeriod, setSelPeriod] = useState(null);
  const [advances, setAdvances] = useState([]);
  const [loans, setLoans] = useState([]);
  const [eosList, setEosList] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');
  const [expRow, setExpRow] = useState(null);

  const [modals, setModals] = useState({ period: false, payslip: false, advance: false, loan: false });
  const [selRec, setSelRec] = useState(null);
  const [pForm, setPForm] = useState({ name: '', month: '', year: '' });
  const [psForm, setPsForm] = useState({ basic_salary: '', housing_allowance: '', transport_allowance: '', food_allowance: '', overtime: '', deductions: '', absences_deduction: '', loan_deduction: '', advance_deduction: '', tax: '', social_insurance: '', notes: '' });
  const [advForm, setAdvForm] = useState({ employee: '', amount: '', purpose: '' });
  const [lnForm, setLnForm] = useState({ employee: '', amount: '', months: '', monthly_installment: '' });

  const isAdmin = JSON.parse(localStorage.getItem('user') || '{}')?.role === 'admin';
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await payrollAPI.getStats()).data); } catch {} })(); (async () => { setLd(true); try { setPeriods((await payrollAPI.getPeriods({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل فترات الرواتب'); } finally { setLd(false); } })(); }, [search, sFilter]);

  useEffect(() => { if (tab === 'payslips' && selPeriod) { (async () => { setLd(true); try { setRecords((await payrollAPI.getRecords({ period: selPeriod.id })).data.results || []); } catch { toast.error('خطأ في تحميل كشف الرواتب'); } finally { setLd(false); } })(); } }, [tab, selPeriod]);

  useEffect(() => { if (tab === 'advances') { (async () => { setLd(true); try { const fn = sub === 'adv' ? payrollAPI.getAdvances : payrollAPI.getLoans; const res = (await fn({ search, status: sFilter })).data.results || []; sub === 'adv' ? setAdvances(res) : setLoans(res); } catch { toast.error('خطأ في التحميل'); } finally { setLd(false); } })(); } }, [tab, sub, search, sFilter]);

  useEffect(() => { if (tab === 'endofservice') { (async () => { setLd(true); try { setEosList((await payrollAPI.getEndOfService({ search })).data.results || []); } catch { toast.error('خطأ في التحميل'); } finally { setLd(false); } })(); } }, [tab, search]);

  const hCreatePeriod = async (e) => { e.preventDefault(); setSv(true); try { await payrollAPI.createPeriod({ ...pForm, year: +pForm.year, month: +pForm.month }); toast.success('تم إنشاء فترة الرواتب بنجاح'); setModals({ ...modals, period: false }); setPForm({ name: '', month: '', year: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hGenerate = async (id) => { try { await payrollAPI.generatePayroll(id); toast.success('تم إنشاء كشف الرواتب بنجاح'); } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); } };
  const hClose = async (id) => { try { await payrollAPI.closePeriod(id); toast.success('تم إقفال الفترة بنجاح'); } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); } };
  const hPay = async (id) => { try { await payrollAPI.payRecord(id); toast.success('تم صرف الراتب بنجاح'); setRecords((await payrollAPI.getRecords({ period: selPeriod.id })).data.results || []); } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); } };
  const hSavePayslip = async (e) => { e.preventDefault(); if (!selRec) return; setSv(true); try { const d = {}; Object.entries(psForm).forEach(([k, v]) => { d[k] = parseFloat(v) || 0; }); await payrollAPI.updateRecord(selRec.id, d); toast.success('تم التحديث بنجاح'); setModals({ ...modals, payslip: false }); } catch { toast.error('خطأ في التحديث'); } finally { setSv(false); } };
  const hCreateAdv = async (e) => { e.preventDefault(); setSv(true); try { await payrollAPI.createAdvance({ ...advForm, amount: +advForm.amount, employee: +advForm.employee }); toast.success('تم إنشاء السلفة'); setModals({ ...modals, advance: false }); setAdvForm({ employee: '', amount: '', purpose: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateLn = async (e) => { e.preventDefault(); setSv(true); try { await payrollAPI.createLoan({ ...lnForm, amount: +lnForm.amount, months: +lnForm.months, monthly_installment: +lnForm.monthly_installment, employee: +lnForm.employee }); toast.success('تم إنشاء القرض'); setModals({ ...modals, loan: false }); setLnForm({ employee: '', amount: '', months: '', monthly_installment: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hApproveAdv = async (id, action) => { try { await payrollAPI.approveAdvance(id, { action }); toast.success(action === 'approve' ? 'تمت الموافقة' : 'تم الرفض'); } catch { toast.error('خطأ'); } };
  const hApproveLn = async (id, action) => { try { await payrollAPI.approveLoan(id, { action }); toast.success(action === 'approve' ? 'تمت الموافقة' : 'تم الرفض'); } catch { toast.error('خطأ'); } };
  const hCalcEos = async (item) => { try { await payrollAPI.createEndOfService({ employee: item.employee }); toast.success('تم حساب مكافأة نهاية الخدمة'); } catch { toast.error('خطأ في الحساب'); } };
  const hExport = async () => { try { const r = await payrollAPI.export(); const u = window.URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = u; a.download = 'payroll.xlsx'; document.body.appendChild(a); a.click(); a.remove(); toast.success('تم التصدير'); } catch { toast.error('خطأ في التصدير'); } };

  const openPsEdit = (r) => { setSelRec(r); setPsForm({ basic_salary: r.basic_salary || '', housing_allowance: r.housing_allowance || '', transport_allowance: r.transport_allowance || '', food_allowance: r.food_allowance || '', overtime: r.overtime || '', deductions: r.total_deductions || '', absences_deduction: r.absences_deduction || '', loan_deduction: r.loan_deduction || '', advance_deduction: r.advance_deduction || '', tax: r.tax || '', social_insurance: r.social_insurance || '', notes: r.notes || '' }); setModals({ ...modals, payslip: true }); };

  const Modal = ({ k, title, children }) => modals[k] && (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
          <button onClick={() => setModals({ ...modals, [k]: false })} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
        </div>
        {children}
      </div>
    </div>
  );
  const Btn = ({ onClick, disabled, children, cls = 'bg-riadah-500 hover:bg-riadah-600', full = true }) => (
    <button type={full ? 'submit' : 'button'} onClick={onClick} disabled={disabled || sv}
      className={`${full ? 'flex-1' : ''} px-4 py-2.5 ${cls} text-white rounded-lg transition-colors disabled:opacity-50 font-medium text-sm`}>
      {sv && full ? <span className="flex items-center justify-center gap-2"><Sp /> جاري المعالجة...</span> : children}
    </button>
  );
  const CancelBtn = ({ k }) => <Btn full={false} onClick={() => setModals({ ...modals, [k]: false })} cls="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600">إلغاء</Btn>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة الرواتب</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة فترات الرواتب، كشوف المرتبات، السلف والقروض، ومكافآت نهاية الخدمة</p>
        </div>
        <div className="flex gap-2">
          {tab === 'periods' && isAdmin && <button onClick={() => setModals({ ...modals, period: true })} className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> فترة جديدة</button>}
          {tab === 'advances' && isAdmin && <button onClick={() => setModals({ ...modals, [sub === 'adv' ? 'advance' : 'loan']: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> {sub === 'adv' ? 'سلفة جديدة' : 'قرض جديد'}</button>}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{key === 'total_paid_this_month' ? fm(stats[key]) : (stats[key] || '-')}</p></div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {TABS.map(t => { const I = t.icon; return <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-riadah-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}><I className="w-4 h-4" /> {t.name}</button>; })}
      </div>

      {/* Search */}
      {tab !== 'payslips' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
            </div>
            {(tab === 'periods' || tab === 'advances') && (
              <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
                <option value="">كل الحالات</option>
                {(tab === 'periods' ? ['draft','processing','paid','closed'] : ['pending','approved','rejected']).map(s => <option key={s} value={s}>{SL[s]}</option>)}
              </select>
            )}
          </div>
        </div>
      )}

      {/* ─── Periods Tab ─── */}
      {tab === 'periods' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : periods.length === 0 ? <div className="p-12 text-center"><CalendarDays className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد فترات رواتب</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>الشهر / السنة</Th><Th>الحالة</Th><Th>عدد الموظفين</Th><Th>الصافي الإجمالي</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{periods.map(p => (
                <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{p.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.month}/{p.year}</td>
                  <td className="px-4 py-3"><span className={badge(p.status)}>{SL[p.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.total_employees || 0}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(p.total_net)}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelPeriod(p); setTab('payslips'); }} className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {p.status === 'draft' && <button onClick={() => hGenerate(p.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="توليد"><RefreshCw className="w-4 h-4" /></button>}
                    {(p.status === 'processing' || p.status === 'paid') && <button onClick={() => hClose(p.id)} className="text-purple-600 dark:text-purple-400 p-1.5 rounded hover:bg-purple-50 dark:hover:bg-purple-900/20" title="إقفال"><Check className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Payslips Tab ─── */}
      {tab === 'payslips' && (!selPeriod ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm border border-gray-100 dark:border-gray-700 text-center">
          <CalendarDays className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500">اختر فترة رواتب من تبويب فترات الرواتب لعرض الكشف</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 flex-wrap gap-3">
            <div className="flex items-center gap-2"><span className="text-sm text-gray-600 dark:text-gray-300">فترة:</span><span className="font-semibold text-gray-900 dark:text-gray-100">{selPeriod.name}</span><span className={badge(selPeriod.status)}>{SL[selPeriod.status]}</span></div>
            <button onClick={hExport} className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"><Download className="w-4 h-4" /> تصدير إكسل</button>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : records.length === 0 ? <div className="p-12 text-center"><FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد سجلات</p></div> : (
              <div className="overflow-x-auto"><table className="w-full text-sm">
                <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="w-8 px-2"></th><Th>الموظف</Th><Th>الرقم</Th><Th>القسم</Th><Th>الراتب الأساسي</Th><Th>الاستحقاقات</Th><Th>الخصومات</Th><Th>صافي الراتب</Th><Th>حالة الدفع</Th><Th>الإجراءات</Th>
                </tr></thead>
                <tbody>{records.map(r => (<>
                  <tr key={r.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-2 py-3"><button onClick={() => setExpRow(expRow === r.id ? null : r.id)} className="text-gray-400 hover:text-gray-600">{expRow === r.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</button></td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{r.employee_name}</td>
                    <td className="px-4 py-3 font-mono text-gray-500">{r.employee_number}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{r.department || '-'}</td>
                    <td className="px-4 py-3">{fm(r.basic_salary)}</td>
                    <td className="px-4 py-3 text-green-600 dark:text-green-400 font-medium">{fm(r.total_earnings)}</td>
                    <td className="px-4 py-3 text-red-600 dark:text-red-400 font-medium">{fm(r.total_deductions)}</td>
                    <td className="px-4 py-3 text-accent-500 dark:text-accent-400 font-bold">{fm(r.net_salary)}</td>
                    <td className="px-4 py-3"><span className={badge(r.payment_status)}>{SL[r.payment_status]}</span></td>
                    <td className="px-4 py-3"><div className="flex gap-1">
                      <button onClick={() => openPsEdit(r)} className="text-accent-500 dark:text-accent-400 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/20"><Eye className="w-4 h-4" /></button>
                      {r.payment_status === 'unpaid' && <button onClick={() => hPay(r.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="صرف"><Wallet className="w-4 h-4" /></button>}
                    </div></td>
                  </tr>
                  {expRow === r.id && <tr key={`${r.id}-d`} className="bg-gray-50 dark:bg-gray-700/20"><td colSpan={10} className="px-6 py-4"><div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    {[['بدل سكن', r.housing_allowance], ['بدل نقل', r.transport_allowance], ['بدل طعام', r.food_allowance], ['ساعات إضافية', r.overtime], ['خصم غياب', r.absences_deduction], ['خصم قروض', r.loan_deduction], ['خصم سلف', r.advance_deduction], ['الضرائب', r.tax]].map(([l, v]) => (
                      <div key={l}><span className="text-gray-500">{l}:</span><p className={`font-medium ${l.startsWith('خصم') ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>{fm(v)}</p></div>
                    ))}
                  </div></td></tr>}
                </>))}</tbody>
              </table></div>
            )}
          </div>
        </div>
      ))}

      {/* ─── Advances & Loans Tab ─── */}
      {tab === 'advances' && (
        <div className="space-y-4">
          <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
            {[['adv', 'السلف'], ['loans', 'القروض']].map(([id, name]) => (
              <button key={id} onClick={() => setSub(id)} className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${sub === id ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>{name}</button>
            ))}
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : (sub === 'adv' ? advances : loans).length === 0 ? <div className="p-12 text-center"><Banknote className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد بيانات</p></div> : (
              <div className="overflow-x-auto"><table className="w-full text-sm">
                <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  {sub === 'adv' ? <><Th>الموظف</Th><Th>المبلغ</Th><Th>الغرض</Th><Th>التاريخ</Th><Th>الحالة</Th><Th>الإجراءات</Th></> : <><Th>الموظف</Th><Th>مبلغ القرض</Th><Th>القسط الشهري</Th><Th>الأشهر المتبقية</Th><Th>المبلغ المتبقي</Th><Th>الحالة</Th><Th>الإجراءات</Th></>}
                </tr></thead>
                <tbody>{(sub === 'adv' ? advances : loans).map(item => (
                  <tr key={item.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{item.employee_name}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(item.amount)}</td>
                    {sub === 'adv' ? <><td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.purpose || '-'}</td><td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.date || '-'}</td></> : <><td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(item.monthly_installment)}</td><td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.months_remaining}</td><td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(item.remaining_amount)}</td></>}
                    <td className="px-4 py-3"><span className={badge(item.status)}>{SL[item.status]}</span></td>
                    <td className="px-4 py-3">{item.status === 'pending' && isAdmin && <div className="flex gap-1">
                      <button onClick={() => sub === 'adv' ? hApproveAdv(item.id, 'approve') : hApproveLn(item.id, 'approve')} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20"><Check className="w-4 h-4" /></button>
                      <button onClick={() => sub === 'adv' ? hApproveAdv(item.id, 'reject') : hApproveLn(item.id, 'reject')} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20"><Ban className="w-4 h-4" /></button>
                    </div>}</td>
                  </tr>
                ))}</tbody>
              </table></div>
            )}
          </div>
        </div>
      )}

      {/* ─── End of Service Tab ─── */}
      {tab === 'endofservice' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : eosList.length === 0 ? <div className="p-12 text-center"><Gift className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد حسابات نهاية خدمة</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الموظف</Th><Th>سنوات الخدمة</Th><Th>أيام الخدمة</Th><Th>إجمالي المكافأة</Th><Th>صافي المكافأة</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{eosList.map(e => (
                <tr key={e.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{e.employee_name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{e.years_of_service}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{e.total_service_days}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(e.total_benefit)}</td>
                  <td className="px-4 py-3 text-accent-500 dark:text-accent-400 font-bold">{fm(e.net_benefit)}</td>
                  <td className="px-4 py-3"><span className={badge(e.status)}>{SL[e.status]}</span></td>
                  <td className="px-4 py-3"><button onClick={() => hCalcEos(e)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="حساب"><Calculator className="w-4 h-4" /></button></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="period" title="إنشاء فترة رواتب جديدة"><form onSubmit={hCreatePeriod} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الفترة *</label><input type="text" value={pForm.name} onChange={e => setPForm({...pForm, name: e.target.value})} required placeholder="مثال: رواتب يناير 2025" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الشهر *</label><select value={pForm.month} onChange={e => setPForm({...pForm, month: e.target.value})} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option>{[1,2,3,4,5,6,7,8,9,10,11,12].map(m => <option key={m} value={m}>{m}</option>)}</select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">السنة *</label><input type="number" value={pForm.year} onChange={e => setPForm({...pForm, year: e.target.value})} required min="2020" max="2099" className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="period" /></div>
      </form></Modal>

      <Modal k="payslip" title={`تعديل كشف: ${selRec?.employee_name || ''}`}><form onSubmit={hSavePayslip} className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-3">{[['basic_salary','الراتب الأساسي'],['housing_allowance','بدل السكن'],['transport_allowance','بدل النقل'],['food_allowance','بدل الطعام'],['overtime','ساعات إضافية'],['absences_deduction','خصم الغياب'],['loan_deduction','خصم القروض'],['advance_deduction','خصم السلف'],['tax','الضرائب'],['social_insurance','التأمينات']].map(([k, l]) => (
          <div key={k}><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{l}</label><input type="number" step="0.01" value={psForm[k]} onChange={e => setPsForm({...psForm, [k]: e.target.value})} className={ic} /></div>
        ))}</div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">ملاحظات</label><textarea value={psForm.notes} onChange={e => setPsForm({...psForm, notes: e.target.value})} rows={2} className={`${ic} resize-none`} /></div>
        <div className="flex gap-3 pt-2"><Btn>حفظ</Btn><CancelBtn k="payslip" /></div>
      </form></Modal>

      <Modal k="advance" title="إنشاء سلفة جديدة"><form onSubmit={hCreateAdv} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الموظف *</label><input type="text" value={advForm.employee} onChange={e => setAdvForm({...advForm, employee: e.target.value})} required placeholder="معرف الموظف" className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ *</label><input type="number" step="0.01" value={advForm.amount} onChange={e => setAdvForm({...advForm, amount: e.target.value})} required className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الغرض</label><textarea value={advForm.purpose} onChange={e => setAdvForm({...advForm, purpose: e.target.value})} rows={2} className={`${ic} resize-none`} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="advance" /></div>
      </form></Modal>

      <Modal k="loan" title="إنشاء قرض جديد"><form onSubmit={hCreateLn} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الموظف *</label><input type="text" value={lnForm.employee} onChange={e => setLnForm({...lnForm, employee: e.target.value})} required placeholder="معرف الموظف" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مبلغ القرض *</label><input type="number" step="0.01" value={lnForm.amount} onChange={e => setLnForm({...lnForm, amount: e.target.value})} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">عدد الأشهر *</label><input type="number" value={lnForm.months} onChange={e => setLnForm({...lnForm, months: e.target.value})} required min="1" className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القسط الشهري *</label><input type="number" step="0.01" value={lnForm.monthly_installment} onChange={e => setLnForm({...lnForm, monthly_installment: e.target.value})} required className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="loan" /></div>
      </form></Modal>
    </div>
  );
}
