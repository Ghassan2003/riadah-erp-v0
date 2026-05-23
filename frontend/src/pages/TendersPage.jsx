/**
 * Tenders Management page - ERP module.
 * Manage tenders, bids, and awards.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { tendersAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Globe, Award,
  FileSearch, FilePlus, Clock, AlertCircle, Send, Star,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  published: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  closed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  awarded: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  submitted: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  under_review: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  qualified: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  disqualified: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  expired: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  open: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};
const SL = {
  draft: 'مسودة', published: 'منشورة', closed: 'مقفلة', cancelled: 'ملغاة',
  awarded: 'مرساة', pending: 'معلّق', submitted: 'مقدّم', under_review: 'قيد المراجعة',
  qualified: 'مؤهل', disqualified: 'غير مؤهل', active: 'نشط', expired: 'منتهي',
  approved: 'معتمد', rejected: 'مرفوض', open: 'مفتوحة',
};

const TABS = [
  { id: 'tenders', name: 'المناقصات', icon: FileSearch },
  { id: 'bids', name: 'العطاءات', icon: FilePlus },
  { id: 'awards', name: 'الترسيات', icon: Award },
];
const STATS = [
  { key: 'total_tenders', label: 'المناقصات', icon: FileSearch, color: 'from-blue-500 to-blue-600' },
  { key: 'published_tenders', label: 'المنشورة', icon: Globe, color: 'from-emerald-500 to-emerald-600' },
  { key: 'total_bids', label: 'العطاءات', icon: FilePlus, color: 'from-amber-500 to-amber-600' },
  { key: 'awarded_count', label: 'المرساة', icon: Award, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function TendersPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('tenders');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [tenders, setTenders] = useState([]);
  const [bids, setBids] = useState([]);
  const [awards, setAwards] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ tender: false });
  const [tForm, setTForm] = useState({ title: '', type: 'open', estimated_value: '', closing_date: '', description: '' });

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => { (async () => { try { setStats((await tendersAPI.getStats()).data); } catch {} })(); }, []);

  useEffect(() => {
    (async () => {
      setLd(true);
      try {
        if (tab === 'tenders') setTenders((await tendersAPI.getTenders({ search, status: sFilter })).data.results || []);
        else if (tab === 'bids') setBids((await tendersAPI.getBids({ search, status: sFilter })).data.results || []);
        else if (tab === 'awards') setAwards((await tendersAPI.getAwards({ search, status: sFilter })).data.results || []);
      } catch { toast.error('خطأ في تحميل البيانات'); } finally { setLd(false); }
    })();
  }, [tab, search, sFilter]);

  const hCreateTender = async (e) => {
    e.preventDefault(); setSv(true);
    try { await tendersAPI.createTender({ ...tForm, estimated_value: +tForm.estimated_value }); toast.success('تم إنشاء المناقصة بنجاح'); setModals({ ...modals, tender: false }); setTForm({ title: '', type: 'open', estimated_value: '', closing_date: '', description: '' }); }
    catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); } finally { setSv(false); }
  };
  const hPublish = async (id) => {
    try { await tendersAPI.publishTender(id); toast.success('تم نشر المناقصة بنجاح'); setTenders((await tendersAPI.getTenders({ search, status: sFilter })).data.results || []); }
    catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };
  const hDisqualify = async (id) => {
    try { await tendersAPI.disqualifyBid(id); toast.success('تم استبعاد العطاء'); setBids((await tendersAPI.getBids({ search, status: sFilter })).data.results || []); }
    catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };
  const hApproveAward = async (id) => {
    try { await tendersAPI.approveAward(id); toast.success('تم اعتماد الترسية بنجاح'); setAwards((await tendersAPI.getAwards({ search, status: sFilter })).data.results || []); }
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

  const statusOptions = tab === 'tenders' ? ['draft', 'published', 'closed', 'cancelled', 'awarded']
    : tab === 'bids' ? ['submitted', 'under_review', 'qualified', 'disqualified']
    : ['pending', 'approved', 'rejected'];

  const typeLabels = { open: 'مفتوحة', restricted: 'مقيّدة', direct: 'مباشرة' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة المناقصات</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة المناقصات، العطاءات، والترسيات</p>
        </div>
        <div className="flex gap-2">
          {tab === 'tenders' && <button onClick={() => setModals({ ...modals, tender: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> مناقصة جديدة</button>}
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

      {/* ─── Tenders Tab ─── */}
      {tab === 'tenders' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : tenders.length === 0 ? <div className="p-12 text-center"><FileSearch className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد مناقصات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الرقم</Th><Th>العنوان</Th><Th>النوع</Th><Th>الحالة</Th><Th>القيمة المقدرة</Th><Th>تاريخ الإغلاق</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{tenders.map(t => (
                <tr key={t.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-medium text-gray-900 dark:text-gray-100">{t.tender_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{t.title}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{typeLabels[t.type] || t.type}</td>
                  <td className="px-4 py-3"><span className={badge(t.status)}>{SL[t.status]}</span></td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(t.estimated_value)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{t.closing_date || '-'}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {t.status === 'draft' && <button onClick={() => hPublish(t.id)} className="text-emerald-600 dark:text-emerald-400 p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20" title="نشر"><Send className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Bids Tab ─── */}
      {tab === 'bids' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : bids.length === 0 ? <div className="p-12 text-center"><FilePlus className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد عطاءات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الرقم</Th><Th>المناقصة</Th><Th>المورّد</Th><Th>المبلغ الإجمالي</Th><Th>الدرجة الفنية</Th><Th>الدرجة المالية</Th><Th>المجموع</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{bids.map(b => (
                <tr key={b.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-medium text-gray-900 dark:text-gray-100">{b.bid_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{b.tender_title || b.tender}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.supplier_name || b.supplier}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(b.total_amount)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.technical_score ?? '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{b.financial_score ?? '-'}</td>
                  <td className="px-4 py-3 font-bold text-gray-900 dark:text-gray-100">{b.total_score ?? '-'}</td>
                  <td className="px-4 py-3"><span className={badge(b.status)}>{SL[b.status]}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {b.status !== 'disqualified' && <button onClick={() => hDisqualify(b.id)} className="text-red-600 dark:text-red-400 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="استبعاد"><Ban className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Awards Tab ─── */}
      {tab === 'awards' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : awards.length === 0 ? <div className="p-12 text-center"><Award className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد ترسيات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>المناقصة</Th><Th>المورّد</Th><Th>قيمة العقد</Th><Th>المدة</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{awards.map(a => (
                <tr key={a.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{a.tender_title || a.tender}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{a.supplier_name || a.supplier}</td>
                  <td className="px-4 py-3 font-bold text-blue-600 dark:text-blue-400">{fm(a.contract_value)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{a.duration || '-'}</td>
                  <td className="px-4 py-3"><span className={badge(a.status)}>{SL[a.status]}</span></td>
                  <td className="px-4 py-3"><div className="flex gap-1">
                    <button className="text-blue-600 dark:text-blue-400 p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20" title="عرض"><Eye className="w-4 h-4" /></button>
                    {a.status === 'pending' && <button onClick={() => hApproveAward(a.id)} className="text-green-600 dark:text-green-400 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="اعتماد"><Check className="w-4 h-4" /></button>}
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Modals ─── */}
      <Modal k="tender" title="إنشاء مناقصة جديدة"><form onSubmit={hCreateTender} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">العنوان *</label><input type="text" value={tForm.title} onChange={e => setTForm({ ...tForm, title: e.target.value })} required placeholder="عنوان المناقصة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع</label><select value={tForm.type} onChange={e => setTForm({ ...tForm, type: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="open">مفتوحة</option><option value="restricted">مقيّدة</option><option value="direct">مباشرة</option>
          </select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القيمة المقدرة *</label><input type="number" step="0.01" value={tForm.estimated_value} onChange={e => setTForm({ ...tForm, estimated_value: e.target.value })} required className={ic} /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ الإغلاق *</label><input type="date" value={tForm.closing_date} onChange={e => setTForm({ ...tForm, closing_date: e.target.value })} required className={ic} /></div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الوصف</label><textarea value={tForm.description} onChange={e => setTForm({ ...tForm, description: e.target.value })} rows={3} className={`${ic} resize-none`} placeholder="وصف المناقصة..." /></div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="tender" /></div>
      </form></Modal>
    </div>
  );
}
