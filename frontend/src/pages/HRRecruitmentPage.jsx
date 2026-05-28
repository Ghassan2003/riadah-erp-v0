/**
 * Recruitment Management page - HR module.
 * Manage job requisitions, postings, applications, interviews, and offers.
 * Supports dark mode and Arabic text throughout.
 */

import { useState, useEffect } from 'react';
import { recruitmentAPI, departmentsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Edit2, Briefcase, FileText, Users, Calendar,
  Award, ChevronDown, ChevronUp, Filter, MoreVertical,
  Send, Clock, CheckCircle, XCircle, ArrowLeft,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/* ── Status color maps ── */

const REQUISITION_STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  filled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  cancelled: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
};

const REQUISITION_STATUS_LABELS = {
  draft: 'مسودة',
  pending: 'قيد المراجعة',
  approved: 'مُوافق',
  rejected: 'مرفوض',
  filled: 'مشغول',
  cancelled: 'ملغى',
};

const POSTING_STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  published: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  closed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const POSTING_STATUS_LABELS = {
  draft: 'مسودة',
  published: 'منشور',
  closed: 'مغلق',
};

const APPLICATION_STATUS_COLORS = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  screening: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  interview: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  offer: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  hired: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const APPLICATION_STATUS_LABELS = {
  new: 'جديد',
  screening: 'فرز',
  interview: 'مقابلة',
  offer: 'عرض',
  hired: 'مُعين',
  rejected: 'مرفوض',
};

const INTERVIEW_STATUS_COLORS = {
  scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const INTERVIEW_STATUS_LABELS = {
  scheduled: 'مجدول',
  completed: 'مكتمل',
  cancelled: 'ملغى',
};

const OFFER_STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  sent: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  accepted: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  declined: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  revoked: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
};

const OFFER_STATUS_LABELS = {
  draft: 'مسودة',
  sent: 'مرسل',
  accepted: 'مقبول',
  declined: 'مرفوض',
  revoked: 'ملغى',
};

const TABS = [
  { key: 'requisitions', label: 'طلبات التوظيف', icon: FileText },
  { key: 'postings', label: 'الإعلانات الوظيفية', icon: Briefcase },
  { key: 'applications', label: 'الطلبات', icon: Users },
  { key: 'interviews', label: 'المقابلات', icon: Calendar },
  { key: 'offers', label: 'العروض', icon: Award },
];

const EMPTY_REQUISITION_FORM = {
  title: '', department: '', position: '', vacancies: '', employment_type: 'full_time',
  min_salary: '', max_salary: '', description: '', requirements: '', status: 'draft',
};

export default function HRRecruitmentPage() {
  const { isHR } = useAuth();
  const canManage = isHR;

  const [activeTab, setActiveTab] = useState('requisitions');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  /* ── Data states ── */
  const [requisitions, setRequisitions] = useState([]);
  const [postings, setPostings] = useState([]);
  const [applications, setApplications] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [offers, setOffers] = useState([]);
  const [departments, setDepartments] = useState([]);

  /* ── Modal states ── */
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_REQUISITION_FORM });

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchDepartments = async () => {
    try {
      const res = await departmentsAPI.list();
      setDepartments(res.data.results || res.data || []);
    } catch (error) { console.error('Error:', error); }
  };

  const fetchTabData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'requisitions': {
          const res = await recruitmentAPI.getRequisitions({ search });
          setRequisitions(res.data.results || res.data || []);
          break;
        }
        case 'postings': {
          const res = await recruitmentAPI.getPostings({ search });
          setPostings(res.data.results || res.data || []);
          break;
        }
        case 'applications': {
          const params = { search };
          if (filterStatus) params.status = filterStatus;
          const res = await recruitmentAPI.getApplications(params);
          setApplications(res.data.results || res.data || []);
          break;
        }
        case 'interviews': {
          const res = await recruitmentAPI.getInterviews({ search });
          setInterviews(res.data.results || res.data || []);
          break;
        }
        case 'offers': {
          const res = await recruitmentAPI.getOffers({ search });
          setOffers(res.data.results || res.data || []);
          break;
        }
      }
    } catch {
      toast.error('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDepartments(); }, []);
  useEffect(() => { fetchTabData(); }, [activeTab, search, filterStatus]);

  // ──────────────────────── Actions ────────────────────────

  const openCreate = () => {
    setForm({ ...EMPTY_REQUISITION_FORM });
    setShowCreateModal(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!canManage) return;
    setSaving(true);
    try {
      const data = { ...form };
      data.vacancies = parseInt(data.vacancies) || 1;
      data.min_salary = parseFloat(data.min_salary) || 0;
      data.max_salary = parseFloat(data.max_salary) || 0;
      data.department = data.department || null;
      await recruitmentAPI.createRequisition(data);
      toast.success('تم إنشاء طلب التوظيف بنجاح');
      setShowCreateModal(false);
      fetchTabData();
    } catch (err) {
      const msg = err.response?.data?.non_field_errors?.[0]
        || err.response?.data?.title?.[0]
        || 'خطأ في حفظ البيانات';
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const handlePublishPosting = async (posting) => {
    try {
      await recruitmentAPI.publishPosting(posting.id);
      toast.success('تم نشر الإعلان بنجاح');
      fetchTabData();
    } catch {
      toast.error('خطأ في نشر الإعلان');
    }
  };

  const handleClosePosting = async (posting) => {
    try {
      await recruitmentAPI.closePosting(posting.id);
      toast.success('تم إغلاق الإعلان');
      fetchTabData();
    } catch {
      toast.error('خطأ في إغلاق الإعلان');
    }
  };

  const handleUpdateApplicationStatus = async (app, newStatus) => {
    try {
      await recruitmentAPI.updateApplication(app.id, { status: newStatus });
      toast.success('تم تحديث حالة الطلب');
      fetchTabData();
    } catch {
      toast.error('خطأ في تحديث الحالة');
    }
  };

  const openDetail = async (item, type) => {
    setSelectedItem({ ...item, _type: type });
    setShowDetailModal(true);
  };

  // ──────────────────────── Helpers ────────────────────────

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const inputClass =
    'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none transition-colors';
  const selectClass =
    'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 transition-colors';
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  const Spinner = () => (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );

  const StatusBadge = ({ status, colorMap, labelMap }) => (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${colorMap[status] || ''}`}>
      {labelMap[status] || status}
    </span>
  );

  const getTabData = () => {
    switch (activeTab) {
      case 'requisitions': return { items: requisitions, colorMap: REQUISITION_STATUS_COLORS, labelMap: REQUISITION_STATUS_LABELS };
      case 'postings': return { items: postings, colorMap: POSTING_STATUS_COLORS, labelMap: POSTING_STATUS_LABELS };
      case 'applications': return { items: applications, colorMap: APPLICATION_STATUS_COLORS, labelMap: APPLICATION_STATUS_LABELS };
      case 'interviews': return { items: interviews, colorMap: INTERVIEW_STATUS_COLORS, labelMap: INTERVIEW_STATUS_LABELS };
      case 'offers': return { items: offers, colorMap: OFFER_STATUS_COLORS, labelMap: OFFER_STATUS_LABELS };
      default: return { items: [], colorMap: {}, labelMap: {} };
    }
  };

  // ──────────────────────── Render ────────────────────────

  const { items, colorMap, labelMap } = getTabData();
  const filteredItems = filterStatus
    ? items.filter((i) => i.status === filterStatus)
    : items;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة التوظيف</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة طلبات التوظيف والإعلانات والتوظيف</p>
        </div>
        {canManage && activeTab === 'requisitions' && (
          <button onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm font-medium">
            <Plus className="w-5 h-5" />
            طلب توظيف جديد
          </button>
        )}
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setFilterStatus(''); }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.key
                ? 'bg-white dark:bg-gray-700 text-riadah-600 dark:text-riadah-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Search & Filter ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input type="text" placeholder="بحث..." value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none" />
          </div>
          {activeTab === 'applications' && (
            <div className="relative">
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                className={selectClass}>
                <option value="">كل الحالات</option>
                {Object.entries(APPLICATION_STATUS_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* ── Applications Funnel Summary ── */}
      {activeTab === 'applications' && !loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {Object.entries(APPLICATION_STATUS_LABELS).map(([key, label]) => {
            const count = items.filter((a) => a.status === key).length;
            return (
              <button key={key} onClick={() => setFilterStatus(filterStatus === key ? '' : key)}
                className={`bg-white dark:bg-gray-800 rounded-xl p-4 border shadow-sm transition-colors text-center ${
                  filterStatus === key
                    ? 'border-riadah-500 dark:border-riadah-400 ring-2 ring-riadah-500/20'
                    : 'border-gray-100 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{count}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{label}</p>
              </button>
            );
          })}
        </div>
      )}

      {/* ── Content ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
            <Spinner /><span>جاري التحميل...</span>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center">
            {activeTab === 'requisitions' && <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />}
            {activeTab === 'postings' && <Briefcase className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />}
            {activeTab === 'applications' && <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />}
            {activeTab === 'interviews' && <Calendar className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />}
            {activeTab === 'offers' && <Award className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />}
            <p className="text-gray-500 dark:text-gray-400">لا توجد بيانات</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  {activeTab === 'requisitions' && (
                    <>
                      <th className="px-4 py-3 text-right font-medium">العنوان</th>
                      <th className="px-4 py-3 text-right font-medium">القسم</th>
                      <th className="px-4 py-3 text-right font-medium">الوظيفة</th>
                      <th className="px-4 py-3 text-right font-medium">الشواغر</th>
                      <th className="px-4 py-3 text-right font-medium">الحالة</th>
                      <th className="px-4 py-3 text-right font-medium">التاريخ</th>
                      <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                    </>
                  )}
                  {activeTab === 'postings' && (
                    <>
                      <th className="px-4 py-3 text-right font-medium">العنوان</th>
                      <th className="px-4 py-3 text-right font-medium">القسم</th>
                      <th className="px-4 py-3 text-right font-medium">الحالة</th>
                      <th className="px-4 py-3 text-right font-medium">تاريخ النشر</th>
                      <th className="px-4 py-3 text-right font-medium">تاريخ الإغلاق</th>
                      <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                    </>
                  )}
                  {activeTab === 'applications' && (
                    <>
                      <th className="px-4 py-3 text-right font-medium">المتقدم</th>
                      <th className="px-4 py-3 text-right font-medium">الوظيفة</th>
                      <th className="px-4 py-3 text-right font-medium">البريد الإلكتروني</th>
                      <th className="px-4 py-3 text-right font-medium">الهاتف</th>
                      <th className="px-4 py-3 text-right font-medium">الحالة</th>
                      <th className="px-4 py-3 text-right font-medium">التاريخ</th>
                      <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                    </>
                  )}
                  {activeTab === 'interviews' && (
                    <>
                      <th className="px-4 py-3 text-right font-medium">المتقدم</th>
                      <th className="px-4 py-3 text-right font-medium">الوظيفة</th>
                      <th className="px-4 py-3 text-right font-medium">التاريخ</th>
                      <th className="px-4 py-3 text-right font-medium">النوع</th>
                      <th className="px-4 py-3 text-right font-medium">المقابل</th>
                      <th className="px-4 py-3 text-right font-medium">التقييم</th>
                      <th className="px-4 py-3 text-right font-medium">الحالة</th>
                    </>
                  )}
                  {activeTab === 'offers' && (
                    <>
                      <th className="px-4 py-3 text-right font-medium">المتقدم</th>
                      <th className="px-4 py-3 text-right font-medium">الوظيفة</th>
                      <th className="px-4 py-3 text-right font-medium">الراتب</th>
                      <th className="px-4 py-3 text-right font-medium">تاريخ البدء</th>
                      <th className="px-4 py-3 text-right font-medium">الحالة</th>
                      <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id}
                    className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">

                    {/* ── Requisitions row ── */}
                    {activeTab === 'requisitions' && (
                      <>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.department_name || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.position || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.vacancies || '-'}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} colorMap={REQUISITION_STATUS_COLORS} labelMap={REQUISITION_STATUS_LABELS} />
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.created_at?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <button onClick={() => openDetail(item, 'requisition')} title="عرض"
                              className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                              <Eye className="w-4 h-4" />
                            </button>
                            {canManage && item.status === 'draft' && (
                              <button onClick={() => openDetail(item, 'requisition')} title="تعديل"
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
                                <Edit2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </>
                    )}

                    {/* ── Postings row ── */}
                    {activeTab === 'postings' && (
                      <>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.department_name || '-'}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} colorMap={POSTING_STATUS_COLORS} labelMap={POSTING_STATUS_LABELS} />
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.published_at?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.closes_at?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            {canManage && item.status === 'draft' && (
                              <button onClick={() => handlePublishPosting(item)} title="نشر"
                                className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
                                <Send className="w-4 h-4" />
                              </button>
                            )}
                            {canManage && item.status === 'published' && (
                              <button onClick={() => handleClosePosting(item)} title="إغلاق"
                                className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                                <XCircle className="w-4 h-4" />
                              </button>
                            )}
                            <button onClick={() => openDetail(item, 'posting')} title="عرض"
                              className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    )}

                    {/* ── Applications row ── */}
                    {activeTab === 'applications' && (
                      <>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{item.full_name || item.applicant_name || '-'}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.position_title || item.job_title || '-'}</td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400" dir="ltr">{item.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.phone || '-'}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} colorMap={APPLICATION_STATUS_COLORS} labelMap={APPLICATION_STATUS_LABELS} />
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.applied_at?.split('T')[0] || item.created_at?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            {canManage && item.status === 'new' && (
                              <button onClick={() => handleUpdateApplicationStatus(item, 'screening')} title="بدء الفرز"
                                className="text-yellow-600 dark:text-yellow-400 p-1.5 rounded-lg hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors">
                                <Filter className="w-4 h-4" />
                              </button>
                            )}
                            {canManage && item.status === 'screening' && (
                              <button onClick={() => handleUpdateApplicationStatus(item, 'interview')} title="تحويل للمقابلة"
                                className="text-purple-600 dark:text-purple-400 p-1.5 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors">
                                <ArrowLeft className="w-4 h-4" />
                              </button>
                            )}
                            {canManage && item.status === 'interview' && (
                              <button onClick={() => handleUpdateApplicationStatus(item, 'offer')} title="تحويل للعرض"
                                className="text-orange-600 dark:text-orange-400 p-1.5 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors">
                                <Award className="w-4 h-4" />
                              </button>
                            )}
                            {canManage && item.status === 'offer' && (
                              <button onClick={() => handleUpdateApplicationStatus(item, 'hired')} title="تعيين"
                                className="text-green-600 dark:text-green-400 p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
                                <CheckCircle className="w-4 h-4" />
                              </button>
                            )}
                            {canManage && !['hired', 'rejected'].includes(item.status) && (
                              <button onClick={() => handleUpdateApplicationStatus(item, 'rejected')} title="رفض"
                                className="text-red-500 dark:text-red-400 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                                <XCircle className="w-4 h-4" />
                              </button>
                            )}
                            <button onClick={() => openDetail(item, 'application')} title="عرض"
                              className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    )}

                    {/* ── Interviews row ── */}
                    {activeTab === 'interviews' && (
                      <>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{item.applicant_name || item.candidate_name || '-'}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.position_title || item.job_title || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.interview_date || item.scheduled_at?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.interview_type || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.interviewer_name || '-'}</td>
                        <td className="px-4 py-3">
                          {item.score != null ? (
                            <span className="text-lg font-bold text-riadah-600 dark:text-riadah-400">{item.score}/100</span>
                          ) : (
                            <span className="text-gray-400 dark:text-gray-500">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} colorMap={INTERVIEW_STATUS_COLORS} labelMap={INTERVIEW_STATUS_LABELS} />
                        </td>
                      </>
                    )}

                    {/* ── Offers row ── */}
                    {activeTab === 'offers' && (
                      <>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{item.applicant_name || item.candidate_name || '-'}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.position_title || item.job_title || '-'}</td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                          {item.salary ? Number(item.salary).toLocaleString('ar-SA') : '-'} ر.س
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.start_date || '-'}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={item.status} colorMap={OFFER_STATUS_COLORS} labelMap={OFFER_STATUS_LABELS} />
                        </td>
                        <td className="px-4 py-3">
                          <button onClick={() => openDetail(item, 'offer')} title="عرض"
                            className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          MODALS
         ═══════════════════════════════════════════════════════════ */}

      {/* ── Create Requisition Modal ── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Plus className="w-5 h-5 text-riadah-500" />
                طلب توظيف جديد
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5">
              <div className="space-y-4">
                <div>
                  <label className={labelClass}>عنوان الطلب *</label>
                  <input type="text" value={form.title} onChange={(e) => updateField('title', e.target.value)} required className={inputClass} />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>القسم</label>
                    <select value={form.department} onChange={(e) => updateField('department', e.target.value)} className={selectClass}>
                      <option value="">اختر القسم</option>
                      {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>المسمى الوظيفي *</label>
                    <input type="text" value={form.position} onChange={(e) => updateField('position', e.target.value)} required className={inputClass} />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className={labelClass}>عدد الشواغر</label>
                    <input type="number" min="1" value={form.vacancies} onChange={(e) => updateField('vacancies', e.target.value)} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>نوع التوظيف</label>
                    <select value={form.employment_type} onChange={(e) => updateField('employment_type', e.target.value)} className={selectClass}>
                      <option value="full_time">دوام كامل</option>
                      <option value="part_time">دوام جزئي</option>
                      <option value="contract">عقد</option>
                      <option value="internship">تدريب</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>الحالة</label>
                    <select value={form.status} onChange={(e) => updateField('status', e.target.value)} className={selectClass}>
                      {Object.entries(REQUISITION_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>الحد الأدنى للراتب</label>
                    <input type="number" step="0.01" value={form.min_salary} onChange={(e) => updateField('min_salary', e.target.value)} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>الحد الأقصى للراتب</label>
                    <input type="number" step="0.01" value={form.max_salary} onChange={(e) => updateField('max_salary', e.target.value)} className={inputClass} />
                  </div>
                </div>
                <div>
                  <label className={labelClass}>الوصف الوظيفي</label>
                  <textarea value={form.description} onChange={(e) => updateField('description', e.target.value)} rows={3}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none transition-colors" />
                </div>
                <div>
                  <label className={labelClass}>المتطلبات</label>
                  <textarea value={form.requirements} onChange={(e) => updateField('requirements', e.target.value)} rows={3}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none transition-colors" />
                </div>
              </div>
              <div className="flex gap-3 pt-4 mt-4 border-t dark:border-gray-700">
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium flex items-center justify-center gap-2">
                  {saving ? <><Spinner /> جاري الحفظ...</> : 'إنشاء'}
                </button>
                <button type="button" onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Detail Modal ── */}
      {showDetailModal && selectedItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowDetailModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {selectedItem.title || selectedItem.full_name || selectedItem.applicant_name || 'تفاصيل'}
              </h3>
              <button onClick={() => setShowDetailModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                {selectedItem._type === 'requisition' && (
                  <>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">القسم</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.department_name || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">المسمى الوظيفي</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.position || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الشواغر</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.vacancies || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الحالة</span>
                      <p className="mt-0.5"><StatusBadge status={selectedItem.status} colorMap={REQUISITION_STATUS_COLORS} labelMap={REQUISITION_STATUS_LABELS} /></p>
                    </div>
                  </>
                )}
                {selectedItem._type === 'application' && (
                  <>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">البريد الإلكتروني</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.email || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الهاتف</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.phone || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الوظيفة</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.position_title || selectedItem.job_title || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الحالة</span>
                      <p className="mt-0.5"><StatusBadge status={selectedItem.status} colorMap={APPLICATION_STATUS_COLORS} labelMap={APPLICATION_STATUS_LABELS} /></p>
                    </div>
                  </>
                )}
                {selectedItem._type === 'offer' && (
                  <>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الوظيفة</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.position_title || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الراتب المقترح</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.salary ? Number(selectedItem.salary).toLocaleString('ar-SA') : '-'} ر.س</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">تاريخ البدء</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.start_date || '-'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">الحالة</span>
                      <p className="mt-0.5"><StatusBadge status={selectedItem.status} colorMap={OFFER_STATUS_COLORS} labelMap={OFFER_STATUS_LABELS} /></p>
                    </div>
                  </>
                )}
              </div>

              {/* Description / Notes for requisition */}
              {selectedItem._type === 'requisition' && selectedItem.description && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">الوصف الوظيفي</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{selectedItem.description}</p>
                </div>
              )}
              {selectedItem._type === 'requisition' && selectedItem.requirements && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">المتطلبات</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{selectedItem.requirements}</p>
                </div>
              )}

              <button onClick={() => setShowDetailModal(false)}
                className="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
