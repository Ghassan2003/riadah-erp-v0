/**
 * Lead Detail Page – comprehensive view of a single CRM lead.
 * Shows header, contact info, activity timeline, notes, status changes,
 * value/probability chart, and conversion to customer.
 * Accessed via /crm/leads/:id
 * Supports dark mode and RTL Arabic.
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { crmAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import {
  ArrowRight, ArrowLeft, User, Mail, Phone, Building2,
  Calendar, DollarSign, Target, Clock, MessageSquare,
  Plus, Send, CheckCircle2, XCircle, AlertCircle,
  FileText, Users as UsersIcon, Video, ClipboardList,
  TrendingUp, X, Loader2, RefreshCw, StickyNote,
  UserCheck, Edit3, Save, ChevronDown,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';

/* ── Pipeline stages ── */
const PIPELINE_STAGES = [
  { key: 'lead',        label: 'عميل محتمل',  color: '#6366f1', bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-700 dark:text-indigo-400' },
  { key: 'qualified',   label: 'مؤهل',        color: '#3b82f6', bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400' },
  { key: 'proposal',    label: 'عرض سعر',     color: '#8b5cf6', bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400' },
  { key: 'negotiation', label: 'تفاوض',       color: '#f59e0b', bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400' },
  { key: 'closed_won',  label: 'رابح',        color: '#10b981', bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-400' },
  { key: 'closed_lost', label: 'خاسر',        color: '#ef4444', bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400' },
];

const ACTIVITY_TYPES = [
  { key: 'call',    label: 'مكالمة',   icon: Phone,          color: 'text-green-500',    bg: 'bg-green-100 dark:bg-green-900/30' },
  { key: 'email',   label: 'بريد',     icon: Mail,           color: 'text-blue-500',     bg: 'bg-blue-100 dark:bg-blue-900/30' },
  { key: 'meeting', label: 'اجتماع',   icon: UsersIcon,      color: 'text-purple-500',   bg: 'bg-purple-100 dark:bg-purple-900/30' },
  { key: 'task',    label: 'مهمة',     icon: ClipboardList,  color: 'text-amber-500',    bg: 'bg-amber-100 dark:bg-amber-900/30' },
  { key: 'note',    label: 'ملاحظة',   icon: StickyNote,     color: 'text-gray-500',     bg: 'bg-gray-100 dark:bg-gray-700' },
];

const Sp = () => (
  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

export default function LeadDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const isDark = document.documentElement.classList.contains('dark');

  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  /* ── State ── */
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activities, setActivities] = useState([]);
  const [actLoading, setActLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [converting, setConverting] = useState(false);
  const [activeTab, setActiveTab] = useState('activities');

  // Activity form
  const [actForm, setActForm] = useState({ type: 'note', subject: '', description: '', scheduled_date: '' });

  // Note form
  const [noteText, setNoteText] = useState('');
  const [noteSaving, setNoteSaving] = useState(false);

  /* ── Input class ── */
  const ic = 'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';

  /* ── Fetch lead data ── */
  const fetchLead = useCallback(async () => {
    setLoading(true);
    try {
      const res = await crmAPI.getLead(id);
      setLead(res.data);
    } catch {
      toast.error('خطأ في تحميل بيانات الفرصة');
      navigate('/crm/pipeline');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  /* ── Fetch activities ── */
  const fetchActivities = useCallback(async () => {
    setActLoading(true);
    try {
      const res = await crmAPI.getLeadActivities(id);
      setActivities(res.data.results || res.data || []);
    } catch {
      // silent
    } finally {
      setActLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchLead(); fetchActivities(); }, [fetchLead, fetchActivities]);

  /* ── Add activity ── */
  const handleAddActivity = async (e) => {
    e.preventDefault();
    if (!actForm.subject && !actForm.description) {
      toast.error('يرجى إدخال الموضوع أو الوصف');
      return;
    }
    setSaving(true);
    try {
      await crmAPI.completeLeadActivity(id, { ...actForm });
      toast.success('تمت إضافة النشاط بنجاح');
      setActForm({ type: 'note', subject: '', description: '', scheduled_date: '' });
      fetchActivities();
    } catch {
      toast.error('خطأ في إضافة النشاط');
    } finally {
      setSaving(false);
    }
  };

  /* ── Add note ── */
  const handleAddNote = async () => {
    if (!noteText.trim()) return;
    setNoteSaving(true);
    try {
      await crmAPI.completeLeadActivity(id, { type: 'note', subject: 'ملاحظة', description: noteText });
      toast.success('تمت إضافة الملاحظة بنجاح');
      setNoteText('');
      fetchActivities();
    } catch {
      toast.error('خطأ في إضافة الملاحظة');
    } finally {
      setNoteSaving(false);
    }
  };

  /* ── Change stage ── */
  const handleChangeStage = async (direction) => {
    if (!lead) return;
    const currentStage = lead.status || lead.stage || 'lead';
    const currentIndex = PIPELINE_STAGES.findIndex(s => s.key === currentStage);
    if (currentIndex < 0) return;

    const newIndex = currentIndex + direction;
    if (newIndex < 0 || newIndex >= PIPELINE_STAGES.length) {
      toast.error('لا يمكن الانتقال إلى هذه المرحلة');
      return;
    }
    const newStage = PIPELINE_STAGES[newIndex].key;

    setSaving(true);
    try {
      await crmAPI.changeLeadStatus(id, { status: newStage });
      toast.success(`تم نقل الفرصة إلى "${PIPELINE_STAGES[newIndex].label}"`);
      setLead(prev => ({ ...prev, status: newStage }));
    } catch {
      toast.error('خطأ في تغيير المرحلة');
    } finally {
      setSaving(false);
    }
  };

  /* ── Convert to customer ── */
  const handleConvert = async () => {
    if (!lead) return;
    setConverting(true);
    try {
      await crmAPI.convertLead(id);
      toast.success('تم تحويل الفرصة إلى عميل بنجاح');
      setLead(prev => ({ ...prev, is_converted: true }));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'خطأ في تحويل الفرصة إلى عميل');
    } finally {
      setConverting(false);
    }
  };

  /* ── Get current stage info ── */
  const currentStageInfo = PIPELINE_STAGES.find(s => s.key === (lead?.status || lead?.stage)) || PIPELINE_STAGES[0];
  const currentStageIndex = PIPELINE_STAGES.findIndex(s => s.key === (lead?.status || lead?.stage));
  const canMovePrev = currentStageIndex > 0;
  const canMoveNext = currentStageIndex < PIPELINE_STAGES.length - 1;

  /* ── Probability chart data ── */
  const probChartData = lead ? [
    { name: 'القيمة', value: Number(lead.value) || 0, fill: '#3b82f6' },
    { name: 'القيمة المتوقعة', value: Math.round((Number(lead.value) || 0) * ((Number(lead.probability) || 0) / 100)), fill: '#10b981' },
  ] : [];

  /* ── Loading state ── */
  if (loading) {
    return (
      <div dir="rtl" className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
        <p className="text-sm text-gray-500 dark:text-gray-400">جاري تحميل بيانات الفرصة...</p>
      </div>
    );
  }

  if (!lead) {
    return (
      <div dir="rtl" className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="w-10 h-10 text-gray-400" />
        <p className="text-sm text-gray-500 dark:text-gray-400">لم يتم العثور على الفرصة</p>
        <button onClick={() => navigate('/crm/pipeline')} className="text-blue-500 hover:text-blue-600 text-sm font-medium">
          العودة إلى خط الأنابيب
        </button>
      </div>
    );
  }

  return (
    <div dir="rtl" className="space-y-5">
      {/* ── Breadcrumb / Back ── */}
      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <button onClick={() => navigate('/crm/pipeline')} className="hover:text-blue-500 transition-colors">
          خط أنابيب المبيعات
        </button>
        <ArrowLeft className="w-4 h-4 rotate-180" />
        <span className="text-gray-900 dark:text-gray-100 font-medium">{lead.title}</span>
      </div>

      {/* ── Lead Header ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{lead.title}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${currentStageInfo.bg} ${currentStageInfo.text}`}>
                {currentStageInfo.label}
              </span>
              {lead.is_converted && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                  تم التحويل
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-1.5">
                <User className="w-4 h-4" />
                <span>{lead.contact_name || '-'}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                <span>{lead.created_at ? lead.created_at.slice(0, 10) : '-'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => handleChangeStage(-1)}
              disabled={!canMovePrev || saving}
              className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium disabled:opacity-50"
            >
              <ArrowRight className="w-4 h-4" />
              المرحلة السابقة
            </button>
            <button
              onClick={() => handleChangeStage(1)}
              disabled={!canMoveNext || saving}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
            >
              المرحلة التالية
              <ArrowLeft className="w-4 h-4" />
            </button>
            {!lead.is_converted && (
              <button
                onClick={handleConvert}
                disabled={converting || (lead.status === 'closed_lost')}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium disabled:opacity-50"
              >
                <UserCheck className="w-4 h-4" />
                {converting ? 'جاري التحويل...' : 'تحويل إلى عميل'}
              </button>
            )}
          </div>
        </div>

        {/* Stage Progress Bar */}
        <div className="mt-5">
          <div className="flex items-center gap-1">
            {PIPELINE_STAGES.map((stage, i) => (
              <div key={stage.key} className="flex-1 flex flex-col items-center gap-1">
                <div className={`h-2 w-full rounded-full transition-all ${
                  i <= currentStageIndex ? stage.bg.replace('/30', '') : 'bg-gray-200 dark:bg-gray-700'
                }`} />
                <span className={`text-[9px] font-medium ${
                  i === currentStageIndex ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'
                }`}>
                  {stage.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">قيمة الفرصة</p>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(lead.value)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">الاحتمالية</p>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{lead.probability != null ? `${lead.probability}%` : '-'}</p>
          <div className="mt-2 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                (lead.probability || 0) < 30 ? 'bg-red-500' : (lead.probability || 0) <= 60 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${lead.probability || 0}%` }}
            />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">القيمة المتوقعة</p>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400" dir="ltr">
            {fmt((Number(lead.value) || 0) * ((Number(lead.probability) || 0) / 100))}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">تاريخ الإغلاق المتوقع</p>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{lead.expected_close_date || '-'}</p>
        </div>
      </div>

      {/* ── Main Content Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: 2 columns */}
        <div className="lg:col-span-2 space-y-5">
          {/* ── Tabs ── */}
          <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
            {[
              { key: 'activities', label: 'سجل النشاطات', icon: MessageSquare },
              { key: 'notes', label: 'الملاحظات', icon: StickyNote },
              { key: 'chart', label: 'التحليل', icon: TrendingUp },
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                    activeTab === tab.key
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* ── Activities Tab ── */}
          {activeTab === 'activities' && (
            <div className="space-y-4">
              {/* Add Activity Form */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <Plus className="w-4 h-4" /> إضافة نشاط
                </h3>
                <form onSubmit={handleAddActivity} className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">النوع</label>
                      <select value={actForm.type} onChange={e => setActForm({ ...actForm, type: e.target.value })}
                        className={`${ic} bg-white dark:bg-gray-700`}>
                        {ACTIVITY_TYPES.map(t => (
                          <option key={t.key} value={t.key}>{t.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">الموعد</label>
                      <input type="datetime-local" value={actForm.scheduled_date}
                        onChange={e => setActForm({ ...actForm, scheduled_date: e.target.value })} className={ic} />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">الموضوع</label>
                    <input type="text" value={actForm.subject}
                      onChange={e => setActForm({ ...actForm, subject: e.target.value })}
                      placeholder="موضوع النشاط" className={ic} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">الوصف</label>
                    <textarea value={actForm.description}
                      onChange={e => setActForm({ ...actForm, description: e.target.value })}
                      placeholder="وصف النشاط..." rows={3}
                      className={`${ic} resize-none`} />
                  </div>
                  <div className="flex justify-end">
                    <button type="submit" disabled={saving}
                      className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50">
                      {saving ? <Sp /> : <Send className="w-4 h-4" />}
                      إضافة
                    </button>
                  </div>
                </form>
              </div>

              {/* Activity Timeline */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">سجل النشاطات</h3>
                </div>
                {actLoading ? (
                  <div className="p-8 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div>
                ) : activities.length === 0 ? (
                  <div className="p-8 text-center">
                    <MessageSquare className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500 dark:text-gray-400">لا توجد نشاطات مسجلة</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-50 dark:divide-gray-700/50 max-h-96 overflow-y-auto">
                    {activities.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).map((act, i) => {
                      const typeInfo = ACTIVITY_TYPES.find(t => t.key === act.type) || ACTIVITY_TYPES[4];
                      const Icon = typeInfo.icon;
                      return (
                        <div key={act.id || i} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                          <div className="flex items-start gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${typeInfo.bg}`}>
                              <Icon className={`w-4 h-4 ${typeInfo.color}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                  {act.subject || typeInfo.label}
                                </span>
                                <div className="flex items-center gap-1.5">
                                  {act.is_completed && (
                                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                                  )}
                                  <span className="text-[10px] text-gray-400 dark:text-gray-500">
                                    {act.created_at ? new Date(act.created_at).toLocaleDateString(nl) : ''}
                                  </span>
                                </div>
                              </div>
                              {act.description && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{act.description}</p>
                              )}
                              {act.scheduled_date && (
                                <div className="flex items-center gap-1 text-[10px] text-blue-500 mt-1">
                                  <Clock className="w-3 h-3" />
                                  <span>{act.scheduled_date}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Notes Tab ── */}
          {activeTab === 'notes' && (
            <div className="space-y-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <StickyNote className="w-4 h-4" /> إضافة ملاحظة
                </h3>
                <div className="space-y-3">
                  <textarea
                    value={noteText}
                    onChange={e => setNoteText(e.target.value)}
                    placeholder="اكتب ملاحظتك هنا..."
                    rows={4}
                    className={`${ic} resize-none`}
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={handleAddNote}
                      disabled={noteSaving || !noteText.trim()}
                      className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      {noteSaving ? <Sp /> : <Send className="w-4 h-4" />}
                      حفظ الملاحظة
                    </button>
                  </div>
                </div>
              </div>

              {/* Notes List (filtered from activities) */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">جميع الملاحظات</h3>
                </div>
                {activities.filter(a => a.type === 'note').length === 0 ? (
                  <div className="p-8 text-center">
                    <StickyNote className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500 dark:text-gray-400">لا توجد ملاحظات</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-50 dark:divide-gray-700/50 max-h-96 overflow-y-auto">
                    {activities
                      .filter(a => a.type === 'note')
                      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                      .map((note, i) => (
                        <div key={note.id || i} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] text-gray-400 dark:text-gray-500">
                              {note.created_at ? new Date(note.created_at).toLocaleDateString(nl, {
                                year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                              }) : ''}
                            </span>
                            {note.created_by_name && (
                              <span className="text-[10px] text-gray-400 dark:text-gray-500 flex items-center gap-1">
                                <User className="w-3 h-3" /> {note.created_by_name}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{note.description}</p>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Chart Tab ── */}
          {activeTab === 'chart' && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">تحليل القيمة والاحتمالية</h3>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={probChartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#1f2937' : '#fff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: isDark ? '#e5e7eb' : '#1f2937',
                      }}
                      formatter={(value) => `${fmt(value)} ر.س`}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]} animationDuration={800}>
                      {probChartData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                  <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">القيمة الإجمالية</p>
                  <p className="text-lg font-bold text-blue-700 dark:text-blue-300" dir="ltr">{fmt(lead.value)} ر.س</p>
                </div>
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-3 text-center">
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mb-1">القيمة المتوقعة</p>
                  <p className="text-lg font-bold text-emerald-700 dark:text-emerald-300" dir="ltr">
                    {fmt((Number(lead.value) || 0) * ((Number(lead.probability) || 0) / 100))} ر.س
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Contact Info */}
        <div className="space-y-5">
          {/* Contact Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            <div className="px-4 py-3 bg-gradient-to-l from-blue-600 to-indigo-600 text-white">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <User className="w-4 h-4" /> معلومات جهة الاتصال
              </h3>
            </div>
            <div className="p-4 space-y-3">
              {[
                { icon: User, label: 'الاسم', value: lead.contact_name },
                { icon: Mail, label: 'البريد', value: lead.contact_email },
                { icon: Phone, label: 'الهاتف', value: lead.contact_phone },
                { icon: Building2, label: 'الشركة', value: lead.company },
                { icon: Target, label: 'المصدر', value: lead.source },
                { icon: Calendar, label: 'تاريخ الإنشاء', value: lead.created_at ? lead.created_at.slice(0, 10) : null },
                { icon: Calendar, label: 'تاريخ الإغلاق', value: lead.expected_close_date },
                { icon: UsersIcon, label: 'المسؤول', value: lead.assigned_to_name },
              ].map((item, i) => {
                const Icon = item.icon;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gray-50 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] text-gray-400 dark:text-gray-500">{item.label}</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100 truncate" dir={item.icon === Mail || item.icon === Phone ? 'ltr' : 'rtl'}>
                        {item.value || '-'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pipeline Stage Quick View */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">مراحل الخط</h3>
            <div className="space-y-2">
              {PIPELINE_STAGES.map((stage, i) => (
                <div
                  key={stage.key}
                  className={`flex items-center gap-2 p-2 rounded-lg transition-all ${
                    stage.key === (lead.status || lead.stage)
                      ? `${stage.bg} border border-current`
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'
                  }`}
                >
                  <div className={`w-3 h-3 rounded-full ${stage.bg}`} style={{ opacity: i <= currentStageIndex ? 1 : 0.3 }} />
                  <span className={`text-xs font-medium ${
                    stage.key === (lead.status || lead.stage)
                      ? stage.text
                      : i <= currentStageIndex ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 dark:text-gray-500'
                  }`}>
                    {stage.label}
                  </span>
                  {stage.key === (lead.status || lead.stage) && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mr-auto" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Description */}
          {lead.description && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" /> الوصف
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{lead.description}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
