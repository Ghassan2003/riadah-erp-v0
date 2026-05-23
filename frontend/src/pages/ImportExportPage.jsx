/**
 * Import/Export Management page - Operations module.
 * Manage import orders, export orders, and customs declarations.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { importExportAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Edit2, Trash2,
  Download, Upload, FileCheck, DollarSign, RefreshCw, Truck, Ship,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  in_transit: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  delivered: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  customs_pending: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  customs_cleared: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  customs_hold: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  shipped: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};
const SL = {
  draft: 'مسودة', pending: 'معلّق', approved: 'معتمد', rejected: 'مرفوض',
  in_transit: 'قيد الشحن', delivered: 'تم التسليم', cancelled: 'ملغى',
  customs_pending: 'معلّق جمركي', customs_cleared: 'مخلى جمركياً', customs_hold: 'محتجز جمركياً',
  shipped: 'تم الشحن', processing: 'قيد المعالجة', completed: 'مكتمل',
};

const TABS = [
  { id: 'imports', name: 'الاستيراد', icon: Download },
  { id: 'exports', name: 'التصدير', icon: Upload },
  { id: 'customs', name: 'الجمارك', icon: FileCheck },
];
const STATS = [
  { key: 'total_imports', label: 'أوامر الاستيراد', icon: Download, color: 'from-blue-500 to-blue-600' },
  { key: 'total_exports', label: 'أوامر التصدير', icon: Upload, color: 'from-emerald-500 to-emerald-600' },
  { key: 'customs_pending', label: 'إقرارات معلّقة', icon: FileCheck, color: 'from-amber-500 to-amber-600' },
  { key: 'total_value', label: 'إجمالي القيمة', icon: DollarSign, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function ImportExportPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('imports');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [imports, setImports] = useState([]);
  const [exports, setExports] = useState([]);
  const [customs, setCustoms] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ imp: false, exp: false, status: false });
  const [selRec, setSelRec] = useState(null);
  const [impForm, setImpForm] = useState({ supplier: '', port: '', country: '', total_amount: '', expected_arrival: '' });
  const [expForm, setExpForm] = useState({ customer: '', destination_country: '', total_amount: '', ship_date: '' });
  const [newStatus, setNewStatus] = useState('');

  const isAdmin = JSON.parse(localStorage.getItem('user') || '{}')?.role === 'admin';
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await importExportAPI.getStats()).data); } catch {} })(); }, []);

  useEffect(() => {
    const fetchTab = async () => {
      setLd(true);
      try {
        if (tab === 'imports') setImports((await importExportAPI.getImportOrders({ search, status: sFilter })).data.results || []);
        else if (tab === 'exports') setExports((await importExportAPI.getExportOrders({ search, status: sFilter })).data.results || []);
        else setCustoms((await importExportAPI.getCustomsDeclarations({ search, status: sFilter })).data.results || []);
      } catch { toast.error('خطأ في تحميل البيانات'); } finally { setLd(false); }
    };
    fetchTab();
  }, [tab, search, sFilter]);

  const hCreateImport = async (e) => { e.preventDefault(); setSv(true); try { await importExportAPI.createImportOrder({ ...impForm, total_amount: +impForm.total_amount }); toast.success('تم إنشاء أمر الاستيراد بنجاح'); setModals({ ...modals, imp: false }); setImpForm({ supplier: '', port: '', country: '', total_amount: '', expected_arrival: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateExport = async (e) => { e.preventDefault(); setSv(true); try { await importExportAPI.createExportOrder({ ...expForm, total_amount: +expForm.total_amount }); toast.success('تم إنشاء أمر التصدير بنجاح'); setModals({ ...modals, exp: false }); setExpForm({ customer: '', destination_country: '', total_amount: '', ship_date: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hChangeStatus = async (e) => { e.preventDefault(); if (!selRec) return; setSv(true); try { await importExportAPI.changeImportStatus(selRec.id, { status: newStatus }); toast.success('تم تحديث الحالة بنجاح'); setModals({ ...modals, status: false }); } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); } finally { setSv(false); } };
  const hDeleteImport = async (id) => { if (!confirm('هل أنت متأكد من حذف أمر الاستيراد؟')) return; try { await importExportAPI.changeImportStatus(id, { status: 'cancelled' }); toast.success('تم الحذف بنجاح'); setImports((prev) => prev.filter(i => i.id !== id)); } catch { toast.error('خطأ في الحذف'); } };
  const hDeleteExport = async (id) => { if (!confirm('هل أنت متأكد من حذف أمر التصدير؟')) return; try { await importExportAPI.changeExportStatus(id, { status: 'cancelled' }); toast.success('تم الحذف بنجاح'); setExports((prev) => prev.filter(ex => ex.id !== id)); } catch { toast.error('خطأ في الحذف'); } };

  const openStatusModal = (rec, currentStatus, type) => {
    setSelRec({ ...rec, _type: type });
    setNewStatus(currentStatus);
    setModals({ ...modals, status: true });
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

  const getStatusOptions = (type) => {
    if (type === 'imports') return ['draft', 'pending', 'approved', 'customs_pending', 'in_transit', 'delivered', 'cancelled'];
    if (type === 'exports') return ['draft', 'pending', 'approved', 'shipped', 'delivered', 'cancelled'];
    return ['pending', 'customs_pending', 'customs_cleared', 'customs_hold', 'completed'];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الاستيراد والتصدير</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة أوامر الاستيراد والتصدير والإقرارات الجمركية</p>
        </div>
        <div className="flex gap-2">
          {tab === 'imports' && isAdmin && <button onClick={() => setModals({ ...modals, imp: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> أمر استيراد جديد</button>}
          {tab === 'exports' && isAdmin && <button onClick={() => setModals({ ...modals, exp: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> أمر تصدير جديد</button>}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{key === 'total_value' ? fm(stats[key]) : (stats[key] || '-')}</p></div>
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
            {(tab === 'imports' ? ['draft','pending','approved','customs_pending','in_transit','delivered','cancelled'] : tab === 'exports' ? ['draft','pending','approved','shipped','delivered','cancelled'] : ['pending','customs_pending','customs_cleared','customs_hold','completed']).map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── Imports Tab ─── */}
      {tab === 'imports' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : imports.length === 0 ? <div className="p-12 text-center"><Download className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد أوامر استيراد</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الأمر</Th><Th>المورّد</Th><Th>الميناء</Th><Th>البلد</Th><Th>الحالة</Th><Th>المبلغ الإجمالي</Th><Th>الرسوم</Th><Th>التكلفة الإجمالية</Th><Th>تاريخ الوصول المتوقع</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{imports.map(i => (
                <tr key={i.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-500">{i.order_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{i.supplier}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{i.port}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{i.country}</td>
                  <td className="px-4 py-3"><span className={badge(i.status)}>{SL[i.status]}</span></td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(i.total_amount)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(i.duties)}</td>
                  <td className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">{fm(i.landed_cost)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{i.expected_arrival || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => openStatusModal(i, i.status, 'imports')} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="تغيير الحالة"><Edit2 className="w-4 h-4" /></button>
                    {isAdmin && <button onClick={() => hDeleteImport(i.id)} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="حذف"><Trash2 className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Exports Tab ─── */}
      {tab === 'exports' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : exports.length === 0 ? <div className="p-12 text-center"><Upload className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد أوامر تصدير</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الأمر</Th><Th>العميل</Th><Th>بلد الوجهة</Th><Th>الحالة</Th><Th>المبلغ الإجمالي</Th><Th>تاريخ الشحن</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{exports.map(ex => (
                <tr key={ex.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-500">{ex.order_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{ex.customer}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{ex.destination_country}</td>
                  <td className="px-4 py-3"><span className={badge(ex.status)}>{SL[ex.status]}</span></td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(ex.total_amount)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{ex.ship_date || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button onClick={() => openStatusModal(ex, ex.status, 'exports')} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="تغيير الحالة"><Edit2 className="w-4 h-4" /></button>
                    {isAdmin && <button onClick={() => hDeleteExport(ex.id)} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="حذف"><Trash2 className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Customs Tab ─── */}
      {tab === 'customs' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : customs.length === 0 ? <div className="p-12 text-center"><FileCheck className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد إقرارات جمركية</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الإقرار</Th><Th>النوع</Th><Th>الحالة</Th><Th>القيمة المصرّحة</Th><Th>الرسوم</Th><Th>الضرائب</Th><Th>تاريخ التقديم</Th>
              </tr></thead>
              <tbody>{customs.map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-500">{c.declaration_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.type === 'import' ? 'استيراد' : 'تصدير'}</td>
                  <td className="px-4 py-3"><span className={badge(c.status)}>{SL[c.status]}</span></td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(c.declared_value)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(c.duties)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{fm(c.taxes)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.submitted_date || '-'}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="imp" title="إنشاء أمر استيراد جديد"><form onSubmit={hCreateImport} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المورّد *</label><input type="text" value={impForm.supplier} onChange={e => setImpForm({ ...impForm, supplier: e.target.value })} required placeholder="اسم المورّد" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الميناء *</label><input type="text" value={impForm.port} onChange={e => setImpForm({ ...impForm, port: e.target.value })} required placeholder="مثال: ميناء جدة الإسلامي" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">البلد *</label><input type="text" value={impForm.country} onChange={e => setImpForm({ ...impForm, country: e.target.value })} required placeholder="الصين" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ الإجمالي *</label><input type="number" step="0.01" value={impForm.total_amount} onChange={e => setImpForm({ ...impForm, total_amount: e.target.value })} required placeholder="0.00" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الوصول المتوقع *</label><input type="date" value={impForm.expected_arrival} onChange={e => setImpForm({ ...impForm, expected_arrival: e.target.value })} required className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="imp" /></div>
      </form></Modal>

      <Modal k="exp" title="إنشاء أمر تصدير جديد"><form onSubmit={hCreateExport} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">العميل *</label><input type="text" value={expForm.customer} onChange={e => setExpForm({ ...expForm, customer: e.target.value })} required placeholder="اسم العميل" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">بلد الوجهة *</label><input type="text" value={expForm.destination_country} onChange={e => setExpForm({ ...expForm, destination_country: e.target.value })} required placeholder="مثال: الإمارات" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ الإجمالي *</label><input type="number" step="0.01" value={expForm.total_amount} onChange={e => setExpForm({ ...expForm, total_amount: e.target.value })} required placeholder="0.00" className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الشحن *</label><input type="date" value={expForm.ship_date} onChange={e => setExpForm({ ...expForm, ship_date: e.target.value })} required className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="exp" /></div>
      </form></Modal>

      <Modal k="status" title={`تغيير الحالة: ${selRec?.order_number || selRec?.declaration_number || ''}`}><form onSubmit={hChangeStatus} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحالة الحالية</label><div className="mt-1"><span className={badge(selRec?.status)}>{SL[selRec?.status]}</span></div></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحالة الجديدة *</label>
          <select value={newStatus} onChange={e => setNewStatus(e.target.value)} required className={`${ic} bg-white dark:bg-gray-700`}>
            {getStatusOptions(selRec?._type).map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
        <div className="flex gap-3 pt-2"><Btn>تحديث</Btn><CancelBtn k="status" /></div>
      </form></Modal>
    </div>
  );
}
