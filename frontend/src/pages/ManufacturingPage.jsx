/**
 * Manufacturing & Production page - ERP module.
 * Manage BOMs, production orders, and work centers.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { manufacturingAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Play, Factory,
  FileText, ClipboardList, Clock, AlertCircle, Settings,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  planned: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  on_hold: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  maintenance: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
};
const SL = {
  draft: 'مسودة', active: 'نشط', inactive: 'غير نشط',
  planned: 'مخطط', in_progress: 'قيد التنفيذ', completed: 'مكتمل',
  cancelled: 'ملغى', on_hold: 'معلّق',
  high: 'عالية', medium: 'متوسطة', low: 'منخفضة',
  maintenance: 'صيانة',
};

const TABS = [
  { id: 'boms', name: 'قوائم المواد', icon: FileText },
  { id: 'orders', name: 'أوامر الإنتاج', icon: ClipboardList },
  { id: 'work_centers', name: 'مراكز العمل', icon: Factory },
];
const STATS = [
  { key: 'total_boms', label: 'قوائم المواد', icon: FileText, color: 'from-blue-500 to-blue-600' },
  { key: 'active_orders', label: 'أوامر نشطة', icon: Play, color: 'from-emerald-500 to-emerald-600' },
  { key: 'completed_orders', label: 'مكتملة', icon: Check, color: 'from-amber-500 to-amber-600' },
  { key: 'work_centers', label: 'مراكز العمل', icon: Factory, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function ManufacturingPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('boms');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [boms, setBoms] = useState([]);
  const [orders, setOrders] = useState([]);
  const [workCenters, setWorkCenters] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ bom: false, order: false });
  const [bomForm, setBomForm] = useState({ product: '', name: '', version: '', effective_date: '' });
  const [orderForm, setOrderForm] = useState({ product: '', quantity: '', priority: 'medium', planned_start: '' });

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await manufacturingAPI.getStats()).data); } catch {} })(); }, []);

  useEffect(() => {
    (async () => {
      setLd(true);
      try {
        if (tab === 'boms') setBoms((await manufacturingAPI.getBOMs({ search, status: sFilter })).data.results || []);
        else if (tab === 'orders') setOrders((await manufacturingAPI.getOrders({ search, status: sFilter })).data.results || []);
        else if (tab === 'work_centers') setWorkCenters((await manufacturingAPI.getWorkCenters({ search, status: sFilter })).data.results || []);
      } catch { toast.error('خطأ في تحميل البيانات'); } finally { setLd(false); }
    })();
  }, [tab, search, sFilter]);

  const hCreateBom = async (e) => {
    e.preventDefault(); setSv(true);
    try { await manufacturingAPI.createBOM(bomForm); toast.success('تم إنشاء قائمة المواد بنجاح'); setModals({ ...modals, bom: false }); setBomForm({ product: '', name: '', version: '', effective_date: '' }); }
    catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); }
  };
  const hCreateOrder = async (e) => {
    e.preventDefault(); setSv(true);
    try { await manufacturingAPI.createOrder({ ...orderForm, quantity: +orderForm.quantity }); toast.success('تم إنشاء أمر الإنتاج بنجاح'); setModals({ ...modals, order: false }); setOrderForm({ product: '', quantity: '', priority: 'medium', planned_start: '' }); }
    catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); }
  };
  const hStartOrder = async (id) => {
    try { await manufacturingAPI.startOrder(id); toast.success('تم بدء أمر الإنتاج'); setOrders((await manufacturingAPI.getOrders({ search, status: sFilter })).data.results || []); }
    catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };
  const hCompleteOrder = async (id) => {
    try { await manufacturingAPI.completeOrder(id); toast.success('تم إكمال أمر الإنتاج'); setOrders((await manufacturingAPI.getOrders({ search, status: sFilter })).data.results || []); }
    catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };
  const hCancelOrder = async (id) => {
    try { await manufacturingAPI.cancelOrder(id); toast.success('تم إلغاء أمر الإنتاج'); setOrders((await manufacturingAPI.getOrders({ search, status: sFilter })).data.results || []); }
    catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
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

  const statusOptions = tab === 'boms' ? ['draft', 'active', 'inactive']
    : tab === 'orders' ? ['planned', 'in_progress', 'completed', 'cancelled', 'on_hold']
    : ['active', 'inactive', 'maintenance'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">التصنيع والإنتاج</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة قوائم المواد، أوامر الإنتاج، ومراكز العمل</p>
        </div>
        <div className="flex gap-2">
          {tab === 'boms' && <button onClick={() => setModals({ ...modals, bom: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> قائمة مواد جديدة</button>}
          {tab === 'orders' && <button onClick={() => setModals({ ...modals, order: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> أمر إنتاج جديد</button>}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{stats[key] || '-'}</p></div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {TABS.map(t => { const I = t.icon; return <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}><I className="w-4 h-4" /> {t.name}</button>; })}
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
          </div>
          <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الحالات</option>
            {statusOptions.map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── BOMs Tab ─── */}
      {tab === 'boms' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : boms.length === 0 ? <div className="p-12 text-center"><FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد قوائم مواد</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>المنتج</Th><Th>الاسم</Th><Th>الإصدار</Th><Th>الحالة</Th><Th>تاريخ السريان</Th><Th>عدد المواد</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{boms.map(b => (
                <tr key={b.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{b.product_name || b.product}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.version}</td>
                  <td className="px-4 py-3"><span className={badge(b.status)}>{SL[b.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.effective_date || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.items_count || 0}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Orders Tab ─── */}
      {tab === 'orders' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : orders.length === 0 ? <div className="p-12 text-center"><ClipboardList className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد أوامر إنتاج</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الأمر</Th><Th>المنتج</Th><Th>الكمية</Th><Th>المنتج</Th><Th>الحالة</Th><Th>الأولوية</Th><Th>تاريخ البدء</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{orders.map(o => (
                <tr key={o.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-medium text-gray-900 dark:text-gray-100">{o.order_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{o.product_name || o.product}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{o.quantity}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{o.produced || 0}</td>
                  <td className="px-4 py-3"><span className={badge(o.status)}>{SL[o.status]}</span></td>
                  <td className="px-4 py-3"><span className={badge(o.priority)}>{SL[o.priority]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{o.planned_start || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {o.status === 'planned' && <button onClick={() => hStartOrder(o.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="بدء"><Play className="w-4 h-4" /></button>}
                    {o.status === 'in_progress' && <button onClick={() => hCompleteOrder(o.id)} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="إكمال"><Check className="w-4 h-4" /></button>}
                    {(o.status === 'planned' || o.status === 'in_progress') && <button onClick={() => hCancelOrder(o.id)} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="إلغاء"><Ban className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Work Centers Tab ─── */}
      {tab === 'work_centers' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : workCenters.length === 0 ? <div className="p-12 text-center"><Factory className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد مراكز عمل</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>الموقع</Th><Th>السعة</Th><Th>الحالة</Th><Th>التكلفة/ساعة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{workCenters.map(wc => (
                <tr key={wc.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{wc.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{wc.location || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{wc.capacity || '-'}</td>
                  <td className="px-4 py-3"><span className={badge(wc.status)}>{SL[wc.status]}</span></td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(wc.cost_per_hour)}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    <button className="text-gray-500 dark:text-gray-400 p-1.5 rounded hover:bg-gray-50 dark:hover:bg-gray-700/20" title="إعدادات"><Settings className="w-4 h-4" /></button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="bom" title="إنشاء قائمة مواد جديدة"><form onSubmit={hCreateBom} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المنتج *</label><input type="text" value={bomForm.product} onChange={e => setBomForm({ ...bomForm, product: e.target.value })} required placeholder="معرف المنتج" className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم القائمة *</label><input type="text" value={bomForm.name} onChange={e => setBomForm({ ...bomForm, name: e.target.value })} required placeholder="مثال: قائمة تصنيع المنتج أ" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الإصدار *</label><input type="text" value={bomForm.version} onChange={e => setBomForm({ ...bomForm, version: e.target.value })} required placeholder="1.0" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ السريان</label><input type="date" value={bomForm.effective_date} onChange={e => setBomForm({ ...bomForm, effective_date: e.target.value })} className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="bom" /></div>
      </form></Modal>

      <Modal k="order" title="إنشاء أمر إنتاج جديد"><form onSubmit={hCreateOrder} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المنتج *</label><input type="text" value={orderForm.product} onChange={e => setOrderForm({ ...orderForm, product: e.target.value })} required placeholder="معرف المنتج" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الكمية *</label><input type="number" value={orderForm.quantity} onChange={e => setOrderForm({ ...orderForm, quantity: e.target.value })} required min="1" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأولوية</label><select value={orderForm.priority} onChange={e => setOrderForm({ ...orderForm, priority: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option>
          </select></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ البدء المخطط</label><input type="date" value={orderForm.planned_start} onChange={e => setOrderForm({ ...orderForm, planned_start: e.target.value })} className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="order" /></div>
      </form></Modal>
    </div>
  );
}
