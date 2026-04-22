/**
 * Internal Audit page – المراجعة الداخلية (RTL Arabic ERP)
 * Tabs: Plans, Findings, Actions, Compliance
 * Supports dark mode and i18n.
 * All data fetched from real API endpoints.
 */

import { useState, useEffect } from 'react';
import { internalauditAPI } from '../api';
import toast from 'react-hot-toast';
import {
  ClipboardCheck, AlertTriangle, ListChecks, ShieldCheck,
  Plus, Search, X, Eye, Download, CheckCircle, Clock, RefreshCw,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

/* eslint-disable react/prop-types */

const SC = {
  planned: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  open: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  closed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  resolved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  compliant: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  non_compliant: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  partially_compliant: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  not_checked: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  overdue: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const SL = {
  planned: 'مخطط', in_progress: 'قيد التنفيذ', completed: 'مكتمل', cancelled: 'ملغي',
  open: 'مفتوح', closed: 'مغلق', pending: 'معلّق', resolved: 'تم الحل',
  high: 'عالي', critical: 'حرج', medium: 'متوسط', low: 'منخفض',
  compliant: 'متوافق', non_compliant: 'غير متوافق', partially_compliant: 'توافق جزئي',
  not_checked: 'لم يُفحص', overdue: 'متأخر',
};

const TABS = [
  { id: 'plans', name: 'خطط التدقيق', icon: ClipboardCheck },
  { id: 'findings', name: 'الملاحظات', icon: AlertTriangle },
  { id: 'actions', name: 'الإجراءات', icon: ListChecks },
  { id: 'compliance', name: 'التوافق', icon: ShieldCheck },
];

const STATS = [
  { key: 'total_plans', label: 'خطط التدقيق', icon: ClipboardCheck, color: 'from-blue-500 to-blue-600' },
  { key: 'open_findings', label: 'ملاحظات مفتوحة', icon: AlertTriangle, color: 'from-red-500 to-red-600' },
  { key: 'pending_actions', label: 'إجراءات معلّقة', icon: ListChecks, color: 'from-amber-500 to-amber-600' },
  { key: 'compliance_rate', label: 'نسبة التوافق', icon: ShieldCheck, color: 'from-emerald-500 to-emerald-600' },
];

const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function InternalAuditPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('plans');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [plans, setPlans] = useState([]);
  const [findings, setFindings] = useState([]);
  const [actions, setActions] = useState([]);
  const [compliance, setCompliance] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ plan: false, finding: false, action: false, compliance: false, detail: false });
  const [selItem, setSelItem] = useState(null);
  const [planForm, setPlanForm] = useState({ name: '', type: '', department: '', start_date: '', lead_auditor: '', risk_level: 'medium' });
  const [findingForm, setFindingForm] = useState({ title: '', plan: '', severity: 'medium', category: '', responsible: '', due_date: '' });
  const [actionForm, setActionForm] = useState({ finding: '', description: '', assigned_to: '', priority: 'medium', due_date: '' });
  const [compForm, setCompForm] = useState({ name: '', regulation: '', department: '', last_check: '', next_check: '' });

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  const loadData = async () => {
    setLd(true);
    try {
      const [plansRes, findingsRes, actionsRes, compRes] = await Promise.all([
        internalauditAPI.getPlans(),
        internalauditAPI.getFindings(),
        internalauditAPI.getActions(),
        internalauditAPI.getComplianceChecks(),
      ]);
      setPlans(plansRes.data.results || plansRes.data || []);
      setFindings(findingsRes.data.results || findingsRes.data || []);
      setActions(actionsRes.data.results || actionsRes.data || []);
      setCompliance(compRes.data.results || compRes.data || []);

      // Load stats separately
      try {
        const statsRes = await internalauditAPI.getStats();
        setStats(statsRes.data || {});
      } catch {
        // Stats non-critical, compute from loaded data
        const openFindings = findings.filter(f => f.status === 'open' || f.status === 'pending').length;
        const pendingActions = actions.filter(a => a.status === 'pending' || a.status === 'in_progress').length;
        const totalCompliance = compliance.length;
        const compliantCount = compliance.filter(c => c.status === 'compliant').length;
        setStats({
          total_plans: plans.length,
          open_findings: openFindings,
          pending_actions: pendingActions,
          compliance_rate: totalCompliance > 0 ? `${Math.round((compliantCount / totalCompliance) * 100)}%` : '0%',
        });
      }
    } catch (err) {
      console.error('Error loading internal audit data:', err);
      toast.error('خطأ في تحميل بيانات المراجعة الداخلية');
    } finally {
      setLd(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const hCompletePlan = async (id) => {
    try {
      await internalauditAPI.completePlan(id);
      toast.success('تم إكمال خطة التدقيق');
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في تحديث الحالة');
    }
  };

  const hResolveFinding = async (id) => {
    try {
      await internalauditAPI.resolveFinding(id, { status: 'resolved' });
      toast.success('تم حل الملاحظة');
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في تحديث الحالة');
    }
  };

  const hCompleteAction = async (id) => {
    try {
      await internalauditAPI.completeAction(id);
      toast.success('تم إكمال الإجراء');
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في تحديث الحالة');
    }
  };

  const hPerformCheck = async (id) => {
    try {
      await internalauditAPI.performComplianceCheck(id, { status: 'compliant' });
      toast.success('تم إجراء فحص التوافق');
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في تنفيذ الفحص');
    }
  };

  const hExport = async () => {
    try {
      const r = await internalauditAPI.export();
      const u = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = u;
      a.download = 'audit-report.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast.success('تم التصدير');
    } catch (err) {
      console.error(err);
      toast.error('خطأ في التصدير');
    }
  };

  const hCreatePlan = async (e) => {
    e.preventDefault();
    setSv(true);
    try {
      await internalauditAPI.createPlan(planForm);
      toast.success('تم إنشاء خطة التدقيق بنجاح');
      setModals({ ...modals, plan: false });
      setPlanForm({ name: '', type: '', department: '', start_date: '', lead_auditor: '', risk_level: 'medium' });
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في إنشاء خطة التدقيق');
    } finally {
      setSv(false);
    }
  };

  const hCreateFinding = async (e) => {
    e.preventDefault();
    setSv(true);
    try {
      await internalauditAPI.createFinding(findingForm);
      toast.success('تم تسجيل الملاحظة بنجاح');
      setModals({ ...modals, finding: false });
      setFindingForm({ title: '', plan: '', severity: 'medium', category: '', responsible: '', due_date: '' });
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في تسجيل الملاحظة');
    } finally {
      setSv(false);
    }
  };

  const hCreateAction = async (e) => {
    e.preventDefault();
    setSv(true);
    try {
      await internalauditAPI.createAction(actionForm);
      toast.success('تم إنشاء الإجراء بنجاح');
      setModals({ ...modals, action: false });
      setActionForm({ finding: '', description: '', assigned_to: '', priority: 'medium', due_date: '' });
      loadData();
    } catch (err) {
      console.error(err);
      toast.error('خطأ في إنشاء الإجراء');
    } finally {
      setSv(false);
    }
  };

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

  const Btn = ({ onClick, disabled, children, cls = 'bg-blue-600 hover:bg-blue-700', full = true }) => (
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">المراجعة الداخلية</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة خطط التدقيق والملاحظات والإجراءات التصحيحية والتوافق</p>
        </div>
        <div className="flex gap-2">
          <button onClick={hExport} className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors shadow-sm text-sm"><Download className="w-4 h-4" /> تصدير</button>
          {tab === 'plans' && <button onClick={() => setModals({ ...modals, plan: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> خطة جديدة</button>}
          {tab === 'findings' && <button onClick={() => setModals({ ...modals, finding: true })} className="flex items-center gap-2 px-4 py-2.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> ملاحظة جديدة</button>}
          {tab === 'actions' && <button onClick={() => setModals({ ...modals, action: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> إجراء جديد</button>}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{key === 'compliance_rate' ? (stats[key] || '0%') : (stats[key] ?? '-')}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {TABS.map(t => { const I = t.icon; return <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}><I className="w-4 h-4" /> {t.name}</button>; })}
      </div>

      {/* Search & Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
          </div>
          <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الحالات</option>
            {tab === 'plans' && ['planned', 'in_progress', 'completed', 'cancelled'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
            {tab === 'findings' && ['open', 'pending', 'resolved', 'closed'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
            {tab === 'actions' && ['pending', 'in_progress', 'resolved', 'completed'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
            {tab === 'compliance' && ['compliant', 'non_compliant', 'partially_compliant', 'not_checked'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── Plans Tab ─── */}
      {tab === 'plans' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : plans.length === 0 ? <div className="p-12 text-center"><ClipboardCheck className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد خطط تدقيق</p><p className="text-xs text-gray-400 mt-1">أنشئ خطة تدقيق جديدة للبدء</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>النوع</Th><Th>القسم</Th><Th>الحالة</Th><Th>تاريخ البدء</Th><Th>مستوى المخاطر</Th><Th>المدقق الرئيسي</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{plans.filter(p => !sFilter || p.status === sFilter).filter(p => !search || p.name.includes(search) || p.department.includes(search) || p.lead_auditor.includes(search)).map(p => (
                <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{p.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.type}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.department}</td>
                  <td className="px-4 py-3"><span className={badge(p.status)}>{SL[p.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.start_date}</td>
                  <td className="px-4 py-3"><span className={badge(p.risk_level)}>{SL[p.risk_level]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.lead_auditor}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelItem(p); setModals({ ...modals, detail: true }); }} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {p.status !== 'completed' && p.status !== 'cancelled' && <button onClick={() => hCompletePlan(p.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="إكمال"><CheckCircle className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Findings Tab ─── */}
      {tab === 'findings' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : findings.length === 0 ? <div className="p-12 text-center"><AlertTriangle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد ملاحظات</p><p className="text-xs text-gray-400 mt-1">سجّل ملاحظة جديدة لتوثيق نتائج التدقيق</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الرقم</Th><Th>العنوان</Th><Th>الخطة</Th><Th>الخطورة</Th><Th>التصنيف</Th><Th>الحالة</Th><Th>المسؤول</Th><Th>تاريخ الاستحقاق</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{findings.filter(f => !sFilter || f.status === sFilter).filter(f => !search || f.title.includes(search) || (f.finding_number && f.finding_number.includes(search)) || (f.responsible && f.responsible.includes(search))).map(f => (
                <tr key={f.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-blue-700 dark:text-blue-300">{f.finding_number || `FN-${String(f.id).padStart(3, '0')}`}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{f.title}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{f.plan_name || f.plan || ''}</td>
                  <td className="px-4 py-3"><span className={badge(f.severity)}>{SL[f.severity]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{f.category || ''}</td>
                  <td className="px-4 py-3"><span className={badge(f.status)}>{SL[f.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{f.responsible || ''}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{f.due_date || ''}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelItem(f); setModals({ ...modals, detail: true }); }} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {f.status !== 'resolved' && f.status !== 'closed' && <button onClick={() => hResolveFinding(f.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="حل"><CheckCircle className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Actions Tab ─── */}
      {tab === 'actions' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : actions.length === 0 ? <div className="p-12 text-center"><ListChecks className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد إجراءات</p><p className="text-xs text-gray-400 mt-1">أنشئ إجراء تصحيحي جديد لمتابعة الملاحظات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الرقم</Th><Th>الملاحظة</Th><Th>الوصف</Th><Th>المسؤول</Th><Th>الأولوية</Th><Th>تاريخ الاستحقاق</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{actions.filter(a => !sFilter || a.status === sFilter).filter(a => !search || a.description.includes(search) || (a.action_number && a.action_number.includes(search)) || (a.assigned_to && a.assigned_to.includes(search))).map(a => (
                <tr key={a.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-emerald-700 dark:text-emerald-300">{a.action_number || `ACT-${String(a.id).padStart(3, '0')}`}</td>
                  <td className="px-4 py-3 font-mono text-sm text-blue-600 dark:text-blue-300">{a.finding || ''}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{a.description}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{a.assigned_to || ''}</td>
                  <td className="px-4 py-3"><span className={badge(a.priority)}>{SL[a.priority]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{a.due_date || ''}</td>
                  <td className="px-4 py-3"><span className={badge(a.status)}>{SL[a.status]}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelItem(a); setModals({ ...modals, detail: true }); }} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {a.status !== 'resolved' && a.status !== 'completed' && <button onClick={() => hCompleteAction(a.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="إكمال"><CheckCircle className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Compliance Tab ─── */}
      {tab === 'compliance' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : compliance.length === 0 ? <div className="p-12 text-center"><ShieldCheck className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد بيانات توافق</p><p className="text-xs text-gray-400 mt-1">أضف فحص توافق جديد لتتبع الامتثال التنظيمي</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>اللائحة</Th><Th>القسم</Th><Th>الحالة</Th><Th>آخر فحص</Th><Th>الفحص القادم</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{compliance.filter(c => !sFilter || c.status === sFilter).filter(c => !search || c.name.includes(search) || c.regulation.includes(search) || c.department.includes(search)).map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.regulation || ''}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.department || ''}</td>
                  <td className="px-4 py-3"><span className={badge(c.status)}>{SL[c.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.last_check || '—'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.next_check || '—'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelItem(c); setModals({ ...modals, detail: true }); }} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    <button onClick={() => hPerformCheck(c.id)} className="text-purple-600 dark:text-purple-400 p-1.5 rounded hover:bg-purple-50 dark:hover:bg-purple-900/20" title="إجراء فحص"><RefreshCw className="w-4 h-4" /></button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Detail Modal ─── */}
      <Modal k="detail" title="تفاصيل">
        <div className="p-5 space-y-3">
          {selItem && tab === 'plans' && (
            <div className="grid grid-cols-2 gap-3">
              {[['الاسم', selItem.name], ['النوع', selItem.type], ['القسم', selItem.department], ['الحالة', <span className={badge(selItem.status)}>{SL[selItem.status]}</span>], ['تاريخ البدء', selItem.start_date], ['مستوى المخاطر', <span className={badge(selItem.risk_level)}>{SL[selItem.risk_level]}</span>], ['المدقق الرئيسي', selItem.lead_auditor]].map(([l, v], i) => (
                <div key={i}><p className="text-xs text-gray-500 dark:text-gray-400">{l}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{v}</p></div>
              ))}
            </div>
          )}
          {selItem && tab === 'findings' && (
            <div className="grid grid-cols-2 gap-3">
              {[['الرقم', selItem.finding_number || `FN-${String(selItem.id).padStart(3, '0')}`], ['العنوان', selItem.title], ['الخطة', selItem.plan_name || selItem.plan || ''], ['الخطورة', <span className={badge(selItem.severity)}>{SL[selItem.severity]}</span>], ['التصنيف', selItem.category || ''], ['الحالة', <span className={badge(selItem.status)}>{SL[selItem.status]}</span>], ['المسؤول', selItem.responsible || ''], ['تاريخ الاستحقاق', selItem.due_date || '']].map(([l, v], i) => (
                <div key={i}><p className="text-xs text-gray-500 dark:text-gray-400">{l}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{v}</p></div>
              ))}
            </div>
          )}
          {selItem && tab === 'actions' && (
            <div className="grid grid-cols-2 gap-3">
              {[['الرقم', selItem.action_number || `ACT-${String(selItem.id).padStart(3, '0')}`], ['الملاحظة', selItem.finding || ''], ['الوصف', selItem.description], ['المسؤول', selItem.assigned_to || ''], ['الأولوية', <span className={badge(selItem.priority)}>{SL[selItem.priority]}</span>], ['تاريخ الاستحقاق', selItem.due_date || ''], ['الحالة', <span className={badge(selItem.status)}>{SL[selItem.status]}</span>]].map(([l, v], i) => (
                <div key={i}><p className="text-xs text-gray-500 dark:text-gray-400">{l}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{v}</p></div>
              ))}
            </div>
          )}
          {selItem && tab === 'compliance' && (
            <div className="grid grid-cols-2 gap-3">
              {[['الاسم', selItem.name], ['اللائحة', selItem.regulation || ''], ['القسم', selItem.department || ''], ['الحالة', <span className={badge(selItem.status)}>{SL[selItem.status]}</span>], ['آخر فحص', selItem.last_check || '—'], ['الفحص القادم', selItem.next_check || '—']].map(([l, v], i) => (
                <div key={i}><p className="text-xs text-gray-500 dark:text-gray-400">{l}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{v}</p></div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      {/* ─── Create Plan Modal ─── */}
      <Modal k="plan" title="إنشاء خطة تدقيق جديدة"><form onSubmit={hCreatePlan} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الخطة *</label><input type="text" value={planForm.name} onChange={e => setPlanForm({ ...planForm, name: e.target.value })} required placeholder="مثال: تدقيق مالي سنوي" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع *</label><select value={planForm.type} onChange={e => setPlanForm({ ...planForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="مالي">مالي</option><option value="تشغيلي">تشغيلي</option><option value="تنظيمي">تنظيمي</option><option value="تقني">تقني</option></select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القسم *</label><input type="text" value={planForm.department} onChange={e => setPlanForm({ ...planForm, department: e.target.value })} required placeholder="القسم" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ البدء *</label><input type="date" value={planForm.start_date} onChange={e => setPlanForm({ ...planForm, start_date: e.target.value })} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مستوى المخاطر *</label><select value={planForm.risk_level} onChange={e => setPlanForm({ ...planForm, risk_level: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="low">منخفض</option><option value="medium">متوسط</option><option value="high">عالي</option><option value="critical">حرج</option></select></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المدقق الرئيسي *</label><input type="text" value={planForm.lead_auditor} onChange={e => setPlanForm({ ...planForm, lead_auditor: e.target.value })} required placeholder="اسم المدقق" className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="plan" /></div>
      </form></Modal>

      {/* ─── Create Finding Modal ─── */}
      <Modal k="finding" title="تسجيل ملاحظة جديدة"><form onSubmit={hCreateFinding} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">عنوان الملاحظة *</label><input type="text" value={findingForm.title} onChange={e => setFindingForm({ ...findingForm, title: e.target.value })} required placeholder="وصف الملاحظة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الخطورة *</label><select value={findingForm.severity} onChange={e => setFindingForm({ ...findingForm, severity: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option><option value="critical">حرجة</option></select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التصنيف *</label><input type="text" value={findingForm.category} onChange={e => setFindingForm({ ...findingForm, category: e.target.value })} required placeholder="مالية / تشغيلية / أمنية" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المسؤول *</label><input type="text" value={findingForm.responsible} onChange={e => setFindingForm({ ...findingForm, responsible: e.target.value })} required placeholder="المسؤول عن المتابعة" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الاستحقاق *</label><input type="date" value={findingForm.due_date} onChange={e => setFindingForm({ ...findingForm, due_date: e.target.value })} required className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-orange-600 hover:bg-orange-700">تسجيل</Btn><CancelBtn k="finding" /></div>
      </form></Modal>

      {/* ─── Create Action Modal ─── */}
      <Modal k="action" title="إنشاء إجراء تصحيحي"><form onSubmit={hCreateAction} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">وصف الإجراء *</label><input type="text" value={actionForm.description} onChange={e => setActionForm({ ...actionForm, description: e.target.value })} required placeholder="وصف الإجراء التصحيحي" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المسؤول *</label><input type="text" value={actionForm.assigned_to} onChange={e => setActionForm({ ...actionForm, assigned_to: e.target.value })} required placeholder="المسؤول عن التنفيذ" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأولوية *</label><select value={actionForm.priority} onChange={e => setActionForm({ ...actionForm, priority: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option><option value="critical">حرجة</option></select></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الاستحقاق *</label><input type="date" value={actionForm.due_date} onChange={e => setActionForm({ ...actionForm, due_date: e.target.value })} required className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="action" /></div>
      </form></Modal>
    </div>
  );
}
