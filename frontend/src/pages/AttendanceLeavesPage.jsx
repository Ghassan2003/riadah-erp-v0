/**
 * Attendance & Leave Requests page - HR module.
 * Shows attendance records and leave request management.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { attendanceAPI, leavesAPI, employeesAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Check, Ban, Clock, CalendarDays,
  Eye, Filter,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const ATTENDANCE_COLORS = {
  present: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  absent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  late: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  half_day: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  holiday: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
};

const APPROVAL_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

export default function AttendanceLeavesPage() {
  const { t, locale } = useI18n();

  const ATTENDANCE_STATUS = {
    present: t('present'),
    absent: t('absent'),
    late: t('late'),
    half_day: t('halfDay'),
    holiday: t('officialHoliday'),
  };

  const LEAVE_TYPE = {
    annual: t('annualLeave'),
    sick: t('sickLeave'),
    emergency: t('emergencyLeave'),
    maternity: t('maternityLeave'),
    hajj: t('hajjLeave'),
    unpaid: t('unpaidLeave'),
    other: t('otherLeave'),
  };

  const APPROVAL_STATUS = {
    pending: t('pending'),
    approved: t('approved'),
    rejected: t('rejected'),
    cancelled: t('cancelled'),
  };

  const [activeTab, setActiveTab] = useState('attendance');
  const [attendance, setAttendance] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dateFilter, setDateFilter] = useState('');

  const userRole = JSON.parse(localStorage.getItem('user') || '{}')?.role;
  const isAdmin = userRole === 'admin';

  // Attendance form
  const [attForm, setAttForm] = useState({ employee: '', date: '', check_in: '', check_out: '', status: 'present', notes: '' });
  // Leave form
  const [leaveForm, setLeaveForm] = useState({ employee: '', leave_type: 'annual', start_date: '', end_date: '', reason: '' });

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const params = {};
      if (dateFilter) params.date_from = dateFilter;
      const res = await attendanceAPI.list(params);
      setAttendance(res.data.results || res.data);
    } catch { toast.error(t('errorLoadingAttendance')); }
    finally { setLoading(false); }
  };

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const res = await leavesAPI.list({});
      setLeaves(res.data.results || res.data);
    } catch { toast.error(t('errorLoadingLeaves')); }
    finally { setLoading(false); }
  };

  const fetchEmployees = async () => {
    try {
      const res = await employeesAPI.list({ page_size: 200 });
      setEmployees(res.data.results || res.data);
    } catch {}
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (activeTab === 'attendance') fetchAttendance();
    else fetchLeaves();
  }, [activeTab, dateFilter]);

  const handleAttendanceSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = { ...attForm, employee: parseInt(attForm.employee) };
      await attendanceAPI.create(data);
      toast.success(t('attendanceSaved'));
      setShowAttendanceModal(false);
      setAttForm({ employee: '', date: '', check_in: '', check_out: '', status: 'present', notes: '' });
      fetchAttendance();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || t('errorSavingAttendance'));
    } finally { setSaving(false); }
  };

  const handleLeaveSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = { ...leaveForm, employee: parseInt(leaveForm.employee) };
      await leavesAPI.create(data);
      toast.success(t('leaveRequestCreated'));
      setShowLeaveModal(false);
      setLeaveForm({ employee: '', leave_type: 'annual', start_date: '', end_date: '', reason: '' });
      fetchLeaves();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || t('errorCreatingRequest'));
    } finally { setSaving(false); }
  };

  const handleApprove = async (id, action) => {
    try {
      await leavesAPI.approve(id, { action });
      toast.success(action === 'approve' ? t('leaveApproved') : t('leaveRejected'));
      fetchLeaves();
    } catch (err) {
      toast.error(err.response?.data?.error || t('error'));
    }
  };

  const tabs = [
    { id: 'attendance', name: t('attendanceRecords'), icon: Clock },
    { id: 'leaves', name: t('leaveRequests'), icon: CalendarDays },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('attendanceAndLeaves')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('attendanceAndLeavesDesc')}</p>
        </div>
        <div className="flex gap-2">
          {isAdmin && (
            <>
              <button onClick={() => setShowAttendanceModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm text-sm">
                <Plus className="w-4 h-4" /> {t('registerAttendance')}
              </button>
              <button onClick={() => setShowLeaveModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm text-sm">
                <Plus className="w-4 h-4" /> {t('submitLeave')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-riadah-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>
              <Icon className="w-4 h-4" /> {tab.name}
            </button>
          );
        })}
      </div>

      {/* Date filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          <label className="text-sm text-gray-600 dark:text-gray-300">{t('fromDate')}:</label>
          <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)}
            className="px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
          {dateFilter && (
            <button onClick={() => setDateFilter('')} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-sm">{t('clear')}</button>
          )}
        </div>
      </div>

      {/* Attendance Tab */}
      {activeTab === 'attendance' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">{t('loading')}</div>
          ) : attendance.length === 0 ? (
            <div className="p-12 text-center"><Clock className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500 dark:text-gray-400">{t('noAttendanceRecords')}</p></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">{t('employeeName')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('department')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('date')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('checkIn')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('checkOut')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('workingHours')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance.map((rec) => (
                    <tr key={rec.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3"><p className="font-medium text-gray-900 dark:text-gray-100">{rec.employee_name}</p><p className="text-xs text-gray-400 dark:text-gray-500">{rec.employee_number}</p></td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{rec.department_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{rec.date}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{rec.check_in || '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{rec.check_out || '-'}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{rec.hours_worked > 0 ? `${rec.hours_worked} ${t('hour')}` : '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ATTENDANCE_COLORS[rec.status] || ''}`}>
                          {ATTENDANCE_STATUS[rec.status] || rec.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Leaves Tab */}
      {activeTab === 'leaves' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">{t('loading')}</div>
          ) : leaves.length === 0 ? (
            <div className="p-12 text-center"><CalendarDays className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" /><p className="text-gray-500 dark:text-gray-400">{t('noLeaveRequests')}</p></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">{t('employeeName')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('leaveType')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('leaveFrom')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('leaveTo')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('days')}</th>
                    <th className="px-4 py-3 text-right font-medium">{t('leaveStatus')}</th>
                    {isAdmin && <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>}
                  </tr>
                </thead>
                <tbody>
                  {leaves.map((leave) => (
                    <tr key={leave.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3"><p className="font-medium text-gray-900 dark:text-gray-100">{leave.employee_name}</p><p className="text-xs text-gray-400 dark:text-gray-500">{leave.department_name || ''}</p></td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{LEAVE_TYPE[leave.leave_type] || leave.leave_type}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{leave.start_date}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{leave.end_date}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{leave.days} {t('day')}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${APPROVAL_COLORS[leave.approval_status] || ''}`}>
                          {APPROVAL_STATUS[leave.approval_status] || leave.approval_status}
                        </span>
                      </td>
                      {isAdmin && leave.approval_status === 'pending' && (
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <button onClick={() => handleApprove(leave.id, 'approve')}
                              className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20"><Check className="w-4 h-4" /></button>
                            <button onClick={() => handleApprove(leave.id, 'reject')}
                              className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20"><Ban className="w-4 h-4" /></button>
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

      {/* Attendance Modal */}
      {showAttendanceModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('registerAttendance')}</h3>
              <button onClick={() => setShowAttendanceModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleAttendanceSave} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('employeeName')} *</label>
                <select value={attForm.employee} onChange={(e) => setAttForm({...attForm, employee: e.target.value})} required
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                  <option value="">{t('selectEmployee')}</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('date')} *</label>
                  <input type="date" value={attForm.date} onChange={(e) => setAttForm({...attForm, date: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('status')}</label>
                  <select value={attForm.status} onChange={(e) => setAttForm({...attForm, status: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                    {Object.entries(ATTENDANCE_STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('checkInTime')}</label>
                  <input type="time" value={attForm.check_in} onChange={(e) => setAttForm({...attForm, check_in: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('checkOutTime')}</label>
                  <input type="time" value={attForm.check_out} onChange={(e) => setAttForm({...attForm, check_out: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('notes')}</label>
                <textarea value={attForm.notes} onChange={(e) => setAttForm({...attForm, notes: e.target.value})} rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none" />
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={saving} className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 disabled:opacity-50 font-medium">
                  {saving ? t('saving') : t('save')}
                </button>
                <button type="button" onClick={() => setShowAttendanceModal(false)} className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium">{t('cancel')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Leave Modal */}
      {showLeaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('newLeaveRequest')}</h3>
              <button onClick={() => setShowLeaveModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleLeaveSave} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('employeeName')} *</label>
                <select value={leaveForm.employee} onChange={(e) => setLeaveForm({...leaveForm, employee: e.target.value})} required
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                  <option value="">{t('selectEmployee')}</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('leaveType')} *</label>
                <select value={leaveForm.leave_type} onChange={(e) => setLeaveForm({...leaveForm, leave_type: e.target.value})}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                  {Object.entries(LEAVE_TYPE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('leaveFrom')} *</label>
                  <input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({...leaveForm, start_date: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('leaveTo')} *</label>
                  <input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({...leaveForm, end_date: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('leaveReason')}</label>
                <textarea value={leaveForm.reason} onChange={(e) => setLeaveForm({...leaveForm, reason: e.target.value})} rows={3}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none" />
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={saving} className="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium">
                  {saving ? t('saving') : t('submitRequest')}
                </button>
                <button type="button" onClick={() => setShowLeaveModal(false)} className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium">{t('cancel')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
