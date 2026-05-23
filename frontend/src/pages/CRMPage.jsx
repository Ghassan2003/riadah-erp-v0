/**
 * CRM Management page - Sales module.
 * Manage contacts, leads, customer segments, and campaigns.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { crmAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Check, Ban, Download,
  Users, Target, Trophy, Megaphone, PieChart,
  Phone, Mail, Building2, ArrowRight,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const SC = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  qualified: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  proposal: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  negotiation: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  won: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  lost: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  running: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};
const SL = {
  active: 'نشط', inactive: 'غير نشط', pending: 'معلّق', qualified: 'مؤهل',
  proposal: 'عرض سعر', negotiation: 'تفاوض', won: 'رابح', lost: 'خاسر',
  draft: 'مسودة', running: 'قيد التنفيذ', completed: 'مكتمل', cancelled: 'ملغى',
};

const TABS = [
  { id: 'contacts', name: 'جهات الاتصال', icon: Users },
  { id: 'leads', name: 'فرص البيع', icon: Target },
  { id: 'segments', name: 'شرائح العملاء', icon: PieChart },
  { id: 'campaigns', name: 'الحملات', icon: Megaphone },
];
const STATS = [
  { key: 'total_contacts', label: 'جهات الاتصال', icon: Users, color: 'from-blue-500 to-blue-600' },
  { key: 'active_leads', label: 'فرص نشطة', icon: Target, color: 'from-emerald-500 to-emerald-600' },
  { key: 'won_deals', label: 'صفقات رابحة', icon: Trophy, color: 'from-amber-500 to-amber-600' },
  { key: 'active_campaigns', label: 'حملات نشطة', icon: Megaphone, color: 'from-purple-500 to-purple-600' },
];
const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);

export default function CRMPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fm = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [tab, setTab] = useState('contacts');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);
  const [stats, setStats] = useState({});
  const [contacts, setContacts] = useState([]);
  const [leads, setLeads] = useState([]);
  const [segments, setSegments] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [search, setSearch] = useState('');
  const [sFilter, setSFilter] = useState('');

  const [modals, setModals] = useState({ contact: false, lead: false, campaign: false });
  const [cForm, setCForm] = useState({ name: '', email: '', phone: '', company: '', source: '' });
  const [lForm, setLForm] = useState({ title: '', contact: '', value: '', probability: '', stage: '' });
  const [campForm, setCampForm] = useState({ name: '', type: '', budget: '', start_date: '', end_date: '' });

  const isAdmin = JSON.parse(localStorage.getItem('user') || '{}')?.role === 'admin';
  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const badge = (s) => `px-2.5 py-1 rounded-full text-xs font-medium ${SC[s] || ''}`;
  const Th = ({ children }) => <th className="px-4 py-3 text-right font-medium">{children}</th>;

  useEffect(() => {
    (async () => { try { setStats((await crmAPI.getStats()).data); } catch {} })();
  }, []);

  useEffect(() => {
    if (tab === 'contacts') {
      (async () => {
        setLd(true); try { setContacts((await crmAPI.getContacts({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل جهات الاتصال'); } finally { setLd(false); }
      })();
    }
    if (tab === 'leads') {
      (async () => {
        setLd(true); try { setLeads((await crmAPI.getLeads({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل فرص البيع'); } finally { setLd(false); }
      })();
    }
    if (tab === 'segments') {
      (async () => {
        setLd(true); try { setSegments((await crmAPI.getSegments({ search })).data.results || []); }
        catch { toast.error('خطأ في تحميل شرائح العملاء'); } finally { setLd(false); }
      })();
    }
    if (tab === 'campaigns') {
      (async () => {
        setLd(true); try { setCampaigns((await crmAPI.getCampaigns({ search, status: sFilter })).data.results || []); }
        catch { toast.error('خطأ في تحميل الحملات'); } finally { setLd(false); }
      })();
    }
  }, [tab, search, sFilter]);

  const hCreateContact = async (e) => {
    e.preventDefault(); setSv(true);
    try {
      await crmAPI.createContact(cForm);
      toast.success('تم إنشاء جهة الاتصال بنجاح');
      setModals({ ...modals, contact: false });
      setCForm({ name: '', email: '', phone: '', company: '', source: '' });
    } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); }
    finally { setSv(false); }
  };

  const hCreateLead = async (e) => {
    e.preventDefault(); setSv(true);
    try {
      await crmAPI.createLead({ ...lForm, value: +lForm.value, probability: +lForm.probability, contact: +lForm.contact });
      toast.success('تم إنشاء فرصة البيع بنجاح');
      setModals({ ...modals, lead: false });
      setLForm({ title: '', contact: '', value: '', probability: '', stage: '' });
    } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); }
    finally { setSv(false); }
  };

  const hCreateCampaign = async (e) => {
    e.preventDefault(); setSv(true);
    try {
      await crmAPI.createCampaign({ ...campForm, budget: +campForm.budget });
      toast.success('تم إنشاء الحملة بنجاح');
      setModals({ ...modals, campaign: false });
      setCampForm({ name: '', type: '', budget: '', start_date: '', end_date: '' });
    } catch (err) { toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ'); }
    finally { setSv(false); }
  };

  const hChangeLeadStatus = async (id, status) => {
    try { await crmAPI.changeLeadStatus(id, { status }); toast.success('تم تغيير حالة الفرصة'); }
    catch { toast.error('خطأ في تغيير الحالة'); }
  };

  const hChangeCampaignStatus = async (id, status) => {
    try { await crmAPI.changeCampaignStatus(id, { status }); toast.success('تم تغيير حالة الحملة'); }
    catch { toast.error('خطأ في تغيير الحالة'); }
  };

  const hExport = async () => {
    try {
      const r = await crmAPI.export();
      const u = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'crm.xlsx';
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

  const leadStatuses = ['pending', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
  const campaignStatuses = ['draft', 'running', 'completed', 'cancelled'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة العملاء</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة جهات الاتصال وفرص البيع وشرائح العملاء والحملات التسويقية</p>
        </div>
        <div className="flex gap-2">
          {tab === 'contacts' && isAdmin && <button onClick={() => setModals({ ...modals, contact: true })} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> جهة اتصال جديدة</button>}
          {tab === 'leads' && isAdmin && <button onClick={() => setModals({ ...modals, lead: true })} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> فرصة بيع جديدة</button>}
          {tab === 'campaigns' && isAdmin && <button onClick={() => setModals({ ...modals, campaign: true })} className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm text-sm"><Plus className="w-4 h-4" /> حملة جديدة</button>}
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
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{key === 'won_deals' ? fm(stats[key]) : (stats[key] || '-')}</p></div>
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
          {tab !== 'segments' && (
            <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
              <option value="">كل الحالات</option>
              {(tab === 'contacts' ? ['active', 'inactive'] : tab === 'leads' ? leadStatuses : campaignStatuses).map(s => <option key={s} value={s}>{SL[s]}</option>)}
            </select>
          )}
        </div>
      </div>

      {/* ─── Contacts Tab ─── */}
      {tab === 'contacts' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : contacts.length === 0 ? <div className="p-12 text-center"><Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد جهات اتصال</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>البريد الإلكتروني</Th><Th>الهاتف</Th><Th>الشركة</Th><Th>المصدر</Th><Th>الحالة</Th>
              </tr></thead>
              <tbody>{contacts.map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.email || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.phone || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.company || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.source || '-'}</td>
                  <td className="px-4 py-3"><span className={badge(c.status)}>{SL[c.status]}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Leads Tab ─── */}
      {tab === 'leads' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : leads.length === 0 ? <div className="p-12 text-center"><Target className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد فرص بيع</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>العنوان</Th><Th>جهة الاتصال</Th><Th>القيمة</Th><Th>الاحتمالية</Th><Th>المرحلة</Th><Th>الحالة</Th><Th>الإجراءات</Th>
              </tr></thead>
              <tbody>{leads.map(l => (
                <tr key={l.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{l.title}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{l.contact_name || '-'}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(l.value)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{l.probability != null ? `${l.probability}%` : '-'}</td>
                  <td className="px-4 py-3"><span className={badge(l.stage)}>{SL[l.stage]}</span></td>
                  <td className="px-4 py-3"><span className={badge(l.status)}>{SL[l.status]}</span></td>
                  <td className="px-4 py-3">{isAdmin && <select
                    value={l.status} onChange={e => hChangeLeadStatus(l.id, e.target.value)}
                    className="text-xs border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md px-2 py-1 outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {leadStatuses.map(s => <option key={s} value={s}>{SL[s]}</option>)}
                  </select>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Segments Tab ─── */}
      {tab === 'segments' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : segments.length === 0 ? <div className="p-12 text-center"><PieChart className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد شرائح عملاء</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>عدد العملاء</Th><Th>الخصم</Th><Th>الحالة</Th>
              </tr></thead>
              <tbody>{segments.map(s => (
                <tr key={s.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{s.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.customer_count || 0}</td>
                  <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400 font-medium">{s.discount != null ? `${s.discount}%` : '-'}</td>
                  <td className="px-4 py-3"><span className={badge(s.is_active ? 'active' : 'inactive')}>{s.is_active ? 'نشط' : 'غير نشط'}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Campaigns Tab ─── */}
      {tab === 'campaigns' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {ld ? <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div> : campaigns.length === 0 ? <div className="p-12 text-center"><Megaphone className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد حملات</p></div> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <Th>الاسم</Th><Th>النوع</Th><Th>الحالة</Th><Th>الميزانية</Th><Th>تاريخ البداية</Th><Th>تاريخ النهاية</Th>
              </tr></thead>
              <tbody>{campaigns.map(c => (
                <tr key={c.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{c.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.type || '-'}</td>
                  <td className="px-4 py-3">
                    <select
                      value={c.status} onChange={e => hChangeCampaignStatus(c.id, e.target.value)}
                      className="text-xs border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md px-2 py-1 outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {campaignStatuses.map(s => <option key={s} value={s}>{SL[s]}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{fm(c.budget)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.start_date || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{c.end_date || '-'}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ─── Create Contact Modal ─── */}
      <Modal k="contact" title="إنشاء جهة اتصال جديدة"><form onSubmit={hCreateContact} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الاسم *</label><input type="text" value={cForm.name} onChange={e => setCForm({ ...cForm, name: e.target.value })} required placeholder="اسم جهة الاتصال" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">البريد الإلكتروني</label><input type="email" value={cForm.email} onChange={e => setCForm({ ...cForm, email: e.target.value })} placeholder="email@example.com" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الهاتف</label><input type="text" value={cForm.phone} onChange={e => setCForm({ ...cForm, phone: e.target.value })} placeholder="+966xxxxxxxxx" className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الشركة</label><input type="text" value={cForm.company} onChange={e => setCForm({ ...cForm, company: e.target.value })} placeholder="اسم الشركة" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المصدر</label><input type="text" value={cForm.source} onChange={e => setCForm({ ...cForm, source: e.target.value })} placeholder="المصدر" className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn>إنشاء</Btn><CancelBtn k="contact" /></div>
      </form></Modal>

      {/* ─── Create Lead Modal ─── */}
      <Modal k="lead" title="إنشاء فرصة بيع جديدة"><form onSubmit={hCreateLead} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">العنوان *</label><input type="text" value={lForm.title} onChange={e => setLForm({ ...lForm, title: e.target.value })} required placeholder="عنوان الفرصة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">جهة الاتصال *</label><input type="text" value={lForm.contact} onChange={e => setLForm({ ...lForm, contact: e.target.value })} required placeholder="معرف جهة الاتصال" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القيمة *</label><input type="number" step="0.01" value={lForm.value} onChange={e => setLForm({ ...lForm, value: e.target.value })} required className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الاحتمالية (%)</label><input type="number" min="0" max="100" value={lForm.probability} onChange={e => setLForm({ ...lForm, probability: e.target.value })} placeholder="50" className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المرحلة</label>
            <select value={lForm.stage} onChange={e => setLForm({ ...lForm, stage: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>
              <option value="">اختر</option>
              {leadStatuses.map(s => <option key={s} value={s}>{SL[s]}</option>)}
            </select>
          </div>
        </div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-emerald-600 hover:bg-emerald-700">إنشاء</Btn><CancelBtn k="lead" /></div>
      </form></Modal>

      {/* ─── Create Campaign Modal ─── */}
      <Modal k="campaign" title="إنشاء حملة جديدة"><form onSubmit={hCreateCampaign} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم الحملة *</label><input type="text" value={campForm.name} onChange={e => setCampForm({ ...campForm, name: e.target.value })} required placeholder="اسم الحملة" className={ic} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع *</label><input type="text" value={campForm.type} onChange={e => setCampForm({ ...campForm, type: e.target.value })} required placeholder="بريد إلكتروني، وسائط..." className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الميزانية *</label><input type="number" step="0.01" value={campForm.budget} onChange={e => setCampForm({ ...campForm, budget: e.target.value })} required className={ic} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ البداية</label><input type="date" value={campForm.start_date} onChange={e => setCampForm({ ...campForm, start_date: e.target.value })} className={ic} /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">تاريخ النهاية</label><input type="date" value={campForm.end_date} onChange={e => setCampForm({ ...campForm, end_date: e.target.value })} className={ic} /></div>
        </div>
        <div className="flex gap-3 pt-2"><Btn cls="bg-purple-600 hover:bg-purple-700">إنشاء</Btn><CancelBtn k="campaign" /></div>
      </form></Modal>
    </div>
  );
}
