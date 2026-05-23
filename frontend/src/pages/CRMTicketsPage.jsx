/**
 * CRM Tickets Page - تذاكر الدعم الفني
 * Features: tickets table, create modal, detail with comments, stats.
 */

import { useState, useEffect, useCallback } from 'react';
import { crmAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Headphones, Plus, X, Edit3, Trash2, Search, Filter, Loader2, Save,
  AlertTriangle, MessageSquare, Send, Clock, CheckCircle, UserPlus,
  ChevronLeft, Eye,
} from 'lucide-react';

const STATUS_CFG = {
  new: { label: 'جديد', cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  in_progress: { label: 'قيد التنفيذ', cls: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  pending: { label: 'معلّق', cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  resolved: { label: 'تم الحل', cls: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  closed: { label: 'مغلق', cls: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
};

const PRIORITY_CFG = {
  low: { label: 'منخفض', cls: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300' },
  medium: { label: 'متوسط', cls: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  high: { label: 'مرتفع', cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  urgent: { label: 'عاجل', cls: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
};

const CAT_LABELS = {
  technical: 'تقني', billing: 'فواتير', general: 'عام',
  feature_request: 'طلب ميزة', bug: 'خلل', complaint: 'شكوى', other: 'أخرى',
};

const emptyTicket = {
  subject: '', description: '', priority: 'medium', category: 'general',
  contact: '', assigned_to: '',
};

export default function CRMTicketsPage() {
  const [tickets, setTickets] = useState([]);
  const [ticketStats, setTicketStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyTicket);

  const [selectedTicket, setSelectedTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [showDetail, setShowDetail] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);

  const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm';

  const fetchStats = useCallback(async () => {
    try { setTicketStats((await crmAPI.ticketStats()).data); } catch {}
  }, []);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = { search: search || undefined, status: statusFilter || undefined, priority: priorityFilter || undefined, category: categoryFilter || undefined };
      const r = await crmAPI.tickets(params);
      setTickets(r.data.results || r.data || []);
    } catch {
      toast.error('خطأ في تحميل التذاكر');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, priorityFilter, categoryFilter]);

  useEffect(() => { fetchStats(); fetchTickets(); }, [fetchStats, fetchTickets]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.subject.trim()) { toast.error('أدخل الموضوع'); return; }
    setSaving(true);
    try {
      await crmAPI.createTicket(form);
      toast.success('تم إنشاء التذكرة');
      setShowModal(false);
      setForm(emptyTicket);
      fetchTickets();
      fetchStats();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await crmAPI.deleteTicket(deleteTarget.id);
      toast.success('تم حذف التذكرة');
      setDeleteTarget(null);
      fetchTickets();
    } catch {
      toast.error('خطأ في الحذف');
    }
  };

  const viewTicket = async (ticket) => {
    setSelectedTicket(ticket);
    setShowDetail(true);
    setCommentsLoading(true);
    try {
      const r = await crmAPI.ticketComments(ticket.id);
      setComments(r.data.results || r.data || []);
    } catch { setComments([]); }
    finally { setCommentsLoading(false); }
  };

  const addComment = async () => {
    if (!newComment.trim() || !selectedTicket) return;
    try {
      await crmAPI.createTicketComment(selectedTicket.id, { content: newComment });
      setNewComment('');
      const r = await crmAPI.ticketComments(selectedTicket.id);
      setComments(r.data.results || r.data || []);
      toast.success('تم إضافة التعليق');
    } catch {
      toast.error('خطأ في إضافة التعليق');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <Headphones className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">تذاكر الدعم الفني</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">إدارة ومتابعة طلبات الدعم</p>
          </div>
        </div>
        <button onClick={() => { setForm(emptyTicket); setShowModal(true); }} className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm shadow-sm">
          <Plus className="w-4 h-4" /> تذكرة جديدة
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'جديد', key: 'new_count', icon: Headphones, color: 'blue' },
          { label: 'قيد التنفيذ', key: 'in_progress_count', icon: Clock, color: 'yellow' },
          { label: 'تم الحل', key: 'resolved_count', icon: CheckCircle, color: 'green' },
          { label: 'متوسط وقت الحل', key: 'avg_resolution_time', icon: Clock, color: 'purple' },
        ].map(({ label, key, icon: I, color }) => (
          <div key={key} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-${color}-100 dark:bg-${color}-900/30`}><I className={`w-5 h-5 text-${color}-600 dark:text-${color}-400`} /></div>
              <div><p className="text-xs text-gray-500 dark:text-gray-400">{label}</p><p className="text-lg font-bold text-gray-900 dark:text-gray-100">{ticketStats[key] || '-'}</p></div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" placeholder="بحث..." value={search} onChange={e => setSearch(e.target.value)} className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none text-sm" />
          </div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الحالات</option>
            {Object.entries(STATUS_CFG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الأولويات</option>
            {Object.entries(PRIORITY_CFG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className={`${ic} bg-white dark:bg-gray-700`}>
            <option value="">كل الفئات</option>
            {Object.entries(CAT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Loader2 className="animate-spin" /> جاري التحميل...</div>
        ) : tickets.length === 0 ? (
          <div className="p-12 text-center"><Headphones className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500">لا توجد تذاكر</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-right font-medium">الرقم</th>
                  <th className="px-4 py-3 text-right font-medium">الموضوع</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                  <th className="px-4 py-3 text-right font-medium">الأولوية</th>
                  <th className="px-4 py-3 text-right font-medium">الفئة</th>
                  <th className="px-4 py-3 text-right font-medium">المسؤول</th>
                  <th className="px-4 py-3 text-right font-medium">التاريخ</th>
                  <th className="px-4 py-3 text-right font-medium">إجراء</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-purple-600 dark:text-purple-400 text-xs" dir="ltr">#{t.ticket_number || t.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{t.subject}</td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CFG[t.status]?.cls || ''}`}>{STATUS_CFG[t.status]?.label || t.status}</span></td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs ${PRIORITY_CFG[t.priority]?.cls || ''}`}>{PRIORITY_CFG[t.priority]?.label || t.priority}</span></td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{CAT_LABELS[t.category] || t.category || '-'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{t.assigned_to_name || t.assigned_to || '-'}</td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{t.created_at?.split('T')[0] || '-'}</td>
                    <td className="px-4 py-3 flex gap-1">
                      <button onClick={() => viewTicket(t)} className="p-1.5 text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg"><Eye className="w-4 h-4" /></button>
                      <button onClick={() => setDeleteTarget(t)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
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
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">تذكرة جديدة</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الموضوع *</label><input type="text" value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })} required className={ic} placeholder="موضوع التذكرة" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الوصف</label><textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} className={ic} placeholder="تفاصيل المشكلة..." /></div>
              <div className="grid grid-cols-3 gap-4">
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الأولوية</label><select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>{Object.entries(PRIORITY_CFG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></div>
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الفئة</label><select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>{Object.entries(CAT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">جهة الاتصال</label><input type="text" value={form.contact} onChange={e => setForm({ ...form, contact: e.target.value })} className={ic} /></div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{saving ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحفظ...</> : <><Save className="w-4 h-4" /> إنشاء</>}</button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ticket Detail Modal */}
      {showDetail && selectedTicket && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">#{selectedTicket.ticket_number || selectedTicket.id} — {selectedTicket.subject}</h3>
                <div className="flex gap-2 mt-1">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_CFG[selectedTicket.status]?.cls || ''}`}>{STATUS_CFG[selectedTicket.status]?.label || selectedTicket.status}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs ${PRIORITY_CFG[selectedTicket.priority]?.cls || ''}`}>{PRIORITY_CFG[selectedTicket.priority]?.label || selectedTicket.priority}</span>
                </div>
              </div>
              <button onClick={() => { setShowDetail(false); setSelectedTicket(null); }} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5">
              {selectedTicket.description && <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 bg-gray-50 dark:bg-gray-700/30 p-3 rounded-lg">{selectedTicket.description}</p>}
              <div className="flex items-center gap-2 mb-3"><MessageSquare className="w-4 h-4 text-gray-500" /><h4 className="font-semibold text-gray-800 dark:text-gray-200 text-sm">التعليقات ({comments.length})</h4></div>
              {commentsLoading ? <div className="text-center text-gray-400 py-4"><Loader2 className="animate-spin mx-auto" /></div> : comments.length === 0 ? <p className="text-gray-400 text-sm py-4 text-center">لا توجد تعليقات</p> : (
                <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                  {comments.map((c, i) => (
                    <div key={i} className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1"><span className="text-sm font-medium text-gray-800 dark:text-gray-200">{c.author_name || c.author || 'مستخدم'}</span><span className="text-xs text-gray-400">{c.created_at?.split('T')[0]}</span></div>
                      <p className="text-sm text-gray-600 dark:text-gray-300">{c.content}</p>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <input type="text" value={newComment} onChange={e => setNewComment(e.target.value)} placeholder="أضف تعليقاً..." className={`flex-1 ${ic}`} onKeyDown={e => e.key === 'Enter' && addComment()} />
                <button onClick={addComment} className="px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"><Send className="w-4 h-4" /></button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">حذف التذكرة</h3>
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
