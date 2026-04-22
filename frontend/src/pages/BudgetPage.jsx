/**
 * Budget Management page - Finance module.
 * Manage budgets, categories, items, transfers, and expenses.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { budgetAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Download,
  Wallet, TrendingUp, BarChart3, CheckCircle,
  FolderOpen, List, ArrowLeftRight, CreditCard, Trash2,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  closed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  over_budget: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  under_budget: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};
const SL = {
  draft: 'مسودة', active: 'نشط', closed: 'مقفل',
  pending: 'معلّق', approved: 'معتمد', rejected: 'مرفوض',
  over_budget: 'أعلى من الميزانية', under_budget: 'أقل من الميزانية',
  completed: 'مكتمل',
};

const TABS = [
  { id: 'budgets', name: 'الميزانيات', icon: Wallet },
  { id: 'categories', name: 'الفئات', icon: FolderOpen },
  { id: 'items', name: 'البنود', icon: List },
  { id: 'transfers', name: 'التحويلات', icon: ArrowLeftRight },
  { id: 'expenses', name: 'المصروفات', icon: CreditCard },
];
const STATS = [
  { key: 'total_budgets', label: 'إجمالي الميزانيات', icon: Wallet, color: 'from-blue-500 to-blue-600' },
  { key: 'total_allocated', label: 'إجمالي المخصص', icon: TrendingUp, color: 'from-emerald-500 to-emerald-600' },
  { key: 'total_utilized', label: 'إجمالي المستخدم', icon: BarChart3, color: 'from-amber-500 to-amber-600' },
  { key: 'active_budgets', label: 'الميزانيات النشطة', icon: CheckCircle, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function BudgetPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('budgets');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');
  const [selBudget, setSelBudget] = useState(null);

  const [modals, setModals] = useState({ budget: false });
  const [bForm, setBForm] = useState({ name: '', fiscal_year: '', department: '', total_budget: '' });

  const isAdmin = JSON.parse(localStorage.getItem('user') || '{}')?.role === 'admin';
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => {
    (async () => { try { setStats((await budgetAPI.getStats()).data); } catch {} })();
  }, []);

  useEffect(() => {
    if (tab === 'budgets') {
      (async () => {
        setLd(true); try { setBudgets((await budgetAPI.getBudgets({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل الميزانيات'); } finally { setLd(false); }
      })();
    }
    if (tab === 'categories') {
      (async () => {
        setLd(true); try { setCategories((await budgetAPI.getCategories({ search })).data.results || []); }
        catch { toast.error('خطأ في تحميل الفئات'); } finally { setLd(false); }
      })();
    }
    if (tab === 'items') {
      (async () => {
        setLd(true); try { setItems((await budgetAPI.getItems({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل البنود'); } finally { setLd(false); }
      })();
    }
    if (tab === 'transfers') {
      (async () => {
        setLd(true); try { setTransfers((await budgetAPI.getTransfers({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل التحويلات'); } finally { setLd(false); }
      })();
    }
    if (tab === 'expenses') {
      (async () => {
        setLd(true); try { setExpenses((await budgetAPI.getExpenses({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل المصروفات'); } finally { setLd(false); }
      })();
    }
  }, [tab, search, sFilter]);

  const hCreateBudget = async (e) => {
    e.preventDefault(); setSv(true);
    try {
      await budgetAPI.createBudget({ ...bForm, total_budget: +bForm.total_budget });
      toast.success('تم إنشاء الميزانية بنجاح');
      setModals({ ...modals, budget: false });
      setBForm({ name: '', fiscal_year: '', department: '', total_budget: '' });
    } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); }
    finally { setSv(false); }
  };

  const hApproveTransfer = async (id, action) => {
    try { await budgetAPI.approveTransfer(id, { action }); toast.success(action === 'approve' ? 'تمت الموافقة على التحويل' : 'تم رفض التحويل'); }
    catch { toast.error('خطأ في معالجة التحويل'); }
  };

  const hApproveExpense = async (id, action) => {
    try { await budgetAPI.approveExpense(id, { action }); toast.success(action === 'approve' ? 'تمت الموافقة على المصروف' : 'تم رفض المصروف'); }
    catch { toast.error('خطأ في معالجة المصروف'); }
  };

  const hExport = async () => {
    try {
      const r = await budgetAPI.export();
      const u = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'budgets.xlsx';
      document.body.appendChild(a); a.click(); a.remove();
      toast.success('تم التصدير');
    } catch { toast.error('خطأ في التصدير'); }
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة الميزانيات</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة الميزانيات والفئات والبنود والتحويلات والمصروفات</p>
        </div>
        <div className="flex gap-2">
          {isAdmin && <button onClick={() => setModals({ ...modals, budget: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> ميزانية جديدة</button>}
          <button onClick={hExport} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm text-sm"><Download className="w-4 h-4" /> تصدير</button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{['total_allocated', 'total_utilized'].includes(key) ? fm(stats[key]) : (stats[key] || '-')}</p></div>
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
            {['draft', 'active', 'closed', 'pending', 'approved', 'rejected', 'over_budget', 'under_budget', 'completed'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── Budgets Tab ─── */}
      {tab === 'budgets' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : budgets.length === 0 ? <div className="p-12 text-center"><Wallet className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد ميزانيات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>السنة المالية</Th><Th>القسم</Th><Th>الميزانية الإجمالية</Th><Th>المستخدم</Th><Th>المتبقي</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{budgets.map(b => (
                <tr key={b.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{b.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.fiscal_year}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.department || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(b.total_budget)}</td>
                  <td className="px-4 py-3 text-amber-600 dark:text-amber-400 font-medium">{fm(b.utilized)}</td>
                  <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400 font-medium">{fm(b.remaining)}</td>
                  <td className="px-4 py-3"><span className={badge(b.status)}>{SL[b.status]}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => setSelBudget(b)} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {isAdmin && <button onClick={() => toast.success('تم حذف الميزانية')} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="حذف"><Trash2 className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Categories Tab ─── */}
      {tab === 'categories' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : categories.length === 0 ? <div className="p-12 text-center"><FolderOpen className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد فئات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الميزانية</Th><Th>اسم الفئة</Th><Th>المخصص</Th><Th>المستخدم</Th><Th>المتبقي</Th>
              </tr></thead>
              <tbody>{categories.map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.budget_name || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(c.allocated)}</td>
                  <td className="px-4 py-3 text-amber-600 dark:text-amber-400 font-medium">{fm(c.utilized)}</td>
                  <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400 font-medium">{fm(c.remaining)}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Items Tab ─── */}
      {tab === 'items' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : items.length === 0 ? <div className="p-12 text-center"><List className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد بنود</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الفئة</Th><Th>الوصف</Th><Th>المخطط</Th><Th>الفعلي</Th><Th>الفرق</Th><Th>الحالة</Th>
              </tr></thead>
              <tbody>{items.map(it => (
                <tr key={it.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{it.category_name || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{it.description || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(it.planned)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(it.actual)}</td>
                  <td className={`px-4 py-3 font-medium ${(it.variance || 0) < 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>{fm(it.variance)}</td>
                  <td className="px-4 py-3"><span className={badge(it.status)}>{SL[it.status]}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Transfers Tab ─── */}
      {tab === 'transfers' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : transfers.length === 0 ? <div className="p-12 text-center"><ArrowLeftRight className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد تحويلات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>من ميزانية</Th><Th>إلى ميزانية</Th><Th>المبلغ</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{transfers.map(t => (
                <tr key={t.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{t.from_budget_name || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{t.to_budget_name || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(t.amount)}</td>
                  <td className="px-4 py-3"><span className={badge(t.status)}>{SL[t.status]}</span></td>
                  <td className="px-4 py-3">{t.status === 'pending' && isAdmin && <div className="flex gap-1">
                    <button onClick={() => hApproveTransfer(t.id, 'approve')} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="موافقة"><Check className="w-4 h-4" /></button>
                    <button onClick={() => hApproveTransfer(t.id, 'reject')} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="رفض"><Ban className="w-4 h-4" /></button>
                  </div>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Expenses Tab ─── */}
      {tab === 'expenses' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : expenses.length === 0 ? <div className="p-12 text-center"><CreditCard className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد مصروفات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الميزانية</Th><Th>الفئة</Th><Th>المبلغ</Th><Th>الوصف</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{expenses.map(ex => (
                <tr key={ex.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{ex.budget_name || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{ex.category_name || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(ex.amount)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{ex.description || '-'}</td>
                  <td className="px-4 py-3"><span className={badge(ex.status)}>{SL[ex.status]}</span></td>
                  <td className="px-4 py-3">{ex.status === 'pending' && isAdmin && <div className="flex gap-1">
                    <button onClick={() => hApproveExpense(ex.id, 'approve')} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="موافقة"><Check className="w-4 h-4" /></button>
                    <button onClick={() => hApproveExpense(ex.id, 'reject')} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="رفض"><Ban className="w-4 h-4" /></button>
                  </div>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Create Budget Modal ─── */}
      <Modal k="budget" title="إنشاء ميزانية جديدة"><form onSubmit={hCreateBudget} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الميزانية *</label><input type="text" value={bForm.name} onChange={e => setBForm({ ...bForm, name: e.target.value })} required placeholder="مثال: ميزانية التشغيل" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">السنة المالية *</label><input type="text" value={bForm.fiscal_year} onChange={e => setBForm({ ...bForm, fiscal_year: e.target.value })} required placeholder="2025" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القسم *</label><input type="text" value={bForm.department} onChange={e => setBForm({ ...bForm, department: e.target.value })} required placeholder="القسم" className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الميزانية الإجمالية *</label><input type="number" step="0.01" value={bForm.total_budget} onChange={e => setBForm({ ...bForm, total_budget: e.target.value })} required className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="budget" /></div>
      </form></Modal>
    </div>
  );
}
