/**
 * EmployeeSelfServicePage - بوابة الخدمة الذاتية للموظفين.
 * يعرض معلومات الموظف الشخصية، أرصدة الإجازات، سجل الحضور، بيانات الراتب، والمستندات.
 * يدعم الوضع الداكن و RTL.
 */

import { useState, useEffect } from 'react';
import { hrAPI, employeesAPI, attendanceAPI, leavesAPI, leaveBalancesAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  User, Briefcase, CalendarDays, Clock, FileText, Plus, X, Eye,
  MapPin, Phone, Mail, Building2, Hash, Calendar, Download,
  Shield, Award, ClipboardList, CreditCard, Wallet, CheckCircle,
  AlertCircle, XCircle, Loader2, ChevronLeft, ChevronRight,
  Palmtree, Heart, AlertTriangle, Pill, Plane, Coffee,
  FolderOpen, Paperclip,
} from 'lucide-react';

/* ─── Spinner ─── */
const Spinner = () => (
  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

/* ─── الحالات والألوان ─── */
const LEAVE_TYPE_MAP = {
  annual: { label: 'سنوية', icon: Palmtree, color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  sick: { label: 'مرضية', icon: Heart, color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  emergency: { label: 'طارئة', icon: AlertTriangle, color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  maternity: { label: 'أمومة', icon: Pill, color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400' },
  hajj: { label: 'حج', icon: Plane, color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  unpaid: { label: 'بدون راتب', icon: Coffee, color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  other: { label: 'أخرى', icon: FileText, color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
};

const STATUS_BADGE = {
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

const STATUS_LABEL = {
  pending: 'معلّق',
  approved: 'معتمد',
  rejected: 'مرفوض',
  cancelled: 'ملغي',
};

const ATTENDANCE_COLOR = {
  present: 'bg-green-500',
  absent: 'bg-red-500',
  late: 'bg-orange-500',
  half_day: 'bg-yellow-500',
  holiday: 'bg-blue-500',
  leave: 'bg-purple-500',
};

const ATTENDANCE_LABEL = {
  present: 'حاضر',
  absent: 'غائب',
  late: 'متأخر',
  half_day: 'نصف يوم',
  holiday: 'عطلة',
  leave: 'إجازة',
};

/* ─── أسماء الأشهر العربية ─── */
const MONTH_NAMES_AR = [
  'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
];

const DAY_NAMES_AR = ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت'];

export default function EmployeeSelfServicePage() {
  const { locale } = useI18n();
  const { user } = useAuth();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const fmtInt = (v) => Number(v || 0).toLocaleString(nl);

  /* ─── حالة البيانات ─── */
  const [loading, setLoading] = useState(true);
  const [employeeData, setEmployeeData] = useState(null);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [hrStats, setHrStats] = useState({});

  /* ─── الحضور الشهري ─── */
  const [calMonth, setCalMonth] = useState(() => new Date().getMonth());
  const [calYear, setCalYear] = useState(() => new Date().getFullYear());

  /* ─── المودال ─── */
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    leave_type: 'annual',
    start_date: '',
    end_date: '',
    reason: '',
  });

  /* ─── حقول الإدخال ─── */
  const inputCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const selectCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700';

  /* ─── تحميل البيانات ─── */
  useEffect(() => {
    if (!user?.id) return;
    loadEmployeeData();
  }, [user]);

  const loadEmployeeData = async () => {
    setLoading(true);
    try {
      const promises = [
        employeesAPI.get(user.id).catch(() => null),
        leaveBalancesAPI.list({ employee: user.id }).catch(() => ({ data: [] })),
        leavesAPI.list({ employee: user.id }).catch(() => ({ data: [] })),
        attendanceAPI.list({ employee: user.id }).catch(() => ({ data: [] })),
        hrAPI.getStats().catch(() => ({ data: {} })),
      ];
      const results = await Promise.all(promises);
      setEmployeeData(results[0]?.data || null);
      setLeaveBalances(results[1].data?.results || results[1].data || []);
      setLeaveRequests(results[2].data?.results || results[2].data || []);
      setAttendanceRecords(results[3].data?.results || results[3].data || []);
      setHrStats(results[4].data || {});
    } catch (err) {
      toast.error('حدث خطأ أثناء تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  /* ─── حساب إحصائيات الحضور للشهر الحالي ─── */
  const getMonthAttendanceStats = () => {
    const monthRecords = attendanceRecords.filter((r) => {
      const d = new Date(r.date);
      return d.getMonth() === calMonth && d.getFullYear() === calYear;
    });
    const present = monthRecords.filter((r) => r.status === 'present').length;
    const absent = monthRecords.filter((r) => r.status === 'absent').length;
    const late = monthRecords.filter((r) => r.status === 'late').length;
    return { present, absent, late, total: monthRecords.length };
  };

  /* ─── تقويم الحضور الشهري ─── */
  const getCalendarDays = () => {
    const firstDay = new Date(calYear, calMonth, 1);
    const lastDay = new Date(calYear, calMonth + 1, 0);
    const startPadding = firstDay.getDay(); // 0=Sunday
    const daysInMonth = lastDay.getDate();

    const cells = [];
    // Padding for first week
    for (let i = 0; i < startPadding; i++) {
      cells.push({ day: null, record: null });
    }
    // Days of month
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const record = attendanceRecords.find((r) => r.date === dateStr);
      const isToday = new Date().toDateString() === new Date(calYear, calMonth, d).toDateString();
      cells.push({ day: d, record, dateStr, isToday });
    }
    return cells;
  };

  /* ─── تقديم طلب إجازة ─── */
  const handleSubmitLeave = async (e) => {
    e.preventDefault();
    if (!user?.id) return;
    setSaving(true);
    try {
      await leavesAPI.create({
        ...leaveForm,
        employee: user.id,
      });
      toast.success('تم تقديم طلب الإجازة بنجاح');
      setShowLeaveModal(false);
      setLeaveForm({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
      loadEmployeeData();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'حدث خطأ أثناء تقديم الطلب');
    } finally {
      setSaving(false);
    }
  };

  /* ─── التنقل بين الأشهر ─── */
  const prevMonth = () => {
    if (calMonth === 0) { setCalMonth(11); setCalYear(calYear - 1); }
    else setCalMonth(calMonth - 1);
  };
  const nextMonth = () => {
    if (calMonth === 11) { setCalMonth(0); setCalYear(calYear + 1); }
    else setCalMonth(calMonth + 1);
  };

  /* ─── حالة التحميل ─── */
  if (loading) {
    return (
      <div dir="rtl" className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
          <p className="text-gray-500 dark:text-gray-400">جاري تحميل البيانات...</p>
        </div>
      </div>
    );
  }

  const attStats = getMonthAttendanceStats();
  const calendarCells = getCalendarDays();
  const emp = employeeData;

  return (
    <div dir="rtl" className="space-y-6">

      {/* ─── العنوان ─── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">بوابة الخدمة الذاتية</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">عرض معلوماتك الشخصية والإجازات والحضور والراتب</p>
        </div>
      </div>

      {/* ─── بطاقة المعلومات الشخصية ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="bg-gradient-to-l from-[#003366] to-[#004d99] p-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5">
            {/* الصورة */}
            <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center text-white text-2xl font-bold border-3 border-white/40 shrink-0">
              {emp?.avatar ? (
                <img src={emp.avatar} alt="" className="w-full h-full rounded-full object-cover" />
              ) : (
                <User className="w-10 h-10 text-white/80" />
              )}
            </div>
            <div className="text-center sm:text-right text-white flex-1">
              <h2 className="text-xl font-bold">{emp?.full_name || user?.full_name || 'الموظف'}</h2>
              <div className="flex flex-wrap justify-center sm:justify-start gap-x-5 gap-y-1 mt-2 text-sm text-white/80">
                {emp?.employee_number && (
                  <span className="flex items-center gap-1.5"><Hash className="w-3.5 h-3.5" /> {emp.employee_number}</span>
                )}
                {emp?.department_name && (
                  <span className="flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5" /> {emp.department_name}</span>
                )}
                {emp?.position && (
                  <span className="flex items-center gap-1.5"><Briefcase className="w-3.5 h-3.5" /> {emp.position}</span>
                )}
                {emp?.hire_date && (
                  <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> {emp.hire_date}</span>
                )}
              </div>
              <div className="flex flex-wrap justify-center sm:justify-start gap-x-5 gap-y-1 mt-1 text-sm text-white/70">
                {emp?.phone && (
                  <span className="flex items-center gap-1.5"><Phone className="w-3.5 h-3.5" /> {emp.phone}</span>
                )}
                {emp?.email && (
                  <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5" /> {emp.email}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── الإحصائيات السريعة ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* أرصدة الإجازات */}
        {leaveBalances.slice(0, 3).map((lb) => {
          const typeInfo = LEAVE_TYPE_MAP[lb.leave_type] || LEAVE_TYPE_MAP.other;
          const Icon = typeInfo.icon;
          return (
            <div key={lb.id || lb.leave_type} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${typeInfo.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500 dark:text-gray-400">رصيد {typeInfo.label}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{fmtInt(lb.remaining)}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">المستخدم: {fmtInt(lb.used || 0)} من {fmtInt(lb.total || 0)}</p>
                </div>
              </div>
              {/* شريط التقدم */}
              <div className="mt-3 w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full bg-blue-500 dark:bg-blue-400 transition-all"
                  style={{ width: `${Math.min(((lb.used || 0) / (lb.total || 1)) * 100, 100)}%` }}
                />
              </div>
            </div>
          );
        })}

        {/* إحصائيات الحضور */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
              <Clock className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-500 dark:text-gray-400">حضور هذا الشهر</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{fmtInt(attStats.present)}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                غائب: {attStats.absent} | متأخر: {attStats.late}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ─── طلبات الإجازات ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            طلبات الإجازات
          </h3>
          <button
            onClick={() => setShowLeaveModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-sm"
          >
            <Plus className="w-4 h-4" />
            طلب جديد
          </button>
        </div>
        <div className="overflow-x-auto">
          {leaveRequests.length === 0 ? (
            <div className="p-12 text-center">
              <CalendarDays className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد طلبات إجازة</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">نوع الإجازة</th>
                  <th className="px-4 py-3 text-right font-medium">من</th>
                  <th className="px-4 py-3 text-right font-medium">إلى</th>
                  <th className="px-4 py-3 text-right font-medium">الأيام</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                  <th className="px-4 py-3 text-right font-medium">السبب</th>
                </tr>
              </thead>
              <tbody>
                {leaveRequests.map((lr) => {
                  const typeInfo = LEAVE_TYPE_MAP[lr.leave_type] || LEAVE_TYPE_MAP.other;
                  return (
                    <tr key={lr.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{lr.start_date}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{lr.end_date}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{lr.days} يوم</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1 w-fit ${STATUS_BADGE[lr.approval_status] || ''}`}>
                          {lr.approval_status === 'approved' && <CheckCircle className="w-3 h-3" />}
                          {lr.approval_status === 'rejected' && <XCircle className="w-3 h-3" />}
                          {lr.approval_status === 'pending' && <AlertCircle className="w-3 h-3" />}
                          {STATUS_LABEL[lr.approval_status] || lr.approval_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400 max-w-[200px] truncate">{lr.reason || '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ─── سجل الحضور الشهري (تقويم) ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            سجل الحضور الشهري
          </h3>
          <div className="flex items-center gap-3">
            <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ChevronRight className="w-5 h-5" />
            </button>
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 min-w-[120px] text-center">
              {MONTH_NAMES_AR[calMonth]} {calYear}
            </span>
            <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* التقويم */}
        <div className="p-5">
          <div className="grid grid-cols-7 gap-1 mb-2">
            {DAY_NAMES_AR.map((day) => (
              <div key={day} className="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-1">
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {calendarCells.map((cell, idx) => (
              <div
                key={idx}
                className={`aspect-square flex flex-col items-center justify-center rounded-lg text-sm transition-all ${
                  cell.day === null
                    ? 'bg-transparent'
                    : cell.isToday
                    ? 'ring-2 ring-blue-500 dark:ring-blue-400'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                } ${cell.day ? 'bg-gray-50 dark:bg-gray-700/30' : ''}`}
                title={cell.record ? `${ATTENDANCE_LABEL[cell.record.status] || cell.record.status} - ${cell.dateStr}` : cell.dateStr}
              >
                <span className={`text-xs ${cell.isToday ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300'}`}>
                  {cell.day || ''}
                </span>
                {cell.record && (
                  <div className={`w-2 h-2 rounded-full mt-0.5 ${ATTENDANCE_COLOR[cell.record.status] || 'bg-gray-400'}`} />
                )}
              </div>
            ))}
          </div>

          {/* مفتاح الألوان */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
            {Object.entries(ATTENDANCE_COLOR).map(([status, color]) => (
              <div key={status} className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                <div className={`w-3 h-3 rounded-full ${color}`} />
                {ATTENDANCE_LABEL[status]}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── بطاقة الراتب ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 mb-4">
          <Wallet className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          معلومات الراتب
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">الراتب الأساسي</p>
            <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{emp?.basic_salary ? fmt(emp.basic_salary) : '***'}</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">بدل السكن</p>
            <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{emp?.housing_allowance ? fmt(emp.housing_allowance) : '***'}</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">بدل النقل</p>
            <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{emp?.transport_allowance ? fmt(emp.transport_allowance) : '***'}</p>
          </div>
          <div className="bg-gradient-to-l from-[#003366] to-[#004d99] rounded-lg p-4 text-center text-white">
            <p className="text-xs text-white/70 mb-1">إجمالي الراتب</p>
            <p className="text-lg font-bold">{emp?.total_salary ? fmt(emp.total_salary) : '***'}</p>
          </div>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-3 text-center flex items-center justify-center gap-1">
          <Shield className="w-3 h-3" />
          البيانات المالية معروضة جزئياً للحفاظ على الخصوصية
        </p>
      </div>

      {/* ─── المستندات ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 mb-4">
          <FolderOpen className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          المستندات والمرفقات
        </h3>
        {(emp?.documents && emp.documents.length > 0) ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {emp.documents.map((doc, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-600">
                <Paperclip className="w-4 h-4 text-gray-400 dark:text-gray-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">{doc.name || doc.title || `مستند ${idx + 1}`}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">{doc.uploaded_at || doc.date || '-'}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="text-gray-500 dark:text-gray-400 text-sm">لا توجد مستندات مرفقة حالياً</p>
          </div>
        )}
      </div>

      {/* ─── مودال طلب إجازة جديد ─── */}
      {showLeaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">طلب إجازة جديد</h3>
              <button onClick={() => setShowLeaveModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmitLeave} className="p-5 space-y-4">
              {/* نوع الإجازة */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع الإجازة *</label>
                <select
                  value={leaveForm.leave_type}
                  onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                  className={selectCls}
                >
                  {Object.entries(LEAVE_TYPE_MAP).map(([key, info]) => (
                    <option key={key} value={key}>{info.label}</option>
                  ))}
                </select>
              </div>

              {/* التواريخ */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">من تاريخ *</label>
                  <input
                    type="date"
                    value={leaveForm.start_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                    required
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">إلى تاريخ *</label>
                  <input
                    type="date"
                    value={leaveForm.end_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                    required
                    className={inputCls}
                  />
                </div>
              </div>

              {/* السبب */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">السبب</label>
                <textarea
                  value={leaveForm.reason}
                  onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                  rows={3}
                  placeholder="اكتب سبب الإجازة..."
                  className={`${inputCls} resize-none`}
                />
              </div>

              {/* الأزرار */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm transition-colors"
                >
                  {saving ? (
                    <span className="flex items-center justify-center gap-2">
                      <Spinner /> جاري التقديم...
                    </span>
                  ) : (
                    'تقديم الطلب'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowLeaveModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium text-sm transition-colors"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
