/**
 * Projects Budget Management Page - إدارة ميزانيات المشاريع
 * Features: budget items table, create modal, summary cards, filters.
 */

import { useState, useEffect, useCallback } from 'react';
import { projectsAPI, projectBudgetAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Wallet, Plus, X, Edit3, Trash2, Search, Loader2, Save,
  AlertTriangle, TrendingDown, TrendingUp, DollarSign, PieChart,
} from 'lucide-react';

const CATEGORY_LABELS = {
  labor: 'أيدي عاملة', materials: 'مواد', equipment: 'معدات',
  subcontractors: 'مقاولين من الباطن', travel: 'سفر', overhead: 'نفقات عامة',
  contingency: 'طوارئ', other: 'أخرى',
};

const emptyItem = {
  project: '', category: 'labor', name: '', description: '',
  planned_amount: '', actual_amount: '',
};

export default function ProjectsBudgetPage() {
  const [projects, setProjects] = useState([]);
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [projectFilter, setProjectFilter] = useState('');
  const [search, setSearch] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyItem);

  const [deleteTarget, setDeleteTarget] = useState(null);

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';
  const nl = 'ar-SA';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const fetchProjects = useCallback(async () => {
    try {
      const r = await projectsAPI.list({ page_size: 100 });
      setProjects(r.data.results || r.data || []);
    } catch {}
  }, []);

  const fetchData = useCallback(async () => {
    if (!projectFilter) { setItems([]); setStats(null); return; }
    setLoading(true);
    try {
      const [itemsRes, statsRes] = await Promise.all([
        projectBudgetAPI.items(projectFilter),
        projectBudgetAPI.stats(projectFilter),
      ]);
      setItems(itemsRes.data.results || itemsRes.data || []);
      setStats(statsRes.data);
    } catch {
      toast.error('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  }, [projectFilter]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);
  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyItem, project: projectFilter || '' });
    setShowModal(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      project: item.project || '', category: item.category || 'labor',
      name: item.name || '', description: item.description || '',
      planned_amount: item.planned_amount || '', actual_amount: item.actual_amount || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('أدخل اسم البند'); return; }
    setSaving(true);
    try {
      const payload = { ...form, planned_amount: +form.planned_amount || 0, actual_amount: +form.actual_amount || 0 };
      if (editing) {
        await projectBudgetAPI.updateItem(editing.id, payload);
        toast.success('تم تحديث البند');
      } else {
        await projectBudgetAPI.createItem(payload);
        toast.success('تم إنشاء البند');
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await projectBudgetAPI.deleteItem(deleteTarget.id);
      toast.success('تم حذف البند');
      setDeleteTarget(null);
      fetchData();
    } catch {
      toast.error('خطأ في الحذف');
    }
  };

  const totalPlanned = items.reduce((s, i) => s + (i.planned_amount || 0), 0);
  const totalActual = items.reduce((s, i) => s + (i.actual_amount || 0), 0);
  const totalVariance = totalPlanned - totalActual;
  const healthPct = totalPlanned > 0 ? Math.round((totalActual / totalPlanned) * 100) : 0;

  const filtered = items.filter(i =>
    !search || i.name?.includes(search) || i.category?.includes(search)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <Wallet className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة ميزانيات المشاريع</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">تتبع المصروفات الفعلية مقابل المخططة</p>
          </div>
        </div>
        <button onClick={openCreate} disabled={!projectFilter} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm shadow-sm disabled:opacity-50">
          <Plus className="w-4 h-4" /> بند جديد
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث في البنود..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
          </div>
          <select value={projectFilter} onChange={e => setProjectFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">اختر مشروعاً</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      {projectFilter && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30"><DollarSign className="w-5 h-5 text-blue-600 dark:text-blue-400" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">المخطط</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(stats?.total_planned || totalPlanned)}</p></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900/30"><PieChart className="w-5 h-5 text-orange-600 dark:text-orange-400" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">الفعلي</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(stats?.total_actual || totalActual)}</p></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${totalVariance >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                {totalVariance >= 0 ? <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" /> : <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />}
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">الفرق</p>
                <p className={`text-lg font-bold ${totalVariance >= 0 ? 'text-green-600' : 'text-red-600'}`} dir="ltr">{fmt(totalVariance)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${healthPct <= 90 ? 'bg-green-100 dark:bg-green-900/30' : healthPct <= 100 ? 'bg-yellow-100 dark:bg-yellow-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                <Wallet className={`w-5 h-5 ${healthPct <= 90 ? 'text-green-600 dark:text-green-400' : healthPct <= 100 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`} />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">صحة الميزانية</p>
                <p className={`text-lg font-bold ${healthPct <= 90 ? 'text-green-600' : healthPct <= 100 ? 'text-yellow-600' : 'text-red-600'}`} dir="ltr">{healthPct}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {!projectFilter ? (
          <div className="p-12 text-center">
            <Wallet className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500">اختر مشروعاً لعرض ميزانيته</p>
          </div>
        ) : loading ? (
          <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Loader2 className="animate-spin" /> جاري التحميل...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <Wallet className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500">لا توجد بنود ميزانية</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-right font-medium">الفئة</th>
                  <th className="px-4 py-3 text-right font-medium">البند</th>
                  <th className="px-4 py-3 text-right font-medium">المخطط</th>
                  <th className="px-4 py-3 text-right font-medium">الفعلي</th>
                  <th className="px-4 py-3 text-right font-medium">الفرق</th>
                  <th className="px-4 py-3 text-right font-medium">النسبة</th>
                  <th className="px-4 py-3 text-right font-medium">إجراء</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(item => {
                  const planned = item.planned_amount || 0;
                  const actual = item.actual_amount || 0;
                  const variance = planned - actual;
                  const pct = planned > 0 ? Math.round((actual / planned) * 100) : 0;
                  const isOver = actual > planned;
                  return (
                    <tr key={item.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{CATEGORY_LABELS[item.category] || item.category}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{item.name}</td>
                      <td className="px-4 py-3" dir="ltr">{fmt(planned)}</td>
                      <td className={`px-4 py-3 ${isOver ? 'text-red-600 dark:text-red-400 font-semibold' : ''}`} dir="ltr">{fmt(actual)}</td>
                      <td className={`px-4 py-3 ${isOver ? 'text-red-600' : 'text-green-600'}`} dir="ltr">{variance >= 0 ? '+' : ''}{fmt(variance)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${pct <= 90 ? 'bg-green-500' : pct <= 100 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                          </div>
                          <span className={`text-xs ${pct > 100 ? 'text-red-600' : 'text-gray-500'}`} dir="ltr">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 flex gap-1">
                        <button onClick={() => openEdit(item)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button>
                        <button onClick={() => setDeleteTarget(item)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot className="bg-gray-50 dark:bg-gray-800/70 font-bold">
                <tr>
                  <td className="px-4 py-3" colSpan={2}><span className="text-gray-700 dark:text-gray-300">الإجمالي</span></td>
                  <td className="px-4 py-3 text-gray-900 dark:text-gray-100" dir="ltr">{fmt(totalPlanned)}</td>
                  <td className={`px-4 py-3 ${totalActual > totalPlanned ? 'text-red-600' : 'text-gray-900 dark:text-gray-100'}`} dir="ltr">{fmt(totalActual)}</td>
                  <td className={`px-4 py-3 ${totalVariance >= 0 ? 'text-green-600' : 'text-red-600'}`} dir="ltr">{totalVariance >= 0 ? '+' : ''}{fmt(totalVariance)}</td>
                  <td className="px-4 py-3" dir="ltr">{healthPct}%</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{editing ? 'تعديل البند' : 'إنشاء بند جديد'}</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم البند *</label>
                <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required className={ic} placeholder="مثال: أجور المهندسين" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الوصف</label>
                <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} className={ic} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المشروع *</label>
                  <select value={form.project} onChange={e => setForm({ ...form, project: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}>
                    <option value="">اختر</option>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الفئة</label>
                  <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
                    {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ المخطط</label>
                  <input type="number" step="0.01" min="0" value={form.planned_amount} onChange={e => setForm({ ...form, planned_amount: e.target.value })} className={ic} dir="ltr" placeholder="0.00" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ الفعلي</label>
                  <input type="number" step="0.01" min="0" value={form.actual_amount} onChange={e => setForm({ ...form, actual_amount: e.target.value })} className={ic} dir="ltr" placeholder="0.00" />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">
                  {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحفظ...</> : <><Save className="w-4 h-4" /> {editing ? 'تحديث' : 'إنشاء'}</>}
                </button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">حذف البند</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">هل أنت متأكد من حذف "{deleteTarget.name}"؟</p>
            <div className="flex gap-3 mt-5">
              <button onClick={handleDelete} className="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors">حذف</button>
              <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
