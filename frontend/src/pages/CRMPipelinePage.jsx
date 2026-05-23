/**
 * CRM Pipeline Page – Kanban-style sales pipeline board.
 * Shows leads organized by pipeline stages with color-coded probability,
 * detail panel, funnel chart, and filters.
 * Supports dark mode and RTL Arabic.
 */

import { useState, useEffect, useMemo } from 'react';
import { crmAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useNavigate } from 'react-router-dom';
import {
  Search, X, Filter, Download, GripVertical,
  Calendar, User, ChevronLeft, ChevronRight,
  ArrowRight, Target, DollarSign, TrendingUp,
  Users, Phone, Mail, Building2, Clock,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';

/* ── Pipeline stage definitions ── */
const PIPELINE_STAGES = [
  { key: 'lead',        label: 'عميل محتمل',  color: '#6366f1', bg: 'bg-indigo-500',  border: 'border-indigo-400' },
  { key: 'qualified',   label: 'مؤهل',        color: '#3b82f6', bg: 'bg-blue-500',    border: 'border-blue-400' },
  { key: 'proposal',    label: 'عرض سعر',     color: '#8b5cf6', bg: 'bg-purple-500',  border: 'border-purple-400' },
  { key: 'negotiation', label: 'تفاوض',       color: '#f59e0b', bg: 'bg-amber-500',   border: 'border-amber-400' },
  { key: 'closed_won',  label: 'رابح',        color: '#10b981', bg: 'bg-emerald-500', border: 'border-emerald-400' },
  { key: 'closed_lost', label: 'خاسر',        color: '#ef4444', bg: 'bg-red-500',     border: 'border-red-400' },
];

const ACTIVITY_ICONS = {
  call:    { icon: Phone,     color: 'text-green-500',    bg: 'bg-green-100 dark:bg-green-900/30' },
  email:   { icon: Mail,      color: 'text-blue-500',     bg: 'bg-blue-100 dark:bg-blue-900/30' },
  meeting: { icon: Users,     color: 'text-purple-500',   bg: 'bg-purple-100 dark:bg-purple-900/30' },
  task:    { icon: Target,    color: 'text-amber-500',    bg: 'bg-amber-100 dark:bg-amber-900/30' },
  note:    { icon: DollarSign, color: 'text-gray-500',    bg: 'bg-gray-100 dark:bg-gray-700' },
};

const Sp = () => (
  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

export default function CRMPipelinePage() {
  const { locale } = useI18n();
  const navigate = useNavigate();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const isDark = document.documentElement.classList.contains('dark');

  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const fmtI = (v) => Number(v || 0).toLocaleString(nl);

  /* ── State ── */
  const [loading, setLoading] = useState(true);
  const [leads, setLeads] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [filterUser, setFilterUser] = useState('');
  const [filterSource, setFilterSource] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [moveModal, setMoveModal] = useState({ open: false, lead: null });
  const [moveTarget, setMoveTarget] = useState('');
  const [funnelData, setFunnelData] = useState([]);

  /* ── Input class ── */
  const ic = 'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';

  /* ── Fetch leads ── */
  const fetchLeads = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (filterUser) params.assigned_to = filterUser;
      if (filterSource) params.source = filterSource;
      if (filterDateFrom) params.date_from = filterDateFrom;
      if (filterDateTo) params.date_to = filterDateTo;
      const res = await crmAPI.getLeads(params);
      setLeads(res.data.results || res.data || []);
    } catch {
      toast.error('خطأ في تحميل فرص البيع');
    } finally {
      setLoading(false);
    }
  };

  /* ── Fetch funnel data ── */
  const fetchFunnel = async () => {
    try {
      const res = await crmAPI.getPipelineFunnel();
      const data = res.data || [];
      setFunnelData(Array.isArray(data) ? data : []);
    } catch {
      // silent – use fallback
      setFunnelData([]);
    }
  };

  useEffect(() => { fetchLeads(); fetchFunnel(); }, [search, filterUser, filterSource, filterDateFrom, filterDateTo]);

  /* ── Move lead to new stage ── */
  const handleMoveLead = async () => {
    if (!moveModal.lead || !moveTarget) return;
    setSaving(true);
    try {
      await crmAPI.changeLeadStatus(moveModal.lead.id, { status: moveTarget });
      toast.success(`تم نقل الفرصة إلى مرحلة "${PIPELINE_STAGES.find(s => s.key === moveTarget)?.label || moveTarget}"`);
      setMoveModal({ open: false, lead: null });
      setMoveTarget('');
      fetchLeads();
      if (selectedLead?.id === moveModal.lead.id) {
        setSelectedLead(prev => ({ ...prev, status: moveTarget }));
      }
    } catch {
      toast.error('خطأ في نقل الفرصة');
    } finally {
      setSaving(false);
    }
  };

  /* ── Export ── */
  const handleExport = async () => {
    try {
      const r = await crmAPI.export();
      const u = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'crm-pipeline.xlsx';
      document.body.appendChild(a); a.click(); a.remove();
      toast.success('تم التصدير بنجاح');
    } catch {
      toast.error('خطأ في التصدير');
    }
  };

  /* ── Group leads by stage ── */
  const leadsByStage = useMemo(() => {
    const grouped = {};
    PIPELINE_STAGES.forEach(s => { grouped[s.key] = []; });
    leads.forEach(l => {
      const stage = l.status || l.stage || 'lead';
      if (grouped[stage]) grouped[stage].push(l);
      else grouped['lead'].push(l);
    });
    return grouped;
  }, [leads]);

  /* ── Probability color class ── */
  const probColor = (prob) => {
    if (prob == null) return 'border-l-gray-300 dark:border-l-gray-600';
    if (prob < 30) return 'border-l-red-400';
    if (prob <= 60) return 'border-l-yellow-400';
    return 'border-l-green-400';
  };
  const probBadge = (prob) => {
    if (prob == null) return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400';
    if (prob < 30) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    if (prob <= 60) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
  };

  /* ── Chart data for funnel ── */
  const chartFunnel = useMemo(() => {
    if (funnelData.length > 0) {
      return funnelData.map(d => ({
        name: PIPELINE_STAGES.find(s => s.key === d.stage)?.label || d.stage || d.name || '',
        value: d.count || d.value || 0,
      }));
    }
    // Fallback: compute from leads
    return PIPELINE_STAGES.map(s => ({
      name: s.label,
      value: (leadsByStage[s.key] || []).length,
    }));
  }, [funnelData, leadsByStage]);

  const totalPipelineValue = useMemo(() => {
    return leads.reduce((sum, l) => sum + (Number(l.value) || 0), 0);
  }, [leads]);

  return (
    <div dir="rtl" className="space-y-5">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Target className="w-6 h-6 text-indigo-500" />
            خط أنابيب المبيعات
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">
            إدارة وتتبع فرص البيع عبر مراحلها المختلفة
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm text-sm">
            <Download className="w-4 h-4" /> تصدير
          </button>
        </div>
      </div>

      {/* ── Funnel Chart ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">قمع المبيعات</h3>
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            {chartFunnel.some(d => d.value > 0) ? (
              <BarChart data={chartFunnel} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f1f5f9'} horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: isDark ? '#9CA3AF' : '#6B7280' }} axisLine={false} tickLine={false} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '0.75rem',
                    fontSize: '12px',
                    color: isDark ? '#e5e7eb' : '#1f2937',
                  }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} animationDuration={800}>
                  {chartFunnel.map((entry, i) => (
                    <Cell key={i} fill={PIPELINE_STAGES[i % PIPELINE_STAGES.length]?.color || '#6366f1'} />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500 text-sm">
                لا توجد بيانات لعرضها
              </div>
            )}
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            إجمالي قيمة الخط: <span className="font-bold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(totalPipelineValue)}</span> ر.س
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            إجمالي الفرص: <span className="font-bold text-gray-900 dark:text-gray-100">{fmtI(leads.length)}</span>
          </span>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
          <Filter className="w-4 h-4" /> تصفية
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)}
              className="w-full pr-10 pl-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
          </div>
          <input type="text" placeholder="المسؤول (معرف)" value={filterUser} onChange={e => setFilterUser(e.target.value)} className={ic} />
          <input type="text" placeholder="المصدر" value={filterSource} onChange={e => setFilterSource(e.target.value)} className={ic} />
          <input type="date" value={filterDateFrom} onChange={e => setFilterDateFrom(e.target.value)} className={ic} />
          <input type="date" value={filterDateTo} onChange={e => setFilterDateTo(e.target.value)} className={ic} />
        </div>
      </div>

      {/* ── Kanban Board ── */}
      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
          <Sp /> جاري تحميل الخط...
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4" style={{ minHeight: '500px' }}>
          {PIPELINE_STAGES.map((stage) => {
            const stageLeads = leadsByStage[stage.key] || [];
            const stageValue = stageLeads.reduce((s, l) => s + (Number(l.value) || 0), 0);
            return (
              <div key={stage.key} className="flex-shrink-0 w-72 flex flex-col">
                {/* Column Header */}
                <div className={`${stage.bg} bg-opacity-10 dark:bg-opacity-20 rounded-t-xl p-3 border border-gray-100 dark:border-gray-700 border-b-0`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${stage.bg}`} />
                      <span className="font-semibold text-sm text-gray-800 dark:text-gray-200">{stage.label}</span>
                    </div>
                    <span className="text-xs bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full font-medium">
                      {stageLeads.length}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1" dir="ltr">
                    {fmt(stageValue)} ر.س
                  </p>
                </div>

                {/* Cards container */}
                <div className="flex-1 bg-gray-50 dark:bg-gray-900/50 rounded-b-xl p-2 space-y-2 border border-gray-100 dark:border-gray-700 border-t-0 overflow-y-auto" style={{ maxHeight: '520px' }}>
                  {stageLeads.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500">
                      <Target className="w-8 h-8 mb-2 opacity-40" />
                      <p className="text-xs">لا توجد فرص</p>
                    </div>
                  ) : (
                    stageLeads.map(lead => (
                      <div
                        key={lead.id}
                        onClick={() => { setSelectedLead(lead); setSidebarOpen(true); }}
                        className={`bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm border border-gray-100 dark:border-gray-700 border-r-4 ${probColor(lead.probability)} cursor-pointer hover:shadow-md transition-all group`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-tight flex-1 ml-2">
                            {lead.title}
                          </h4>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setMoveModal({ open: true, lead });
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
                            title="نقل إلى مرحلة أخرى"
                          >
                            <ArrowRight className="w-3.5 h-3.5 text-gray-400" />
                          </button>
                        </div>
                        {lead.contact_name && (
                          <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                            <User className="w-3 h-3" />
                            <span className="truncate">{lead.contact_name}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-sm font-bold text-gray-900 dark:text-gray-100" dir="ltr">
                            {fmt(lead.value)}
                          </span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${probBadge(lead.probability)}`}>
                            {lead.probability != null ? `${lead.probability}%` : '-'}
                          </span>
                        </div>
                        {lead.expected_close_date && (
                          <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500 mt-2 pt-2 border-t border-gray-50 dark:border-gray-700/50">
                            <Calendar className="w-3 h-3" />
                            <span>{lead.expected_close_date}</span>
                          </div>
                        )}
                        {lead.assigned_to_name && (
                          <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500 mt-1">
                            <Users className="w-3 h-3" />
                            <span>{lead.assigned_to_name}</span>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Detail Sidebar ── */}
      {sidebarOpen && selectedLead && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="fixed inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
          <div className="relative w-full max-w-md bg-white dark:bg-gray-800 shadow-2xl overflow-y-auto flex flex-col" dir="rtl">
            {/* Sidebar Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">تفاصيل الفرصة</h2>
              <button onClick={() => setSidebarOpen(false)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-4 space-y-4 flex-1">
              {/* Title & Value */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{selectedLead.title}</h3>
                <div className="flex items-center gap-3 mt-2">
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${probBadge(selectedLead.probability)}`}>
                    {PIPELINE_STAGES.find(s => s.key === (selectedLead.status || selectedLead.stage))?.label || selectedLead.status || '-'}
                  </span>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${probBadge(selectedLead.probability)}`}>
                    احتمالية: {selectedLead.probability != null ? `${selectedLead.probability}%` : '-'}
                  </span>
                </div>
              </div>

              {/* Value */}
              <div className="bg-gradient-to-l from-indigo-500 to-blue-600 rounded-xl p-4 text-white">
                <p className="text-xs opacity-80">قيمة الفرصة</p>
                <p className="text-2xl font-bold mt-1" dir="ltr">{fmt(selectedLead.value)}</p>
                <p className="text-xs opacity-70 mt-1">
                  القيمة المتوقعة: {fmt((Number(selectedLead.value) || 0) * ((Number(selectedLead.probability) || 0) / 100))} ر.س
                </p>
              </div>

              {/* Contact Info */}
              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4 space-y-3">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">معلومات جهة الاتصال</h4>
                {selectedLead.contact_name && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <User className="w-4 h-4 text-gray-400" />
                    <span>{selectedLead.contact_name}</span>
                  </div>
                )}
                {selectedLead.contact_email && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <span dir="ltr">{selectedLead.contact_email}</span>
                  </div>
                )}
                {selectedLead.contact_phone && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span dir="ltr">{selectedLead.contact_phone}</span>
                  </div>
                )}
                {selectedLead.company && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Building2 className="w-4 h-4 text-gray-400" />
                    <span>{selectedLead.company}</span>
                  </div>
                )}
              </div>

              {/* Details */}
              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4 space-y-3">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">تفاصيل الفرصة</h4>
                {selectedLead.source && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">المصدر</span>
                    <span className="text-gray-900 dark:text-gray-100 font-medium">{selectedLead.source}</span>
                  </div>
                )}
                {selectedLead.expected_close_date && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">تاريخ الإغلاق المتوقع</span>
                    <span className="text-gray-900 dark:text-gray-100 font-medium">{selectedLead.expected_close_date}</span>
                  </div>
                )}
                {selectedLead.created_at && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">تاريخ الإنشاء</span>
                    <span className="text-gray-900 dark:text-gray-100 font-medium">{selectedLead.created_at}</span>
                  </div>
                )}
              </div>

              {/* Description */}
              {selectedLead.description && (
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4">
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">الوصف</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{selectedLead.description}</p>
                </div>
              )}
            </div>

            {/* Sidebar Footer */}
            <div className="p-4 border-t border-gray-100 dark:border-gray-700 space-y-2">
              <button
                onClick={() => {
                  navigate(`/crm/leads/${selectedLead.id}`);
                  setSidebarOpen(false);
                }}
                className="w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                عرض التفاصيل الكاملة
              </button>
              <button
                onClick={() => {
                  setMoveModal({ open: true, lead: selectedLead });
                }}
                className="w-full py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
              >
                نقل إلى مرحلة أخرى
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Move Lead Modal ── */}
      {moveModal.open && moveModal.lead && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">نقل الفرصة</h3>
              <button onClick={() => setMoveModal({ open: false, lead: null })} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                نقل <span className="font-semibold text-gray-900 dark:text-gray-100">"{moveModal.lead.title}"</span> إلى مرحلة جديدة:
              </p>
              <div className="grid grid-cols-2 gap-2">
                {PIPELINE_STAGES.map(stage => (
                  <button
                    key={stage.key}
                    onClick={() => setMoveTarget(stage.key)}
                    className={`p-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                      moveTarget === stage.key
                        ? `border-current ${stage.bg} text-white`
                        : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    {stage.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="p-4 border-t dark:border-gray-700 flex gap-3">
              <button
                onClick={handleMoveLead}
                disabled={!moveTarget || saving}
                className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {saving ? <span className="flex items-center justify-center gap-2"><Sp /> جاري النقل...</span> : 'نقل'}
              </button>
              <button
                onClick={() => setMoveModal({ open: false, lead: null })}
                className="flex-1 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
