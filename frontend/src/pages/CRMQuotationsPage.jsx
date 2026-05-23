/**
 * CRM Quotations Page - عروض الأسعار
 * Features: quotations table, create with line items, detail, convert to order.
 */

import { useState, useEffect, useCallback } from 'react';
import { crmAPI } from '../api';
import toast from 'react-hot-toast';
import {
  FileText, Plus, X, Search, Loader2, Save, AlertTriangle,
  Eye, Trash2, RefreshCw, ArrowLeftRight,
} from 'lucide-react';

const STATUS_CFG = {
  draft: { label: 'مسودة', cls: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  sent: { label: 'مرسلة', cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  approved: { label: 'مقبولة', cls: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  rejected: { label: 'مرفوضة', cls: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  expired: { label: 'منتهية', cls: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  converted: { label: 'تم التحويل', cls: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
};

const emptyLine = { description: '', quantity: 1, unit_price: 0 };

const emptyForm = {
  company: '', contact: '', valid_until: '', notes: '',
  items: [{ ...emptyLine }],
};

export default function CRMQuotationsPage() {
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const [selected, setSelected] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const nl = 'ar-SA';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';

  const fetchQuotations = useCallback(async () => {
    setLoading(true);
    try {
      const params = { search: search || undefined, status: statusFilter || undefined };
      const r = await crmAPI.quotations(params);
      setQuotations(r.data.results || r.data || []);
    } catch {
      toast.error('خطأ في تحميل عروض الأسعار');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => { fetchQuotations(); }, [fetchQuotations]);

  const totalForm = () => (form.items || []).reduce((s, i) => s + (i.quantity * i.unit_price), 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company.trim()) { toast.error('أدخل اسم الشركة'); return; }
    setSaving(true);
    try {
      await crmAPI.createQuotation({ ...form, items: form.items.map(i => ({ ...i, quantity: +i.quantity, unit_price: +i.unit_price })) });
      toast.success('تم إنشاء العرض');
      setShowModal(false);
      setForm(emptyForm);
      fetchQuotations();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await crmAPI.deleteQuotation(deleteTarget.id);
      toast.success('تم حذف العرض');
      setDeleteTarget(null);
      fetchQuotations();
    } catch { toast.error('خطأ في الحذف'); }
  };

  const handleConvert = async (q) => {
    try {
      await crmAPI.convertQuotation(q.id);
      toast.success('تم تحويل العرض إلى طلب');
      fetchQuotations();
    } catch {
      toast.error('خطأ في التحويل');
    }
  };

  const addLine = () => setForm({ ...form, items: [...form.items, { ...emptyLine }] });
  const removeLine = (idx) => setForm({ ...form, items: form.items.filter((_, i) => i !== idx) });
  const updateLine = (idx, field, value) => {
    const items = [...form.items];
    items[idx] = { ...items[idx], [field]: value };
    setForm({ ...form, items });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center">
            <FileText className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">عروض الأسعار</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">إنشاء وإدارة عروض الأسعار للعملاء</p>
          </div>
        </div>
        <button onClick={() => { setForm(emptyForm); setShowModal(true); }} className="flex items-center gap-2 px-4 py-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-sm shadow-sm">
          <Plus className="w-4 h-4" /> عرض سعر جديد
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none text-sm" />
          </div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الحالات</option>
            {Object.entries(STATUS_CFG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Loader2 className="animate-spin" /> جاري التحميل...</div>
        ) : quotations.length === 0 ? (
          <div className="p-12 text-center"><FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد عروض أسعار</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-right font-medium">الرقم</th>
                  <th className="px-4 py-3 text-right font-medium">الشركة</th>
                  <th className="px-4 py-3 text-right font-medium">المجموع الفرعي</th>
                  <th className="px-4 py-3 text-right font-medium">الإجمالي</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                  <th className="px-4 py-3 text-right font-medium">صالح حتى</th>
                  <th className="px-4 py-3 text-right font-medium">إجراء</th>
                </tr>
              </thead>
              <tbody>
                {quotations.map(q => (
                  <tr key={q.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-teal-600 dark:text-teal-400 text-xs" dir="ltr">#{q.quote_number || q.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{q.company_name || q.company || '-'}</td>
                    <td className="px-4 py-3" dir="ltr">{fmt(q.subtotal)}</td>
                    <td className="px-4 py-3 font-semibold" dir="ltr">{fmt(q.total)}</td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CFG[q.status]?.cls || ''}`}>{STATUS_CFG[q.status]?.label || q.status}</span></td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{q.valid_until || '-'}</td>
                    <td className="px-4 py-3 flex gap-1">
                      <button onClick={() => { setSelected(q); setShowDetail(true); }} className="p-1.5 text-teal-500 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-lg"><Eye className="w-4 h-4" /></button>
                      {(q.status === 'approved' || q.status === 'sent') && (
                        <button onClick={() => handleConvert(q)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg" title="تحويل لطلب"><RefreshCw className="w-4 h-4" /></button>
                      )}
                      <button onClick={() => setDeleteTarget(q)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">عرض سعر جديد</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الشركة *</label><input type="text" value={form.company} onChange={e => setForm({ ...form, company: e.target.value })} required className={ic} placeholder="اسم الشركة" /></div>
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">صالح حتى</label><input type="date" value={form.valid_until} onChange={e => setForm({ ...form, valid_until: e.target.value })} className={ic} /></div>
              </div>

              {/* Line Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">البنود</label>
                  <button type="button" onClick={addLine} className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"><Plus className="w-3 h-3" /> إضافة بند</button>
                </div>
                <div className="space-y-2">
                  {form.items.map((item, idx) => (
                    <div key={idx} className="flex gap-2 items-start">
                      <input type="text" value={item.description} onChange={e => updateLine(idx, 'description', e.target.value)} placeholder="الوصف" className="flex-1 min-w-0 px-2.5 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg outline-none focus:ring-1 focus:ring-teal-500" />
                      <input type="number" min="1" value={item.quantity} onChange={e => updateLine(idx, 'quantity', e.target.value)} placeholder="الكمية" className="w-20 px-2 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg outline-none focus:ring-1 focus:ring-teal-500 text-center" dir="ltr" />
                      <input type="number" min="0" step="0.01" value={item.unit_price || ''} onChange={e => updateLine(idx, 'unit_price', e.target.value)} placeholder="السعر" className="w-28 px-2 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg outline-none focus:ring-1 focus:ring-teal-500 text-center" dir="ltr" />
                      {form.items.length > 1 && (
                        <button type="button" onClick={() => removeLine(idx)} className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><X className="w-4 h-4" /></button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="text-left mt-2 text-sm text-gray-700 dark:text-gray-300 font-medium">الإجمالي: <span dir="ltr">{fmt(totalForm())}</span> ر.س</div>
              </div>

              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">ملاحظات</label><textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} rows={2} className={ic} /></div>

              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{saving ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحفظ...</> : <><Save className="w-4 h-4" /> إنشاء</>}</button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && selected && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">عرض #{selected.quote_number || selected.id}</h3>
                <div className="flex gap-2 mt-1">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_CFG[selected.status]?.cls || ''}`}>{STATUS_CFG[selected.status]?.label || selected.status}</span>
                </div>
              </div>
              <button onClick={() => { setShowDetail(false); setSelected(null); }} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-gray-500 dark:text-gray-400">الشركة:</span> <span className="font-medium text-gray-900 dark:text-gray-100 mr-1">{selected.company_name || selected.company || '-'}</span></div>
                <div><span className="text-gray-500 dark:text-gray-400">صالح حتى:</span> <span className="font-medium text-gray-900 dark:text-gray-100 mr-1">{selected.valid_until || '-'}</span></div>
              </div>
              {selected.items?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">البنود</h4>
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs"><tr><th className="px-3 py-2 text-right">الوصف</th><th className="px-3 py-2 text-right">الكمية</th><th className="px-3 py-2 text-right">السعر</th><th className="px-3 py-2 text-right">المجموع</th></tr></thead>
                      <tbody>{selected.items.map((item, i) => (
                        <tr key={i} className="border-t border-gray-200 dark:border-gray-600"><td className="px-3 py-2">{item.description}</td><td className="px-3 py-2 text-center" dir="ltr">{item.quantity}</td><td className="px-3 py-2" dir="ltr">{fmt(item.unit_price)}</td><td className="px-3 py-2 font-medium" dir="ltr">{fmt(item.quantity * item.unit_price)}</td></tr>
                      ))}</tbody>
                      <tfoot className="bg-gray-100 dark:bg-gray-700 font-bold"><tr><td className="px-3 py-2" colSpan={3}>الإجمالي</td><td className="px-3 py-2" dir="ltr">{fmt(selected.total)}</td></tr></tfoot>
                    </table>
                  </div>
                </div>
              )}
              {selected.notes && <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-sm text-gray-600 dark:text-gray-300">{selected.notes}</div>}
              {(selected.status === 'approved' || selected.status === 'sent') && (
                <button onClick={() => handleConvert(selected)} className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"><ArrowLeftRight className="w-4 h-4" /> تحويل إلى طلب</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">حذف العرض</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">هل أنت متأكد؟</p>
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
