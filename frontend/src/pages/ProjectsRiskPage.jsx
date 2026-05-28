/**
 * Projects Risk Management Page - إدارة مخاطر المشاريع
 * Features: risk table, create/edit modal, risk matrix visual, filters.
 */

import { useState, useEffect, useCallback } from 'react';
import { projectsAPI, projectRisksAPI } from '../api';
import toast from 'react-hot-toast';
import {
  ShieldAlert, Plus, X, Edit3, Trash2, Search, Filter,
  Loader2, Save, AlertTriangle, Eye, ChevronDown,
} from 'lucide-react';

const RISK_SCORE_COLOR = (score) => {
  if (score <= 5) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
  if (score <= 10) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
  if (score <= 15) return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
  return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
};

const RISK_DOT_COLOR = (score) => {
  if (score <= 5) return 'bg-green-500';
  if (score <= 10) return 'bg-yellow-500';
  if (score <= 15) return 'bg-orange-500';
  return 'bg-red-500';
};

const MATRIX_COLOR = (p, i) => {
  const score = p * i;
  if (score <= 5) return 'bg-green-200 dark:bg-green-800';
  if (score <= 10) return 'bg-yellow-200 dark:bg-yellow-800';
  if (score <= 15) return 'bg-orange-300 dark:bg-orange-700';
  return 'bg-red-400 dark:bg-red-600';
};

const STATUS_LABELS = {
  open: 'مفتوح', mitigating: 'قيد المعالجة', closed: 'مغلق', accepted: 'مقبول',
};

const CATEGORY_LABELS = {
  technical: 'تقني', financial: 'مالي', operational: 'تشغيلي',
  strategic: 'استراتيجي', legal: 'قانوني', other: 'أخرى',
};

const STRATEGY_LABELS = {
  avoid: 'تجنب', mitigate: 'تخفيف', transfer: 'نقل', accept: 'قبول', exploit: 'استغلال',
};

const emptyRisk = {
  project: '', risk_name: '', description: '', category: 'technical',
  probability: 3, impact: 3, response_strategy: 'mitigate',
  owner: '', status: 'open', due_date: '',
};

export default function ProjectsRiskPage() {
  const [projects, setProjects] = useState([]);
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [projectFilter, setProjectFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyRisk);

  // Risk Matrix
  const [showMatrix, setShowMatrix] = useState(false);
  const [matrixData, setMatrixData] = useState(null);

  // Delete
  const [deleteTarget, setDeleteTarget] = useState(null);

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${RISK_SCORE_COLOR(s)}`;

  const fetchProjects = useCallback(async () => {
    try {
      const r = await projectsAPI.list({ page_size: 100 });
      setProjects(r.data.results || r.data || []);
    } catch (error) { console.error('Error:', error); }
  }, []);

  const fetchRisks = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (projectFilter) params.project = projectFilter;
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (search) params.search = search;
      const r = await projectRisksAPI.list(projectFilter || undefined);
      setRisks(r.data.results || r.data || []);
    } catch {
      toast.error('خطأ في تحميل المخاطر');
    } finally {
      setLoading(false);
    }
  }, [projectFilter, statusFilter, categoryFilter, search]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);
  useEffect(() => { fetchRisks(); }, [fetchRisks]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyRisk, project: projectFilter || '' });
    setShowModal(true);
  };

  const openEdit = (risk) => {
    setEditing(risk);
    setForm({
      project: risk.project || '', risk_name: risk.risk_name || '', description: risk.description || '',
      category: risk.category || 'technical', probability: risk.probability || 3,
      impact: risk.impact || 3, response_strategy: risk.response_strategy || 'mitigate',
      owner: risk.owner || '', status: risk.status || 'open', due_date: risk.due_date || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.risk_name.trim()) { toast.error('أدخل اسم الخطر'); return; }
    setSaving(true);
    try {
      const payload = { ...form, probability: +form.probability, impact: +form.impact };
      if (editing) {
        await projectRisksAPI.update(editing.id, payload);
        toast.success('تم تحديث الخطر');
      } else {
        await projectRisksAPI.create(payload);
        toast.success('تم إنشاء الخطر');
      }
      setShowModal(false);
      fetchRisks();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await projectRisksAPI.delete(deleteTarget.id);
      toast.success('تم حذف الخطر');
      setDeleteTarget(null);
      fetchRisks();
    } catch {
      toast.error('خطأ في الحذف');
    }
  };

  const viewMatrix = async () => {
    if (!projectFilter) { toast.error('اختر مشروعاً أولاً'); return; }
    try {
      const r = await projectRisksAPI.riskMatrix(projectFilter);
      setMatrixData(r.data);
      setShowMatrix(true);
    } catch {
      toast.error('خطأ في تحميل مصفوفة المخاطر');
    }
  };

  const MatrixModal = () => showMatrix && (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">مصفوفة المخاطر (5×5)</h3>
          <button onClick={() => setShowMatrix(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5">
          <div className="flex items-start gap-2">
            <div className="w-12" />
            {[1,2,3,4,5].map(i => (
              <div key={i} className="flex-1 text-center text-xs text-gray-500 dark:text-gray-400 mb-1">{i}</div>
            ))}
          </div>
          {[5,4,3,2,1].map(prob => (
            <div key={prob} className="flex items-center gap-2 mb-1">
              <div className="w-12 text-center text-xs text-gray-500 dark:text-gray-400">{prob}</div>
              {[1,2,3,4,5].map(imp => (
                <div key={`${prob}-${imp}`} className={`flex-1 aspect-square rounded flex items-center justify-center text-xs font-bold text-gray-700 dark:text-gray-200 ${MATRIX_COLOR(prob, imp)}`}>
                  {prob * imp}
                </div>
              ))}
            </div>
          ))}
          <div className="flex items-center gap-2 mt-3 text-xs">
            <span className="text-gray-500">← الاحتمالية</span>
            <span className="mr-auto text-gray-500">التأثير →</span>
          </div>
          <div className="flex gap-3 mt-4 text-xs">
            <div className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-400" /> منخفض (1-5)</div>
            <div className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-400" /> متوسط (6-10)</div>
            <div className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-orange-400" /> مرتفع (11-15)</div>
            <div className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500" /> حرج (16-25)</div>
          </div>
          {matrixData?.risks?.length > 0 && (
            <div className="mt-4 pt-4 border-t dark:border-gray-700">
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">المخاطر على المصفوفة:</p>
              <div className="space-y-1">
                {matrixData.risks.map((r, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <span className={`w-2 h-2 rounded-full ${RISK_DOT_COLOR(r.risk_score)}`} />
                    <span className="text-gray-900 dark:text-gray-100">{r.risk_name}</span>
                    <span className={badge(r.risk_score)}>{r.risk_score}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة مخاطر المشاريع</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">تحديد وتتبع وإدارة مخاطر المشاريع</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={viewMatrix} className="flex items-center gap-2 px-4 py-2.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm">
            <Eye className="w-4 h-4" /> مصفوفة المخاطر
          </button>
          <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm shadow-sm">
            <Plus className="w-4 h-4" /> خطر جديد
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث في المخاطر..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
          </div>
          <select value={projectFilter} onChange={e => setProjectFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل المشاريع</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الحالات</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الفئات</option>
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'إجمالي المخاطر', value: risks.length, color: 'text-red-600' },
          { label: 'مخاطر مفتوحة', value: risks.filter(r => r.status === 'open').length, color: 'text-yellow-600' },
          { label: 'قيد المعالجة', value: risks.filter(r => r.status === 'mitigating').length, color: 'text-blue-600' },
          { label: 'حرجة (16+)', value: risks.filter(r => (r.probability || 0) * (r.impact || 0) >= 16).length, color: 'text-red-600' },
        ].map((s, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Loader2 className="animate-spin" /> جاري التحميل...</div>
        ) : risks.length === 0 ? (
          <div className="p-12 text-center">
            <ShieldAlert className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500">لا توجد مخاطر مسجلة</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-right font-medium">الخطر</th>
                  <th className="px-4 py-3 text-right font-medium">الفئة</th>
                  <th className="px-4 py-3 text-right font-medium">الاحتمالية</th>
                  <th className="px-4 py-3 text-right font-medium">التأثير</th>
                  <th className="px-4 py-3 text-right font-medium">الدرجة</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                  <th className="px-4 py-3 text-right font-medium">الاستجابة</th>
                  <th className="px-4 py-3 text-right font-medium">المسؤول</th>
                  <th className="px-4 py-3 text-right font-medium">إجراء</th>
                </tr>
              </thead>
              <tbody>
                {risks.map(r => {
                  const score = (r.probability || 1) * (r.impact || 1);
                  return (
                    <tr key={r.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{r.risk_name}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{CATEGORY_LABELS[r.category] || r.category}</td>
                      <td className="px-4 py-3 text-center">{r.probability}</td>
                      <td className="px-4 py-3 text-center">{r.impact}</td>
                      <td className="px-4 py-3"><span className={badge(score)}>{score}</span></td>
                      <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs ${r.status === 'open' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' : r.status === 'closed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}`}>{STATUS_LABELS[r.status] || r.status}</span></td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{STRATEGY_LABELS[r.response_strategy] || r.response_strategy}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{r.owner || '-'}</td>
                      <td className="px-4 py-3 flex gap-1">
                        <button onClick={() => openEdit(r)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button>
                        <button onClick={() => setDeleteTarget(r)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{editing ? 'تعديل الخطر' : 'إنشاء خطر جديد'}</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الخطر *</label>
                <input type="text" value={form.risk_name} onChange={e => setForm({ ...form, risk_name: e.target.value })} required className={ic} placeholder="وصف الخطر" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الوصف</label>
                <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} className={ic} placeholder="تفاصيل إضافية" />
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
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الاحتمالية (1-5)</label>
                  <input type="number" min="1" max="5" value={form.probability} onChange={e => setForm({ ...form, probability: e.target.value })} className={ic} dir="ltr" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التأثير (1-5)</label>
                  <input type="number" min="1" max="5" value={form.impact} onChange={e => setForm({ ...form, impact: e.target.value })} className={ic} dir="ltr" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الدرجة</label>
                  <div className={`px-3 py-2.5 rounded-lg text-center font-bold ${RISK_SCORE_COLOR((+form.probability || 1) * (+form.impact || 1))}`}>
                    {(+form.probability || 1) * (+form.impact || 1)}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">استراتيجية الاستجابة</label>
                  <select value={form.response_strategy} onChange={e => setForm({ ...form, response_strategy: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
                    {Object.entries(STRATEGY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحالة</label>
                  <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
                    {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المسؤول</label>
                  <input type="text" value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} className={ic} placeholder="اسم المسؤول" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الاستحقاق</label>
                  <input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} className={ic} />
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
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">حذف الخطر</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">هل أنت متأكد من حذف "{deleteTarget.risk_name}"؟</p>
            <div className="flex gap-3 mt-5">
              <button onClick={handleDelete} className="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors">حذف</button>
              <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
            </div>
          </div>
        </div>
      )}

      <MatrixModal />
    </div>
  );
}
