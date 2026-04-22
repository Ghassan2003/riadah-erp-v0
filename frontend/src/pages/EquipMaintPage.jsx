import { useState, useEffect } from 'react';
import { equipmaintAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Wrench, CalendarClock, ClipboardList, Search, Plus, X,
  Eye, Download, Check, Play, AlertTriangle
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  out_of_service: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  excellent: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  good: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  fair: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  poor: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  overdue: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};
const SL = {
  pending: 'معلّق', approved: 'معتمد', in_progress: 'قيد التنفيذ',
  completed: 'مكتمل', cancelled: 'ملغي',
  active: 'نشط', inactive: 'غير نشط', out_of_service: 'خارج الخدمة',
  excellent: 'ممتاز', good: 'جيد', fair: 'مقبول', poor: 'سيء',
  scheduled: 'مجدول', overdue: 'متأخر',
  high: 'عالية', medium: 'متوسطة', low: 'منخفضة',
};

const TABS = [
  { id: 'equipment', name: 'المعدات', icon: Wrench },
  { id: 'schedules', name: 'جداول الصيانة', icon: CalendarClock },
  { id: 'work_orders', name: 'أوامر العمل', icon: ClipboardList },
  { id: 'inspections', name: 'الفحوصات', icon: Search },
];
const STATS = [
  { key: 'total_equipment', label: 'المعدات', icon: Wrench, color: 'from-blue-500 to-blue-600' },
  { key: 'active_schedules', label: 'جداول نشطة', icon: CalendarClock, color: 'from-emerald-500 to-emerald-600' },
  { key: 'open_orders', label: 'أوامر مفتوحة', icon: ClipboardList, color: 'from-amber-500 to-amber-600' },
  { key: 'pending_inspections', label: 'فحوصات معلّقة', icon: Search, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function EquipMaintPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('equipment');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [equipment, setEquipment] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [inspections, setInspections] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ equipment: false, schedule: false, workOrder: false, inspection: false });
  const [eqForm, setEqForm] = useState({ name: '', number: '', category: '', location: '', status: 'active' });
  const [schForm, setSchForm] = useState({ equipment: '', type: '', frequency: '', next_due: '', priority: 'medium' });
  const [woForm, setWoForm] = useState({ equipment: '', type: '', priority: 'medium', assigned_to: '' });
  const [inspForm, setInspForm] = useState({ equipment: '', type: '', inspector: '', condition_rating: 'good' });

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await equipmaintAPI.getStats()).data); } catch {} })(); }, []);
  useEffect(() => { (async () => { setLd(true); try { setEquipment((await equipmaintAPI.getEquipment({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل المعدات'); } finally { setLd(false); } })(); }, [search, sFilter]);
  useEffect(() => { (async () => { if (tab === 'schedules') { setLd(true); try { setSchedules((await equipmaintAPI.getSchedules({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل الجداول'); } finally { setLd(false); } } })(); }, [tab, search, sFilter]);
  useEffect(() => { (async () => { if (tab === 'work_orders') { setLd(true); try { setWorkOrders((await equipmaintAPI.getWorkOrders({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل أوامر العمل'); } finally { setLd(false); } } })(); }, [tab, search, sFilter]);
  useEffect(() => { (async () => { if (tab === 'inspections') { setLd(true); try { setInspections((await equipmaintAPI.getInspections({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ في تحميل الفحوصات'); } finally { setLd(false); } } })(); }, [tab, search, sFilter]);

  const hCreateEquipment = async (e) => { e.preventDefault(); setSv(true); try { await equipmaintAPI.createEquipment(eqForm); toast.success('تم إضافة المعدة بنجاح'); setModals({ ...modals, equipment: false }); setEqForm({ name: '', number: '', category: '', location: '', status: 'active' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateSchedule = async (e) => { e.preventDefault(); setSv(true); try { await equipmaintAPI.createSchedule(schForm); toast.success('تم إنشاء جدول الصيانة بنجاح'); setModals({ ...modals, schedule: false }); setSchForm({ equipment: '', type: '', frequency: '', next_due: '', priority: 'medium' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateWorkOrder = async (e) => { e.preventDefault(); setSv(true); try { await equipmaintAPI.createWorkOrder(woForm); toast.success('تم إنشاء أمر العمل بنجاح'); setModals({ ...modals, workOrder: false }); setWoForm({ equipment: '', type: '', priority: 'medium', assigned_to: '' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };
  const hCreateInspection = async (e) => { e.preventDefault(); setSv(true); try { await equipmaintAPI.createInspection(inspForm); toast.success('تم إنشاء الفحص بنجاح'); setModals({ ...modals, inspection: false }); setInspForm({ equipment: '', type: '', inspector: '', condition_rating: 'good' }); } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); } };

  const hApproveOrder = async (id) => { try { await equipmaintAPI.approveWorkOrder(id); toast.success('تم اعتماد أمر العمل'); setWorkOrders((await equipmaintAPI.getWorkOrders({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ'); } };
  const hStartOrder = async (id) => { try { await equipmaintAPI.startWorkOrder(id); toast.success('تم بدء أمر العمل'); setWorkOrders((await equipmaintAPI.getWorkOrders({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ'); } };
  const hCompleteOrder = async (id) => { try { await equipmaintAPI.completeWorkOrder(id); toast.success('تم إكمال أمر العمل'); setWorkOrders((await equipmaintAPI.getWorkOrders({ search, status: sFilter })).data.results || []); } catch { toast.error('خطأ'); } };
  const hExport = async () => { try { const r = await equipmaintAPI.export(); const u = window.URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = u; a.download = 'equipment-maintenance.xlsx'; document.body.appendChild(a); a.click(); a.remove(); toast.success('تم التصدير'); } catch { toast.error('خطأ في التصدير'); } };

  const statusOpts = {
    equipment: ['active', 'inactive', 'out_of_service'],
    schedules: ['scheduled', 'overdue', 'completed', 'cancelled'],
    work_orders: ['pending', 'approved', 'in_progress', 'completed', 'cancelled'],
    inspections: ['pending', 'in_progress', 'completed'],
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">صيانة المعدات</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة المعدات وجداول الصيانة وأوامر العمل والفحوصات</p>
        </div>
        <div className="flex gap-2">
          <button onClick={hExport} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm text-sm"><Download className="w-4 h-4" /> تصدير</button>
          <button onClick={() => setModals({ ...modals, [tab === 'equipment' ? 'equipment' : tab === 'schedules' ? 'schedule' : tab === 'work_orders' ? 'workOrder' : 'inspection']: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> إضافة جديد</button>
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
        {TABS.map(t => { const I = t.icon; return <button key={t.id} onClick={() => { setTab(t.id); setSFilter(''); }} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}><I className="w-4 h-4" /> {t.name}</button>; })}
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
            {(statusOpts[tab] || []).map(s => <option key={s} value={s}>{SL[s]}</option>)}
          </select>
        </div>
      </div>

      {/* ─── Equipment Tab ─── */}
      {tab === 'equipment' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : equipment.length === 0 ? <div className="p-12 text-center"><Wrench className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد معدات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>الرقم</Th><Th>التصنيف</Th><Th>الموقع</Th><Th>الحالة</Th><Th>الحالة الفنية</Th>
              </tr></thead>
              <tbody>{equipment.map(eq => (
                <tr key={eq.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{eq.name}</td>
                  <td className="px-4 py-3 font-mono text-blue-600 dark:text-blue-400">{eq.number}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{eq.category}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{eq.location}</td>
                  <td className="px-4 py-3"><span className={badge(eq.status)}>{SL[eq.status]}</span></td>
                  <td className="px-4 py-3"><span className={badge(eq.condition || 'good')}>{SL[eq.condition || 'good']}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Schedules Tab ─── */}
      {tab === 'schedules' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : schedules.length === 0 ? <div className="p-12 text-center"><CalendarClock className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد جداول صيانة</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>المعدة</Th><Th>نوع الصيانة</Th><Th>التكرار</Th><Th>التاريخ القادم</Th><Th>الأولوية</Th><Th>الحالة</Th>
              </tr></thead>
              <tbody>{schedules.map(s => (
                <tr key={s.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{s.equipment}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.type}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.frequency}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.next_due}</td>
                  <td className="px-4 py-3"><span className={badge(s.priority)}>{SL[s.priority]}</span></td>
                  <td className="px-4 py-3"><span className={badge(s.status)}>{SL[s.status]}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Work Orders Tab ─── */}
      {tab === 'work_orders' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : workOrders.length === 0 ? <div className="p-12 text-center"><ClipboardList className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد أوامر عمل</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>رقم الأمر</Th><Th>المعدة</Th><Th>النوع</Th><Th>الأولوية</Th><Th>الحالة</Th><Th>المسند إليه</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{workOrders.map(wo => (
                <tr key={wo.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-blue-600 dark:text-blue-400">{wo.order_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{wo.equipment}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{wo.type}</td>
                  <td className="px-4 py-3"><span className={badge(wo.priority)}>{SL[wo.priority]}</span></td>
                  <td className="px-4 py-3"><span className={badge(wo.status)}>{SL[wo.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{wo.assigned_to || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {wo.status === 'pending' && <button onClick={() => hApproveOrder(wo.id)} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="اعتماد"><Check className="w-4 h-4" /></button>}
                    {wo.status === 'approved' && <button onClick={() => hStartOrder(wo.id)} className="text-yellow-600 dark:text-yellow-400 p-1.5 rounded hover:bg-yellow-50 dark:hover:bg-yellow-900/20" title="بدء"><Play className="w-4 h-4" /></button>}
                    {wo.status === 'in_progress' && <button onClick={() => hCompleteOrder(wo.id)} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="إكمال"><Check className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Inspections Tab ─── */}
      {tab === 'inspections' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : inspections.length === 0 ? <div className="p-12 text-center"><Search className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد فحوصات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>المعدة</Th><Th>نوع الفحص</Th><Th>المفتش</Th><Th>التقييم</Th><Th>الحالة</Th><Th>التاريخ</Th>
              </tr></thead>
              <tbody>{inspections.map(insp => (
                <tr key={insp.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{insp.equipment}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{insp.type}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{insp.inspector}</td>
                  <td className="px-4 py-3"><span className={badge(insp.condition_rating || 'good')}>{SL[insp.condition_rating || 'good']}</span></td>
                  <td className="px-4 py-3"><span className={badge(insp.status)}>{SL[insp.status]}</span></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{insp.date}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="equipment" title="إضافة معدة جديدة"><form onSubmit={hCreateEquipment} className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم المعدة *</label><input type="text" value={eqForm.name} onChange={e => setEqForm({ ...eqForm, name: e.target.value })} required placeholder="اسم المعدة" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الرقم *</label><input type="text" value={eqForm.number} onChange={e => setEqForm({ ...eqForm, number: e.target.value })} required placeholder="EQ-001" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التصنيف *</label><input type="text" value={eqForm.category} onChange={e => setEqForm({ ...eqForm, category: e.target.value })} required placeholder="التصنيف" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الموقع *</label><input type="text" value={eqForm.location} onChange={e => setEqForm({ ...eqForm, location: e.target.value })} required placeholder="الموقع" className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحالة</label><select value={eqForm.status} onChange={e => setEqForm({ ...eqForm, status: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}><option value="active">نشط</option><option value="inactive">غير نشط</option><option value="out_of_service">خارج الخدمة</option></select></div>
        <div className="flex gap-3 pt-2"><Btn>إضافة</Btn><CancelBtn k="equipment" /></div>
      </form></Modal>

      <Modal k="schedule" title="إنشاء جدول صيانة"><form onSubmit={hCreateSchedule} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المعدة *</label><input type="text" value={schForm.equipment} onChange={e => setSchForm({ ...schForm, equipment: e.target.value })} required placeholder="اسم المعدة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع الصيانة *</label><select value={schForm.type} onChange={e => setSchForm({ ...schForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="preventive">وقائية</option><option value="corrective">تصحيحية</option><option value="predictive">تنبؤية</option></select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التكرار *</label><select value={schForm.frequency} onChange={e => setSchForm({ ...schForm, frequency: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="daily">يومي</option><option value="weekly">أسبوعي</option><option value="monthly">شهري</option><option value="quarterly">ربع سنوي</option><option value="yearly">سنوي</option></select></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التاريخ القادم *</label><input type="date" value={schForm.next_due} onChange={e => setSchForm({ ...schForm, next_due: e.target.value })} required className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأولوية</label><select value={schForm.priority} onChange={e => setSchForm({ ...schForm, priority: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}><option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option></select></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="schedule" /></div>
      </form></Modal>

      <Modal k="workOrder" title="إنشاء أمر عمل"><form onSubmit={hCreateWorkOrder} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المعدة *</label><input type="text" value={woForm.equipment} onChange={e => setWoForm({ ...woForm, equipment: e.target.value })} required placeholder="اسم المعدة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع *</label><select value={woForm.type} onChange={e => setWoForm({ ...woForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="repair">إصلاح</option><option value="maintenance">صيانة</option><option value="replacement">استبدال</option><option value="overhaul">إعادة تأهيل</option></select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأولوية</label><select value={woForm.priority} onChange={e => setWoForm({ ...woForm, priority: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}><option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option></select></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المسند إليه</label><input type="text" value={woForm.assigned_to} onChange={e => setWoForm({ ...woForm, assigned_to: e.target.value })} placeholder="اسم الفني" className={ic} /></div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="workOrder" /></div>
      </form></Modal>

      <Modal k="inspection" title="إنشاء فحص جديد"><form onSubmit={hCreateInspection} className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المعدة *</label><input type="text" value={inspForm.equipment} onChange={e => setInspForm({ ...inspForm, equipment: e.target.value })} required placeholder="اسم المعدة" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع الفحص *</label><select value={inspForm.type} onChange={e => setInspForm({ ...inspForm, type: e.target.value })} required className={`${ic} bg-white dark:bg-gray-700`}><option value="">اختر</option><option value="routine">دوري</option><option value="special">خاص</option><option value="emergency">طارئ</option></select></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المفتش *</label><input type="text" value={inspForm.inspector} onChange={e => setInspForm({ ...inspForm, inspector: e.target.value })} required placeholder="اسم المفتش" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التقييم</label><select value={inspForm.condition_rating} onChange={e => setInspForm({ ...inspForm, condition_rating: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}><option value="excellent">ممتاز</option><option value="good">جيد</option><option value="fair">مقبول</option><option value="poor">سيء</option></select></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="inspection" /></div>
      </form></Modal>
    </div>
  );
}
