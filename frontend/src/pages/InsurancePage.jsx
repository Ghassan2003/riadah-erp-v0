/**
 * Insurance & Pension Management page - HR module.
 * Manage insurance policies, claims, and pension schemes.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { insuranceAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Edit2, Trash2,
  Shield, CheckCircle, DollarSign, FileWarning, PiggyBank, RefreshCw,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  expired: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  under_review: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  partially_approved: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};
const SL = {
  active: 'نشط', expired: 'منتهي', pending: 'معلّق', approved: 'معتمد',
  rejected: 'مرفوض', cancelled: 'ملغى', under_review: 'قيد المراجعة',
  partially_approved: 'معتمد جزئياً', inactive: 'غير نشط',
};

const TABS = [
  { id: 'policies', name: 'بوالص التأمين', icon: Shield },
  { id: 'claims', name: 'طلبات التعويض', icon: FileWarning },
  { id: 'pensions', name: 'المعاشات', icon: PiggyBank },
];
const STATS = [
  { key: 'total_policies', label: 'البوالص', icon: Shield, color: 'from-blue-500 to-blue-600' },
  { key: 'active_policies', label: 'النشطة', icon: CheckCircle, color: 'from-emerald-500 to-emerald-600' },
  { key: 'total_premiums', label: 'الأقساط', icon: DollarSign, color: 'from-amber-500 to-amber-600' },
  { key: 'pending_claims', label: 'طلبات معلّقة', icon: FileWarning, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function InsurancePage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('policies');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [policies, setPolicies] = useState([]);
  const [claims, setClaims] = useState([]);
  const [pensions, setPensions] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ policy: false, claim: false, pension: false, review: false });
  const [selRec, setSelRec] = useState(null);
  const [polForm, setPolForm] = useState({ name: '', provider: '', type: '', coverage: '', premium: '', start_date: '', end_date: '' });
  const [clForm, setClForm] = useState({ policy: '', type: '', claimed_amount: '' });
  const [penForm, setPenForm] = useState({ employee: '', scheme: '', monthly_contribution: '', employer_contrib: '', employee_contrib: '' });
  const [reviewAction, setReviewAction] = useState('approved');
  const [reviewNote, setReviewNote] = useState('');

  const isAdmin = JSON.parse(localStorage.getItem('user') || '{}')?.role === 'admin';
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await insuranceAPI.getStats()).data); } catch {} })(); }, []);

  useEffect(() => {
    const fetchTab = async () => {
      setLd(true);
      try {
        if (tab === 'policies') setPolicies((await insuranceAPI.getPolicies({ search, status: sFilter })).data.results || []);
        else if (tab === 'claims') setClaims((await insuranceAPI.getClaims({ search, status: sFilter })).data.results || []);
        else setPensions((await insuranceAPI.getPensions({ search, status: sFilter })).data.results || []);
      } catch { toast.error('خطأ في تحميل البيانات'); } finally { setLd(false); }
    };
    fetchTab();
  }, [tab, search, sFilter]);

  const hCreatePolicy = async (e) => { e.preventDefault(); setSv(true); try { await insuranceAPI.createPolicy({ ...polForm, premium: +polForm.premium, coverage: +polForm.coverage }); toast.success('تم إنشاء بوليصة التأمين بنجاح'); setModals({ ...modals, policy: false }); setPolForm({ name: '', provider: '', type: '', coverage: '', premium: '', start_date: '', end_date: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateClaim = async (e) => { e.preventDefault(); setSv(true); try { await insuranceAPI.createClaim({ ...clForm, claimed_amount: +clForm.claimed_amount, policy: +clForm.policy }); toast.success('تم إنشاء طلب التعويض بنجاح'); setModals({ ...modals, claim: false }); setClForm({ policy: '', type: '', claimed_amount: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreatePension = async (e) => { e.preventDefault(); setSv(true); try { await insuranceAPI.createPension({ ...penForm, monthly_contribution: +penForm.monthly_contribution, employer_contrib: +penForm.employer_contrib, employee_contrib: +penForm.employee_contrib, employee: +penForm.employee }); toast.success('تم إنشاء اشتراك المعاش بنجاح'); setModals({ ...modals, pension: false }); setPenForm({ employee: '', scheme: '', monthly_contribution: '', employer_contrib: '', employee_contrib: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hReviewClaim = async (e) => { e.preventDefault(); if (!selRec) return; setSv(true); try { await insuranceAPI.reviewClaim(selRec.id, { action: reviewAction, notes: reviewNote }); toast.success(reviewAction === 'approved' ? 'تمت الموافقة على الطلب' : 'تم رفض الطلب'); setModals({ ...modals, review: false }); setReviewNote(''); } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); } finally { setSv(false); } };
  const hDeletePolicy = async (id) => { if (!confirm('هل أنت متأكد من حذف هذه البوليصة؟')) return; try { await insuranceAPI.deletePolicy(id); toast.success('تم الحذف بنجاح'); setPolicies((prev) => prev.filter(p => p.id !== id)); } catch { toast.error('خطأ في الحذف'); } };

  const openReview = (c) => { setSelRec(c); setReviewAction('approved'); setReviewNote(''); setModals({ ...modals, review: true }); };

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">التأمين والمعاشات</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة بوالص التأمين، طلبات التعويض، واشتراكات المعاشات</p>
        </div>
        <div className="flex gap-2">
          {tab === 'policies' && isAdmin && <button onClick={() => setModals({ ...modals, policy: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> بوليصة جديدة</button>}
          {tab === 'claims' && isAdmin && <button onClick={() => setModals({ ...modals, claim: true })} className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> طلب تعويض</button>}
          {tab === 'pensions' && isAdmin && <button onClick={() => setModals({ ...modals, pension: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> اشتراك جديد</button>}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{key === 'total_premiums' ? fm(stats[key]) : (stats[key] || '-')}</p></div>
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
            {(tab === 'policies' ? ['active','expired','pending','cancelled'] : tab === 'claims' ? ['pending','under_review','approved','partially_approved','rejected'] : ['active','inactive','pending']).map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── Policies Tab ─── */}
      {tab === 'policies' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : policies.length === 0 ? <div className="p-12 text-center"><Shield className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد بوالص تأمين</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم البوليصة</Th><Th>الاسم</Th><Th>مزود الخدمة</Th><Th>النوع</Th><Th>التغطية</Th><Th>القسط</Th><Th>الحالة</Th><Th>تاريخ البداية</Th><Th>تاريخ النهاية</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{policies.map(p => (
                <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-500">{p.policy_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{p.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.provider}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.type}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(p.coverage)}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(p.premium)}</td>
                  <td className="px-4 py-3"><span className={badge(p.status)}>{SL[p.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.start_date || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.end_date || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => { setSelRec(p); setPolForm({ name: p.name, provider: p.provider, type: p.type, coverage: p.coverage || '', premium: p.premium || '', start_date: p.start_date || '', end_date: p.end_date || '' }); setModals({ ...modals, policy: true }); }} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="تعديل"><Edit2 className="w-4 h-4" /></button>
                    {isAdmin && <button onClick={() => hDeletePolicy(p.id)} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="حذف"><Trash2 className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Claims Tab ─── */}
      {tab === 'claims' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : claims.length === 0 ? <div className="p-12 text-center"><FileWarning className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد طلبات تعويض</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الطلب</Th><Th>البوليصة</Th><Th>النوع</Th><Th>المبلغ المطالب</Th><Th>المبلغ المعتمد</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{claims.map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-500">{c.claim_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.policy}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.type}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(c.claimed_amount)}</td>
                  <td className="px-4 py-3 font-medium text-blue-600 dark:text-blue-400">{c.approved_amount != null ? fm(c.approved_amount) : '-'}</td>
                  <td className="px-4 py-3"><span className={badge(c.status)}>{SL[c.status]}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    {(c.status === 'pending' || c.status === 'under_review') && isAdmin && <button onClick={() => openReview(c)} className="text-purple-600 dark:text-purple-400 p-1.5 rounded hover:bg-purple-50 dark:hover:bg-purple-900/20" title="مراجعة"><Eye className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Pensions Tab ─── */}
      {tab === 'pensions' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : pensions.length === 0 ? <div className="p-12 text-center"><PiggyBank className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد اشتراكات معاشات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الموظف</Th><Th>المخطط</Th><Th>المساهمة الشهرية</Th><Th>مساهمة صاحب العمل</Th><Th>مساهمة الموظف</Th><Th>الحالة</Th><Th>إجمالي المساهمات</Th>
              </tr></thead>
              <tbody>{pensions.map(p => (
                <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{p.employee}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{p.scheme}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(p.monthly_contribution)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(p.employer_contrib)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(p.employee_contrib)}</td>
                  <td className="px-4 py-3"><span className={badge(p.status)}>{SL[p.status]}</span></td>
                  <td className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">{fm(p.total_contributions)}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="policy" title={selRec ? 'تعديل بوليصة التأمين' : 'إنشاء بوليصة جديدة'}><form onSubmit={hCreatePolicy} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم البوليصة *</label><input type="text" value={polForm.name} onChange={e => setPolForm({ ...polForm, name: e.target.value })} required placeholder="مثال: تأمين شامل" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مزود الخدمة *</label><input type="text" value={polForm.provider} onChange={e => setPolForm({ ...polForm, provider: e.target.value })} required placeholder="شركة التأمين" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع *</label><select value={polForm.type} onChange={e => setPolForm({ ...polForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="health">تأمين صحي</option><option value="life">تأمين حياة</option><option value="property">تأمين ممتلكات</option><option value="vehicle">تأمين مركبات</option><option value="liability">تأمين مسؤولية</option></select></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مبلغ التغطية *</label><input type="number" step="0.01" value={polForm.coverage} onChange={e => setPolForm({ ...polForm, coverage: e.target.value })} required placeholder="0.00" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القسط السنوي *</label><input type="number" step="0.01" value={polForm.premium} onChange={e => setPolForm({ ...polForm, premium: e.target.value })} required placeholder="0.00" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ البداية *</label><input type="date" value={polForm.start_date} onChange={e => setPolForm({ ...polForm, start_date: e.target.value })} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ النهاية *</label><input type="date" value={polForm.end_date} onChange={e => setPolForm({ ...polForm, end_date: e.target.value })} required className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>{selRec ? 'تحديث' : 'إنشاء'}</Btn><CancelBtn k="policy" /></div>
      </form></Modal>

      <Modal k="claim" title="إنشاء طلب تعويض جديد"><form onSubmit={hCreateClaim} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">البوليصة *</label><input type="text" value={clForm.policy} onChange={e => setClForm({ ...clForm, policy: e.target.value })} required placeholder="معرف البوليصة" className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع التعويض *</label><select value={clForm.type} onChange={e => setClForm({ ...clForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="health">صحي</option><option value="accident">حادث</option><option value="property">ممتلكات</option><option value="liability">مسؤولية</option></select></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ المطالب *</label><input type="number" step="0.01" value={clForm.claimed_amount} onChange={e => setClForm({ ...clForm, claimed_amount: e.target.value })} required placeholder="0.00" className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-purple-600 hover:bg-purple-700">إنشاء</Btn><CancelBtn k="claim" /></div>
      </form></Modal>

      <Modal k="pension" title="إنشاء اشتراك معاش جديد"><form onSubmit={hCreatePension} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الموظف *</label><input type="text" value={penForm.employee} onChange={e => setPenForm({ ...penForm, employee: e.target.value })} required placeholder="معرف الموظف" className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المخطط *</label><select value={penForm.scheme} onChange={e => setPenForm({ ...penForm, scheme: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="gosi">التأمينات الاجتماعية (GOSI)</option><option value="private">تقاعد خاص</option></select></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مساهمة صاحب العمل *</label><input type="number" step="0.01" value={penForm.employer_contrib} onChange={e => setPenForm({ ...penForm, employer_contrib: e.target.value })} required placeholder="0.00" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">مساهمة الموظف *</label><input type="number" step="0.01" value={penForm.employee_contrib} onChange={e => setPenForm({ ...penForm, employee_contrib: e.target.value })} required placeholder="0.00" className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="pension" /></div>
      </form></Modal>

      <Modal k="review" title={`مراجعة طلب: ${selRec?.claim_number || ''}`}><form onSubmit={hReviewClaim} className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-sm"><span className="text-gray-500 dark:text-gray-400">المبلغ المطالب:</span><p className="font-bold text-gray-900 dark:text-gray-100 mt-1">{selRec ? fm(selRec.claimed_amount) : ''}</p></div>
          <div className="text-sm"><span className="text-gray-500 dark:text-gray-400">النوع:</span><p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{selRec?.type}</p></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">القرار *</label>
          <div className="flex gap-3">
            <button type="button" onClick={() => setReviewAction('approved')} className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${reviewAction === 'approved' ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400'}`}><Check className="w-4 h-4" /> موافقة</button>
            <button type="button" onClick={() => setReviewAction('rejected')} className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${reviewAction === 'rejected' ? 'border-red-500 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400' : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400'}`}><Ban className="w-4 h-4" /> رفض</button>
          </div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">ملاحظات</label><textarea value={reviewNote} onChange={e => setReviewNote(e.target.value)} rows={2} placeholder="أضف ملاحظات المراجعة..." className={`${ic} resize-none`} /></div>
        <div className="flex gap-3 pt-2"><Btn cls={reviewAction === 'approved' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}>تأكيد</Btn><CancelBtn k="review" /></div>
      </form></Modal>
    </div>
  );
}
