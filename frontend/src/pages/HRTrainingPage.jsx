/**
 * Training Management page - HR module.
 * Manage training needs, courses, sessions, enrollments, and budget.
 * Supports dark mode and Arabic text throughout.
 */

import { useState, useEffect } from 'react';
import { trainingAPI, departmentsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Eye, Edit2, BookOpen, Users, Calendar,
  Award, GraduationCap, DollarSign, BarChart3, TrendingUp,
  AlertTriangle, CheckCircle, Clock, XCircle, Save,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/* ── Status color maps ── */

const PRIORITY_COLORS = {
  low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const PRIORITY_LABELS = {
  low: 'منخفضة',
  medium: 'متوسطة',
  high: 'عالية',
  critical: 'حرجة',
};

const SESSION_STATUS_COLORS = {
  planned: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const SESSION_STATUS_LABELS = {
  planned: 'مخطط',
  scheduled: 'مجدول',
  in_progress: 'قيد التنفيذ',
  completed: 'مكتمل',
  cancelled: 'ملغى',
};

const ENROLLMENT_STATUS_COLORS = {
  enrolled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  dropped: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  certified: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
};

const ENROLLMENT_STATUS_LABELS = {
  enrolled: 'مسجل',
  in_progress: 'قيد الدراسة',
  completed: 'مكتمل',
  dropped: 'منسحب',
  certified: 'حاصل على الشهادة',
};

const TABS = [
  { key: 'needs', label: 'الاحتياجات التدريبية', icon: AlertTriangle },
  { key: 'courses', label: 'الدورات', icon: BookOpen },
  { key: 'sessions', label: 'الجلسات', icon: Calendar },
  { key: 'enrollments', label: 'التسجيلات', icon: Users },
  { key: 'budget', label: 'الميزانية', icon: DollarSign },
];

const EMPTY_NEED_FORM = {
  title: '', department: '', priority: 'medium', description: '',
  target_employees: '', deadline: '', status: 'open',
};

export default function HRTrainingPage() {
  const { isHR } = useAuth();
  const canManage = isHR;

  const [activeTab, setActiveTab] = useState('needs');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  /* ── Data states ── */
  const [needs, setNeeds] = useState([]);
  const [courses, setCourses] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [budgetData, setBudgetData] = useState(null);
  const [departments, setDepartments] = useState([]);

  /* ── Modal states ── */
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_NEED_FORM });

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchDepartments = async () => {
    try {
      const res = await departmentsAPI.list();
      setDepartments(res.data.results || res.data || []);
    } catch { /* silent */ }
  };

  const fetchTabData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'needs': {
          const res = await trainingAPI.getNeeds({ search });
          setNeeds(res.data.results || res.data || []);
          break;
        }
        case 'courses': {
          const res = await trainingAPI.getCourses({ search });
          setCourses(res.data.results || res.data || []);
          break;
        }
        case 'sessions': {
          const res = await trainingAPI.getSessions({ search });
          setSessions(res.data.results || res.data || []);
          break;
        }
        case 'enrollments': {
          const params = { search };
          if (filterStatus) params.status = filterStatus;
          const res = await trainingAPI.getEnrollments(params);
          setEnrollments(res.data.results || res.data || []);
          break;
        }
        case 'budget': {
          const res = await trainingAPI.getBudget();
          setBudgetData(res.data || {});
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
    if (activeTab === 'needs') {
      setForm({ ...EMPTY_NEED_FORM });
    } else {
      setForm({});
    }
    setShowCreateModal(true);
  };

  const handleCreateNeed = async (e) => {
    e.preventDefault();
    if (!canManage) return;
    setSaving(true);
    try {
      const data = { ...form };
      data.department = data.department || null;
      data.deadline = data.deadline || null;
      await trainingAPI.createNeed(data);
      toast.success('تم إنشاء الاحتياج التدريبي بنجاح');
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

  const openDetail = (item) => {
    setSelectedItem(item);
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

  const formatCurrency = (val) => Number(val || 0).toLocaleString('ar-SA', { minimumFractionDigits: 2 });

  const getBudgetUtilization = (budget, actual) => {
    if (!budget || budget <= 0) return 0;
    return Math.min((actual / budget) * 100, 100);
  };

  const getUtilizationColor = (pct) => {
    if (pct >= 90) return 'bg-red-500';
    if (pct >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة التدريب</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة الاحتياجات التدريبية والدورات والجلسات</p>
        </div>
        {canManage && activeTab !== 'budget' && (
          <button onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm font-medium">
            <Plus className="w-5 h-5" />
            {activeTab === 'needs' && 'احتياج تدريبي جديد'}
            {activeTab === 'courses' && 'دورة جديدة'}
            {activeTab === 'sessions' && 'جلسة جديدة'}
            {activeTab === 'enrollments' && 'تسجيل جديد'}
          </button>
        )}
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setFilterStatus(''); setSearch(''); }}
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
      {activeTab !== 'budget' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input type="text" placeholder="بحث..." value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none" />
            </div>
            {activeTab === 'enrollments' && (
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                className={selectClass}>
                <option value="">كل الحالات</option>
                {Object.entries(ENROLLMENT_STATUS_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB CONTENT
         ═══════════════════════════════════════════════════════════ */}

      {/* ── Tab 1: Training Needs ── */}
      {activeTab === 'needs' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
              <Spinner /><span>جاري التحميل...</span>
            </div>
          ) : needs.length === 0 ? (
            <div className="p-12 text-center">
              <AlertTriangle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد احتياجات تدريبية</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">العنوان</th>
                    <th className="px-4 py-3 text-right font-medium">القسم</th>
                    <th className="px-4 py-3 text-right font-medium">الأولوية</th>
                    <th className="px-4 py-3 text-right font-medium">الموظفون المستهدفون</th>
                    <th className="px-4 py-3 text-right font-medium">الموعد النهائي</th>
                    <th className="px-4 py-3 text-right font-medium">الحالة</th>
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {needs.map((item) => (
                    <tr key={item.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                        {item.description && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5 truncate max-w-xs">{item.description}</p>}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.department_name || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[item.priority] || ''}`}>
                          {PRIORITY_LABELS[item.priority] || item.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.target_employees || '-'}</td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.deadline || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          item.status === 'open'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {item.status === 'open' ? 'مفتوح' : 'مغلق'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button onClick={() => openDetail(item)} title="عرض"
                            className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Tab 2: Courses (Cards) ── */}
      {activeTab === 'courses' && (
        loading ? (
          <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
            <Spinner /><span>جاري التحميل...</span>
          </div>
        ) : courses.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
            <BookOpen className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">لا توجد دورات تدريبية</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <div key={course.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-10 h-10 bg-riadah-100 dark:bg-riadah-900/30 rounded-lg flex items-center justify-center">
                      <BookOpen className="w-5 h-5 text-riadah-600 dark:text-riadah-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">{course.title}</h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{course.category || '-'}</p>
                    </div>
                  </div>
                  <button onClick={() => openDetail(course)} title="عرض"
                    className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">{course.description || '-'}</p>
                <div className="space-y-2 text-sm">
                  {course.provider && (
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">مقدم الدورة</span>
                      <span className="text-gray-900 dark:text-gray-100">{course.provider}</span>
                    </div>
                  )}
                  {course.duration_hours != null && (
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">المدة</span>
                      <span className="text-gray-900 dark:text-gray-100">{course.duration_hours} ساعة</span>
                    </div>
                  )}
                  {course.cost != null && (
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">التكلفة</span>
                      <span className="font-medium text-riadah-600 dark:text-riadah-400">{formatCurrency(course.cost)} ر.س</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* ── Tab 3: Sessions ── */}
      {activeTab === 'sessions' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
              <Spinner /><span>جاري التحميل...</span>
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-12 text-center">
              <Calendar className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد جلسات تدريبية</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">الدورة</th>
                    <th className="px-4 py-3 text-right font-medium">المدرب</th>
                    <th className="px-4 py-3 text-right font-medium">تاريخ البدء</th>
                    <th className="px-4 py-3 text-right font-medium">تاريخ الانتهاء</th>
                    <th className="px-4 py-3 text-right font-medium">المكان</th>
                    <th className="px-4 py-3 text-right font-medium">المسجلون</th>
                    <th className="px-4 py-3 text-right font-medium">الحالة</th>
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((item) => (
                    <tr key={item.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{item.course_title || item.course_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.instructor || '-'}</td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.start_date || '-'}</td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.end_date || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.location || '-'}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 text-gray-700 dark:text-gray-300">
                          <Users className="w-3.5 h-3.5" />
                          {item.enrollment_count ?? item.enrolled_count ?? 0}
                        </span>
                        {item.max_capacity && (
                          <span className="text-gray-400 dark:text-gray-500">/{item.max_capacity}</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${SESSION_STATUS_COLORS[item.status] || ''}`}>
                          {SESSION_STATUS_LABELS[item.status] || item.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => openDetail(item)} title="عرض"
                          className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Tab 4: Enrollments ── */}
      {activeTab === 'enrollments' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
              <Spinner /><span>جاري التحميل...</span>
            </div>
          ) : enrollments.length === 0 ? (
            <div className="p-12 text-center">
              <GraduationCap className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد تسجيلات</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">الموظف</th>
                    <th className="px-4 py-3 text-right font-medium">الدورة</th>
                    <th className="px-4 py-3 text-right font-medium">الجلسة</th>
                    <th className="px-4 py-3 text-right font-medium">التسجيل</th>
                    <th className="px-4 py-3 text-right font-medium">الدرجة</th>
                    <th className="px-4 py-3 text-right font-medium">الشهادة</th>
                    <th className="px-4 py-3 text-right font-medium">الحالة</th>
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {(filterStatus ? enrollments.filter((e) => e.status === filterStatus) : enrollments).map((item) => (
                    <tr key={item.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{item.employee_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.course_title || item.course_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{item.session_title || item.session_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{item.enrolled_at?.split('T')[0] || item.created_at?.split('T')[0] || '-'}</td>
                      <td className="px-4 py-3">
                        {item.score != null ? (
                          <span className="text-lg font-bold text-riadah-600 dark:text-riadah-400">{item.score}/100</span>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {item.has_certificate || item.certificate_number ? (
                          <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
                            <Award className="w-4 h-4" />
                            <span className="text-xs">صادر</span>
                          </span>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ENROLLMENT_STATUS_COLORS[item.status] || ''}`}>
                          {ENROLLMENT_STATUS_LABELS[item.status] || item.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => openDetail(item)} title="عرض"
                          className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Tab 5: Budget ── */}
      {activeTab === 'budget' && (
        <div className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
              <Spinner /><span>جاري التحميل...</span>
            </div>
          ) : budgetData && (budgetData.items || budgetData.departments || budgetData.categories) ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-riadah-100 dark:bg-riadah-900/30 rounded-lg flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-riadah-600 dark:text-riadah-400" />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">الميزانية الإجمالية</p>
                  </div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{formatCurrency(budgetData.total_budget)} ر.س</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">المصروف الفعلي</p>
                  </div>
                  <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{formatCurrency(budgetData.total_spent || budgetData.total_actual)} ر.س</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                      <BarChart3 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">المتبقي</p>
                  </div>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">{formatCurrency(budgetData.total_remaining || (budgetData.total_budget - (budgetData.total_spent || budgetData.total_actual || 0)))} ر.س</p>
                </div>
              </div>

              {/* Utilization Bars */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">استخدام الميزانية حسب القسم</h3>
                <div className="space-y-4">
                  {(budgetData.items || budgetData.departments || budgetData.categories || []).map((item, idx) => {
                    const deptBudget = item.budget || item.allocated || 0;
                    const deptActual = item.actual || item.spent || 0;
                    const pct = getBudgetUtilization(deptBudget, deptActual);
                    return (
                      <div key={idx}>
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.department_name || item.name || item.category || '-'}</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatCurrency(deptActual)} / {formatCurrency(deptBudget)} ر.س ({Math.round(pct)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                          <div
                            className={`h-2.5 rounded-full transition-all ${getUtilizationColor(pct)}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
              <BarChart3 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد بيانات ميزانية</p>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          MODALS
         ═══════════════════════════════════════════════════════════ */}

      {/* ── Create Training Need Modal ── */}
      {showCreateModal && activeTab === 'needs' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Plus className="w-5 h-5 text-riadah-500" />
                احتياج تدريبي جديد
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateNeed} className="p-5">
              <div className="space-y-4">
                <div>
                  <label className={labelClass}>العنوان *</label>
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
                    <label className={labelClass}>الأولوية</label>
                    <select value={form.priority} onChange={(e) => updateField('priority', e.target.value)} className={selectClass}>
                      {Object.entries(PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>الموعد النهائي</label>
                    <input type="date" value={form.deadline} onChange={(e) => updateField('deadline', e.target.value)} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>عدد الموظفين المستهدفين</label>
                    <input type="number" min="1" value={form.target_employees} onChange={(e) => updateField('target_employees', e.target.value)} className={inputClass} />
                  </div>
                </div>
                <div>
                  <label className={labelClass}>الوصف</label>
                  <textarea value={form.description} onChange={(e) => updateField('description', e.target.value)} rows={3}
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
                {selectedItem.title || selectedItem.course_title || selectedItem.employee_name || 'تفاصيل'}
              </h3>
              <button onClick={() => setShowDetailModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                {selectedItem.department_name && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">القسم</span>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.department_name}</p>
                  </div>
                )}
                {selectedItem.priority && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">الأولوية</span>
                    <p className="mt-0.5">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[selectedItem.priority]}`}>
                        {PRIORITY_LABELS[selectedItem.priority]}
                      </span>
                    </p>
                  </div>
                )}
                {selectedItem.provider && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">مقدم الدورة</span>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedItem.provider}</p>
                  </div>
                )}
                {selectedItem.cost != null && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">التكلفة</span>
                    <p className="font-medium text-riadah-600 dark:text-riadah-400">{formatCurrency(selectedItem.cost)} ر.س</p>
                  </div>
                )}
                {selectedItem.score != null && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">الدرجة</span>
                    <p className="font-medium text-riadah-600 dark:text-riadah-400">{selectedItem.score}/100</p>
                  </div>
                )}
                {selectedItem.status && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">الحالة</span>
                    <p className="mt-0.5">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ENROLLMENT_STATUS_COLORS[selectedItem.status] || SESSION_STATUS_COLORS[selectedItem.status] || ''}`}>
                        {ENROLLMENT_STATUS_LABELS[selectedItem.status] || SESSION_STATUS_LABELS[selectedItem.status] || selectedItem.status}
                      </span>
                    </p>
                  </div>
                )}
              </div>

              {selectedItem.description && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">الوصف</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{selectedItem.description}</p>
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
