import { useState, useEffect } from 'react';
import { shippingAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Truck, Route, Navigation, CheckCircle, Plus, Search, X,
  Eye, Download, RefreshCw
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  in_transit: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  delivered: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  returned: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};
const SL = {
  pending: 'معلّق', processing: 'قيد التحضير', in_transit: 'قيد النقل',
  delivered: 'مسلّم', returned: 'مرتجع', cancelled: 'ملغي',
  active: 'نشط', inactive: 'غير نشط',
};

const TABS = [
  { id: 'shipments', name: 'الشحنات', icon: Truck },
  { id: 'methods', name: 'طرق الشحن', icon: Route },
];
const STATS = [
  { key: 'total_shipments', label: 'إجمالي الشحنات', icon: Truck, color: 'from-blue-500 to-blue-600' },
  { key: 'in_transit', label: 'قيد النقل', icon: Navigation, color: 'from-emerald-500 to-emerald-600' },
  { key: 'delivered', label: 'المسلّمة', icon: CheckCircle, color: 'from-amber-500 to-amber-600' },
  { key: 'total_methods', label: 'طرق الشحن', icon: Route, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function ShippingPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('shipments');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [shipments, setShipments] = useState([]);
  const [methods, setMethods] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ shipment: false, method: false });
  const [shForm, setShForm] = useState({ customer: '', method: '', tracking_number: '', shipping_cost: '', estimated_delivery: '' });
  const [mtForm, setMtForm] = useState({ name: '', carrier: '', cost_type: 'fixed', base_cost: '', estimated_days: '' });

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await shippingAPI.getStats()).data); } catch {} })(); }, []);
  useEffect(() => { (async () => { setLd(true); try { setShipments((await shippingAPI.getShipments({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل الشحنات'); } finally { setLd(false); } })(); }, [search, sFilter]);
  useEffect(() => { (async () => { if (tab === 'methods') { setLd(true); try { setMethods((await shippingAPI.getMethods({ search })).data.results || []); } catch { toast.error('خطأ في تحميل طرق الشحن'); } finally { setLd(false); } } })(); }, [tab, search]);

  const hCreateShipment = async (e) => { e.preventDefault(); setSv(true); try { await shippingAPI.createShipment({ ...shForm, shipping_cost: +shForm.shipping_cost }); toast.success('تم إنشاء الشحنة بنجاح'); setModals({ ...modals, shipment: false }); setShForm({ customer: '', method: '', tracking_number: '', shipping_cost: '', estimated_delivery: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateMethod = async (e) => { e.preventDefault(); setSv(true); try { await shippingAPI.createMethod({ ...mtForm, base_cost: +mtForm.base_cost, estimated_days: +mtForm.estimated_days }); toast.success('تم إنشاء طريقة الشحن بنجاح'); setModals({ ...modals, method: false }); setMtForm({ name: '', carrier: '', cost_type: 'fixed', base_cost: '', estimated_days: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hChangeStatus = async (id, status) => { try { await shippingAPI.changeStatus(id, { status }); toast.success('تم تغيير حالة الشحنة'); setShipments((await shippingAPI.getShipments({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تغيير الحالة'); } };
  const hToggleMethod = async (id, isActive) => { try { await shippingAPI.toggleMethod(id, { is_active: !isActive }); toast.success(isActive ? 'تم تعطيل الطريقة' : 'تم تفعيل الطريقة'); setMethods((await shippingAPI.getMethods({ search })).data.results || []); } catch { toast.error('خطأ'); } };
  const hExport = async () => { try { const r = await shippingAPI.export(); const u = window.URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = u; a.download = 'shipments.xlsx'; document.body.appendChild(a); a.click(); a.remove(); toast.success('تم التصدير'); } catch { toast.error('خطأ في التصدير'); } };

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الشحن والتوصيل</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة الشحنات وطرق الشحن والتتبع</p>
        </div>
        <div className="flex gap-2">
          <button onClick={hExport} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm text-sm"><Download className="w-4 h-4" /> تصدير</button>
          <button onClick={() => setModals({ ...modals, [tab === 'shipments' ? 'shipment' : 'method']: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> {tab === 'shipments' ? 'شحنة جديدة' : 'طريقة شحن جديدة'}</button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ key, label, icon: I, color }) => (
          <div key={key} className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`absolute top-0 ${locale === 'ar' ? 'left-0' : 'right-0'} w-20 h-20 bg-gradient-to-br ${color} opacity-10 rounded-bl-full`} />
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} text-white`}><I className="w-5 h-5" /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{stats[key] ?? '-'}</p></div>
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
          {tab === 'shipments' && (
            <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
              <option value="">كل الحالات</option>
              {['pending', 'processing', 'in_transit', 'delivered', 'returned', 'cancelled'].map(s => <option key={s} value={s}>{SL[s]}</option>)}
            </select>
          )}
        </div>
      </div>

      {/* ─── Shipments Tab ─── */}
      {tab === 'shipments' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : shipments.length === 0 ? <div className="p-12 text-center"><Truck className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد شحنات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الشحنة</Th><Th>العميل</Th><Th>طريقة الشحن</Th><Th>الحالة</Th><Th>رقم التتبع</Th><Th>تكلفة الشحن</Th><Th>تاريخ التسليم المتوقع</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{shipments.map(s => (
                <tr key={s.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-blue-600 dark:text-blue-400">{s.shipment_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{s.customer}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.method}</td>
                  <td className="px-4 py-3"><span className={badge(s.status)}>{SL[s.status]}</span></td>
                  <td className="px-4 py-3 font-mono text-gray-500">{s.tracking_number || '-'}</td>
                  <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{fm(s.shipping_cost)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.estimated_delivery || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {s.status === 'pending' && <button onClick={() => hChangeStatus(s.id, 'processing')} className="text-yellow-600 dark:text-yellow-400 p-1.5 rounded hover:bg-yellow-50 dark:hover:bg-yellow-900/20" title="تحضير"><RefreshCw className="w-4 h-4" /></button>}
                    {s.status === 'processing' && <button onClick={() => hChangeStatus(s.id, 'in_transit')} className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="إرسال"><Navigation className="w-4 h-4" /></button>}
                    {s.status === 'in_transit' && <button onClick={() => hChangeStatus(s.id, 'delivered')} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="تسليم"><CheckCircle className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Methods Tab ─── */}
      {tab === 'methods' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : methods.length === 0 ? <div className="p-12 text-center"><Route className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد طرق شحن</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>الناقل</Th><Th>نوع التكلفة</Th><Th>التكلفة الأساسية</Th><Th>الأيام المتوقعة</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{methods.map(m => (
                <tr key={m.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{m.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{m.carrier}</td>
                  <td className="px-4 py-3"><span className="badge bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 px-2.5 py-1 rounded-full text-xs font-medium">{m.cost_type === 'fixed' ? 'ثابتة' : m.cost_type === 'weight' ? 'حسب الوزن' : 'حسب المسافة'}</span></td>
                  <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{fm(m.base_cost)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{m.estimated_days} يوم</td>
                  <td className="px-4 py-3"><span className={badge(m.is_active ? 'active' : 'inactive')}>{SL[m.is_active ? 'active' : 'inactive']}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    <button onClick={() => hToggleMethod(m.id, m.is_active)} className={`p-1.5 rounded ${m.is_active ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20' : 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'}`} title={m.is_active ? 'تعطيل' : 'تفعيل'}><RefreshCw className="w-4 h-4" /></button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="shipment" title="إنشاء شحنة جديدة"><form onSubmit={hCreateShipment} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">العميل *</label><input type="text" value={shForm.customer} onChange={e => setShForm({ ...shForm, customer: e.target.value })} required placeholder="اسم العميل" className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">طريقة الشحن *</label><select value={shForm.method} onChange={e => setShForm({ ...shForm, method: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option>{methods.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">رقم التتبع</label><input type="text" value={shForm.tracking_number} onChange={e => setShForm({ ...shForm, tracking_number: e.target.value })} placeholder="رقم التتبع" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تكلفة الشحن *</label><input type="number" step="0.01" value={shForm.shipping_cost} onChange={e => setShForm({ ...shForm, shipping_cost: e.target.value })} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التسليم المتوقع</label><input type="date" value={shForm.estimated_delivery} onChange={e => setShForm({ ...shForm, estimated_delivery: e.target.value })} className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="shipment" /></div>
      </form></Modal>

      <Modal k="method" title="إنشاء طريقة شحن جديدة"><form onSubmit={hCreateMethod} className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الطريقة *</label><input type="text" value={mtForm.name} onChange={e => setMtForm({ ...mtForm, name: e.target.value })} required placeholder="مثال: شحن سريع" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الناقل *</label><input type="text" value={mtForm.carrier} onChange={e => setMtForm({ ...mtForm, carrier: e.target.value })} required placeholder="اسم شركة النقل" className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع التكلفة *</label><select value={mtForm.cost_type} onChange={e => setMtForm({ ...mtForm, cost_type: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}><option value="fixed">ثابتة</option><option value="weight">حسب الوزن</option><option value="distance">حسب المسافة</option></select></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التكلفة الأساسية *</label><input type="number" step="0.01" value={mtForm.base_cost} onChange={e => setMtForm({ ...mtForm, base_cost: e.target.value })} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأيام المتوقعة *</label><input type="number" value={mtForm.estimated_days} onChange={e => setMtForm({ ...mtForm, estimated_days: e.target.value })} required min="1" className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="method" /></div>
      </form></Modal>
    </div>
  );
}
