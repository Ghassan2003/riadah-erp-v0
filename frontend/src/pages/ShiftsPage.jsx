/**
 * Shift Management page - HR module.
 * Manage work shifts and employee shift assignments.
 * Supports dark mode, RTL, and i18n.
 */

import { useState, useEffect } from 'react';
import { shiftsAPI, employeeShiftsAPI, employeesAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Search, Plus, X, Edit2, Trash2, Clock, Moon, Sun, Calendar, Users,
} from 'lucide-react';

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

const ALL_DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

const DAY_KEYS = {
  mon: 'monday',
  tue: 'tuesday',
  wed: 'wednesday',
  thu: 'thursday',
  fri: 'friday',
  sat: 'saturday',
  sun: 'sunday',
};

const DAY_AR = {
  mon: 'الاثنين',
  tue: 'الثلاثاء',
  wed: 'الأربعاء',
  thu: 'الخميس',
  fri: 'الجمعة',
  sat: 'السبت',
  sun: 'الأحد',
};

const DAY_EN = {
  mon: 'Mon',
  tue: 'Tue',
  wed: 'Wed',
  thu: 'Thu',
  fri: 'Fri',
  sat: 'Sat',
  sun: 'Sun',
};

const emptyShiftForm = {
  name: '',
  start_time: '',
  end_time: '',
  break_duration: 0,
  is_night: false,
  applicable_days: ['sun', 'mon', 'tue', 'wed', 'thu'],
  is_active: true,
};

const emptyAssignmentForm = {
  employee: '',
  shift: '',
  effective_date: '',
  end_date: '',
  is_active: true,
};

export default function ShiftsPage() {
  const { t, locale } = useI18n();
  const { isHR } = useAuth();
  const canManage = isHR;

  // ── State ────────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState('shifts');
  const [shifts, setShifts] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [saving, setSaving] = useState(false);

  // Shift modal
  const [showShiftModal, setShowShiftModal] = useState(false);
  const [editingShift, setEditingShift] = useState(null);
  const [shiftForm, setShiftForm] = useState(emptyShiftForm);

  // Assignment modal
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [assignmentForm, setAssignmentForm] = useState(emptyAssignmentForm);

  // ── Fetch helpers ────────────────────────────────────────────────────────
  const fetchShifts = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (filterStatus) params.is_active = filterStatus === 'active';
      const res = await shiftsAPI.list(params);
      setShifts(res.data.results || res.data || []);
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignments = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (filterStatus) params.is_active = filterStatus === 'active';
      const res = await employeeShiftsAPI.list(params);
      setAssignments(res.data.results || res.data || []);
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const res = await employeesAPI.list({ page_size: 500 });
      setEmployees(res.data.results || res.data || []);
    } catch (error) { console.error('Error:', error); }
  };

  // ── Effects ──────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (activeTab === 'shifts') fetchShifts();
    else fetchAssignments();
  }, [activeTab, search, filterStatus]);

  // ── Day helpers ──────────────────────────────────────────────────────────
  const getDayLabel = (dayKey) => {
    if (locale === 'ar') return DAY_AR[dayKey] || dayKey;
    return DAY_EN[dayKey] || dayKey;
  };

  const toggleDay = (dayKey) => {
    setShiftForm((prev) => {
      const days = prev.applicable_days.includes(dayKey)
        ? prev.applicable_days.filter((d) => d !== dayKey)
        : [...prev.applicable_days, dayKey];
      return { ...prev, applicable_days: days };
    });
  };

  // ── Shift CRUD ───────────────────────────────────────────────────────────
  const openCreateShift = () => {
    setEditingShift(null);
    setShiftForm({ ...emptyShiftForm });
    setShowShiftModal(true);
  };

  const openEditShift = (shift) => {
    setEditingShift(shift);
    setShiftForm({
      name: shift.name || '',
      start_time: shift.start_time || '',
      end_time: shift.end_time || '',
      break_duration: shift.break_duration || 0,
      is_night: shift.is_night || false,
      applicable_days: shift.applicable_days || [],
      is_active: shift.is_active !== false,
    });
    setShowShiftModal(true);
  };

  const handleSaveShift = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {
        ...shiftForm,
        break_duration: parseInt(shiftForm.break_duration, 10) || 0,
      };
      if (editingShift) {
        await shiftsAPI.update(editingShift.id, data);
        toast.success(t('shiftUpdated'));
      } else {
        await shiftsAPI.create(data);
        toast.success(t('shiftCreated'));
      }
      setShowShiftModal(false);
      fetchShifts();
    } catch (err) {
      const msg =
        err.response?.data?.name?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        t('errorSavingData');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteShift = async (shift) => {
    if (!window.confirm(t('confirmDelete'))) return;
    try {
      await shiftsAPI.update(shift.id, { is_active: false });
      toast.success(t('shiftDeleted'));
      fetchShifts();
    } catch {
      toast.error(t('errorSavingData'));
    }
  };

  // ── Assignment CRUD ─────────────────────────────────────────────────────
  const openCreateAssignment = () => {
    setEditingAssignment(null);
    setAssignmentForm({ ...emptyAssignmentForm });
    setShowAssignmentModal(true);
  };

  const openEditAssignment = (assignment) => {
    setEditingAssignment(assignment);
    setAssignmentForm({
      employee: assignment.employee || '',
      shift: assignment.shift || '',
      effective_date: assignment.effective_date || '',
      end_date: assignment.end_date || '',
      is_active: assignment.is_active !== false,
    });
    setShowAssignmentModal(true);
  };

  const handleSaveAssignment = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {
        ...assignmentForm,
        employee: parseInt(assignmentForm.employee, 10),
        shift: parseInt(assignmentForm.shift, 10),
        end_date: assignmentForm.end_date || null,
      };
      if (editingAssignment) {
        await employeeShiftsAPI.update(editingAssignment.id, data);
        toast.success(t('assignmentUpdated'));
      } else {
        await employeeShiftsAPI.create(data);
        toast.success(t('assignmentCreated'));
      }
      setShowAssignmentModal(false);
      fetchAssignments();
    } catch (err) {
      const msg =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.employee?.[0] ||
        err.response?.data?.shift?.[0] ||
        t('errorSavingData');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  // ── Display helpers ─────────────────────────────────────────────────────
  const activeShifts = shifts.filter((s) => s.is_active !== false);
  const getEmployeeName = (empId) => {
    const emp = employees.find((e) => e.id === empId);
    return emp ? emp.full_name : (locale === 'ar' ? 'غير معروف' : 'Unknown');
  };
  const getShiftName = (shiftId) => {
    const shift = shifts.find((s) => s.id === shiftId);
    return shift ? shift.name : (locale === 'ar' ? 'غير معروف' : 'Unknown');
  };

  // ── Tabs config ─────────────────────────────────────────────────────────
  const tabs = [
    { id: 'shifts', name: t('shifts'), icon: Clock },
    { id: 'assignments', name: t('employeeAssignments'), icon: Users },
  ];

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('shifts')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {activeTab === 'shifts'
              ? (locale === 'ar' ? 'إدارة الورديات وأنواعها' : 'Manage work shifts and schedules')
              : (locale === 'ar' ? 'توزيع الموظفين على الورديات' : 'Assign employees to shifts')}
          </p>
        </div>
        <div className="flex gap-2">
          {canManage && (
            <button
              onClick={activeTab === 'shifts' ? openCreateShift : openCreateAssignment}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm text-sm"
            >
              <Plus className="w-4 h-4" />
              {activeTab === 'shifts' ? t('addShift') : t('assignShift')}
            </button>
          )}
        </div>
      </div>

      {/* ── Tabs ────────────────────────────────────────────────────────── */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSearch('');
                setFilterStatus('');
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-riadah-500 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.name}
            </button>
          );
        })}
      </div>

      {/* ── Search & Filter ─────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder={t('search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
          >
            <option value="">{t('status')}</option>
            <option value="active">{t('active')}</option>
            <option value="inactive">{t('inactive')}</option>
          </select>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════
          SHIFTS TAB
         ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'shifts' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">
              {t('loading')}
            </div>
          ) : shifts.length === 0 ? (
            <div className="p-12 text-center">
              <Clock className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">{t('noShifts')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">{t('shiftName')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('startTime')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('endTime')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('breakDuration')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('applicableDays')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('nightShift')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                    {canManage && (
                      <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {shifts.map((shift) => (
                    <tr
                      key={shift.id}
                      className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100">
                          {shift.name}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300" dir="ltr">
                        <span className="inline-flex items-center gap-1">
                          <Sun className="w-3.5 h-3.5 text-amber-500" />
                          {shift.start_time}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300" dir="ltr">
                        <span className="inline-flex items-center gap-1">
                          <Moon className="w-3.5 h-3.5 text-indigo-400" />
                          {shift.end_time}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {shift.break_duration > 0
                          ? `${shift.break_duration} ${t('minutes')}`
                          : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {(shift.applicable_days || []).map((day) => (
                            <span
                              key={day}
                              className="inline-block px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-medium"
                            >
                              {getDayLabel(day)}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {shift.is_night ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
                            <Moon className="w-3 h-3" />
                            {locale === 'ar' ? 'ليلي' : 'Night'}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                            <Sun className="w-3 h-3" />
                            {locale === 'ar' ? 'صباحي' : 'Day'}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            shift.is_active !== false
                              ? STATUS_COLORS.active
                              : STATUS_COLORS.inactive
                          }`}
                        >
                          {shift.is_active !== false ? t('active') : t('inactive')}
                        </span>
                      </td>
                      {canManage && (
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <button
                              onClick={() => openEditShift(shift)}
                              className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors"
                              title={t('editShift')}
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {shift.is_active !== false && (
                              <button
                                onClick={() => handleDeleteShift(shift)}
                                className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                title={t('delete')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════
          ASSIGNMENTS TAB
         ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'assignments' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">
              {t('loading')}
            </div>
          ) : assignments.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">{t('noAssignments')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">{t('employee')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('shift')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('effectiveDate')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('endDate')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                    {canManage && (
                      <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {assignments.map((assignment) => (
                    <tr
                      key={assignment.id}
                      className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100">
                          {assignment.employee_name || getEmployeeName(assignment.employee)}
                        </p>
                        {assignment.employee_number && (
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            {assignment.employee_number}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 text-gray-700 dark:text-gray-300">
                          {assignment.shift_name
                            ? assignment.shift_name
                            : getShiftName(assignment.shift)}
                          {assignment.is_night_shift && (
                            <Moon className="w-3.5 h-3.5 text-indigo-400" />
                          )}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-gray-400" />
                          {assignment.effective_date || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {assignment.end_date || (
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {locale === 'ar' ? 'مستمر' : 'Ongoing'}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            assignment.is_active !== false
                              ? STATUS_COLORS.active
                              : STATUS_COLORS.inactive
                          }`}
                        >
                          {assignment.is_active !== false ? t('active') : t('inactive')}
                        </span>
                      </td>
                      {canManage && (
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <button
                              onClick={() => openEditAssignment(assignment)}
                              className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors"
                              title={t('editShift')}
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {assignment.is_active !== false && (
                              <button
                                onClick={async () => {
                                  if (!window.confirm(t('confirmDelete'))) return;
                                  try {
                                    await employeeShiftsAPI.update(assignment.id, {
                                      is_active: false,
                                    });
                                    toast.success(t('shiftDeleted'));
                                    fetchAssignments();
                                  } catch {
                                    toast.error(t('errorSavingData'));
                                  }
                                }}
                                className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                title={t('delete')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════
          SHIFT CREATE / EDIT MODAL
         ══════════════════════════════════════════════════════════════════ */}
      {showShiftModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingShift ? t('editShift') : t('addShift')}
              </h3>
              <button
                onClick={() => setShowShiftModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSaveShift} className="p-5 space-y-4">
              {/* Shift name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('shiftName')} *
                </label>
                <input
                  type="text"
                  value={shiftForm.name}
                  onChange={(e) =>
                    setShiftForm({ ...shiftForm, name: e.target.value })
                  }
                  required
                  placeholder={locale === 'ar' ? 'مثال: وردية الصباح' : 'e.g. Morning Shift'}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>

              {/* Times */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('startTime')} *
                  </label>
                  <input
                    type="time"
                    value={shiftForm.start_time}
                    onChange={(e) =>
                      setShiftForm({ ...shiftForm, start_time: e.target.value })
                    }
                    required
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('endTime')} *
                  </label>
                  <input
                    type="time"
                    value={shiftForm.end_time}
                    onChange={(e) =>
                      setShiftForm({ ...shiftForm, end_time: e.target.value })
                    }
                    required
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>

              {/* Break & Night */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('breakDuration')} ({t('minutes')})
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={shiftForm.break_duration}
                    onChange={(e) =>
                      setShiftForm({
                        ...shiftForm,
                        break_duration: parseInt(e.target.value, 10) || 0,
                      })
                    }
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
                <div className="flex items-center gap-3 pt-6">
                  <button
                    type="button"
                    onClick={() =>
                      setShiftForm({ ...shiftForm, is_night: !shiftForm.is_night })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      shiftForm.is_night
                        ? 'bg-indigo-600 dark:bg-indigo-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        shiftForm.is_night ? '-translate-x-6' : '-translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 inline-flex items-center gap-1.5">
                    <Moon className="w-4 h-4 text-indigo-500" />
                    {t('nightShift')}
                  </span>
                </div>
              </div>

              {/* Applicable days */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('applicableDays')}
                </label>
                <div className="flex flex-wrap gap-2">
                  {ALL_DAYS.map((day) => {
                    const isSelected = shiftForm.applicable_days.includes(day);
                    return (
                      <button
                        key={day}
                        type="button"
                        onClick={() => toggleDay(day)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
                          isSelected
                            ? 'bg-riadah-500 text-white border-riadah-500 shadow-sm'
                            : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-riadah-400 dark:hover:border-riadah-500 hover:text-riadah-600 dark:hover:text-riadah-400'
                        }`}
                      >
                        {t(DAY_KEYS[day])}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Status (only in edit) */}
              {editingShift && (
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setShiftForm({ ...shiftForm, is_active: !shiftForm.is_active })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      shiftForm.is_active
                        ? 'bg-green-600 dark:bg-green-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        shiftForm.is_active ? '-translate-x-6' : '-translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('status')}: {shiftForm.is_active ? t('active') : t('inactive')}
                  </span>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? t('saving') : editingShift ? t('save') : t('create')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowShiftModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════
          ASSIGNMENT CREATE / EDIT MODAL
         ══════════════════════════════════════════════════════════════════ */}
      {showAssignmentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingAssignment ? t('editShift') : t('assignShift')}
              </h3>
              <button
                onClick={() => setShowAssignmentModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSaveAssignment} className="p-5 space-y-4">
              {/* Employee select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('employee')} *
                </label>
                <select
                  value={assignmentForm.employee}
                  onChange={(e) =>
                    setAssignmentForm({ ...assignmentForm, employee: e.target.value })
                  }
                  required
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                >
                  <option value="">{t('selectEmployee')}</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name}
                      {emp.employee_number ? ` (${emp.employee_number})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Shift select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('shift')} *
                </label>
                <select
                  value={assignmentForm.shift}
                  onChange={(e) =>
                    setAssignmentForm({ ...assignmentForm, shift: e.target.value })
                  }
                  required
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                >
                  <option value="">{t('selectShift')}</option>
                  {activeShifts.map((shift) => (
                    <option key={shift.id} value={shift.id}>
                      {shift.name}
                      {shift.is_night
                        ? ` (${locale === 'ar' ? 'ليلي' : 'Night'})`
                        : ` (${locale === 'ar' ? 'صباحي' : 'Day'})`}
                      {' – '}
                      {shift.start_time} - {shift.end_time}
                    </option>
                  ))}
                </select>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('effectiveDate')} *
                  </label>
                  <input
                    type="date"
                    value={assignmentForm.effective_date}
                    onChange={(e) =>
                      setAssignmentForm({
                        ...assignmentForm,
                        effective_date: e.target.value,
                      })
                    }
                    required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('endDate')}
                  </label>
                  <input
                    type="date"
                    value={assignmentForm.end_date}
                    onChange={(e) =>
                      setAssignmentForm({
                        ...assignmentForm,
                        end_date: e.target.value,
                      })
                    }
                    min={assignmentForm.effective_date}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {locale === 'ar'
                      ? 'اتركه فارغاً للتكوين المستمر'
                      : 'Leave empty for ongoing assignment'}
                  </p>
                </div>
              </div>

              {/* Status (only in edit) */}
              {editingAssignment && (
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setAssignmentForm({
                        ...assignmentForm,
                        is_active: !assignmentForm.is_active,
                      })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      assignmentForm.is_active
                        ? 'bg-green-600 dark:bg-green-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        assignmentForm.is_active ? '-translate-x-6' : '-translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('status')}: {assignmentForm.is_active ? t('active') : t('inactive')}
                  </span>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? t('saving') : editingAssignment ? t('save') : t('create')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAssignmentModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
