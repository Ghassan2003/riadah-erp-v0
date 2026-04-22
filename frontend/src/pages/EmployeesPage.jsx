/**
 * Employees Management page - HR module.
 * List, create, and manage employees with department filtering.
 * Supports dark mode and i18n.
 */

import { useState, useEffect } from 'react';
import { employeesAPI, departmentsAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Edit2, Eye, Users, Filter, Download, Paperclip,
} from 'lucide-react';
import AttachmentManager from '../components/AttachmentManager';
import { useI18n } from '../i18n/I18nContext';

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  on_leave: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  suspended: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  terminated: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

export default function EmployeesPage() {
  const { t, locale } = useI18n();

  const STATUS_LABELS = {
    active: t('active'),
    on_leave: t('onLeave'),
    suspended: t('suspended'),
    terminated: t('terminated'),
  };

  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', phone: '', gender: 'male',
    department: '', position: '', hire_date: '', salary: '',
    housing_allowance: '', transport_allowance: '',
    bank_name: '', bank_account: '', national_id: '', notes: '',
  });

  const userRole = JSON.parse(localStorage.getItem('user') || '{}')?.role;
  const canManage = userRole === 'admin';

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (filterDept) params.department = filterDept;
      if (filterStatus) params.status = filterStatus;
      const res = await employeesAPI.list(params);
      setEmployees(res.data.results || res.data);
      setTotalCount(res.data.count || employees.length);
    } catch {
      toast.error(t('errorLoadingEmployees'));
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await departmentsAPI.list();
      setDepartments(res.data.results || res.data);
    } catch {}
  };

  useEffect(() => { fetchEmployees(); }, [search, filterDept, filterStatus, page]);
  useEffect(() => { fetchDepartments(); }, []);

  const openCreate = () => {
    setForm({
      first_name: '', last_name: '', email: '', phone: '', gender: 'male',
      department: '', position: '', hire_date: '', salary: '',
      housing_allowance: '', transport_allowance: '',
      bank_name: '', bank_account: '', national_id: '', notes: '',
    });
    setShowModal(true);
  };

  const openDetail = async (emp) => {
    try {
      const res = await employeesAPI.get(emp.id);
      setSelectedEmp(res.data);
      setShowDetail(true);
    } catch {
      toast.error(t('errorLoadingEmployeeDetails'));
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = { ...form };
      data.salary = parseFloat(data.salary) || 0;
      data.housing_allowance = parseFloat(data.housing_allowance) || 0;
      data.transport_allowance = parseFloat(data.transport_allowance) || 0;
      data.department = data.department || null;
      await employeesAPI.create(data);
      toast.success(t('employeeCreated'));
      setShowModal(false);
      fetchEmployees();
    } catch (err) {
      const msg = err.response?.data?.email?.[0] || err.response?.data?.non_field_errors?.[0] || t('errorSavingData');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const numLocale = locale === 'ar' ? 'ar-SA' : 'en-US';
  const formatAmount = (val) => Number(val || 0).toLocaleString(numLocale, { minimumFractionDigits: 2 });

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.employees();
      downloadBlob(new Blob([response.data]), 'employees.xlsx');
      toast.success(t('dataExported'));
    } catch {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageEmployees')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageEmployeesDesc')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('exporting')}
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                {t('exportExcel')}
              </>
            )}
          </button>
          {canManage && (
            <button onClick={openCreate}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm">
              <Plus className="w-5 h-5" />
              {t('addNewEmployee')}
            </button>
          )}
        </div>
      </div>

      {/* Search & Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input type="text" placeholder={t('searchEmployees')} value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
          </div>
          <select value={filterDept} onChange={(e) => { setFilterDept(e.target.value); setPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
            <option value="">{t('allDepartments')}</option>
            {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
            <option value="">{t('allStatuses')}</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 dark:text-gray-500">{t('loading')}</div>
        ) : employees.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">{t('noEmployees')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">{t('employeeNumber')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('name')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('department')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('position')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('totalSalary')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('hireDate')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp) => (
                  <tr key={emp.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-500 dark:text-gray-400">{emp.employee_number}</td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{emp.full_name}</p>
                      {emp.email && <p className="text-xs text-gray-400 dark:text-gray-500">{emp.email}</p>}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{emp.department_name || '-'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{emp.position || '-'}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{formatAmount(emp.total_salary)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[emp.status] || ''}`}>
                        {STATUS_LABELS[emp.status] || emp.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{emp.hire_date}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => openDetail(emp)}
                        className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
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

      {/* Pagination */}
      {totalCount > 20 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300">{t('previous')}</button>
          <span className="px-3 py-2 text-sm text-gray-600 dark:text-gray-300">{t('page')} {page}</span>
          <button onClick={() => setPage(page + 1)} disabled={employees.length < 20}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300">{t('next')}</button>
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('addNewEmployee')}</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('firstName')} *</label>
                  <input type="text" value={form.first_name} onChange={(e) => setForm({...form, first_name: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('lastName')} *</label>
                  <input type="text" value={form.last_name} onChange={(e) => setForm({...form, last_name: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('email')}</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('phone')}</label>
                  <input type="text" value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('department')}</label>
                  <select value={form.department} onChange={(e) => setForm({...form, department: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                    <option value="">{t('selectDepartment')}</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('position')}</label>
                  <input type="text" value={form.position} onChange={(e) => setForm({...form, position: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('hireDate')} *</label>
                  <input type="date" value={form.hire_date} onChange={(e) => setForm({...form, hire_date: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('basicSalary')} *</label>
                  <input type="number" step="0.01" value={form.salary} onChange={(e) => setForm({...form, salary: e.target.value})} required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('housingAllowance')}</label>
                  <input type="number" step="0.01" value={form.housing_allowance} onChange={(e) => setForm({...form, housing_allowance: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('transportAllowance')}</label>
                  <input type="number" step="0.01" value={form.transport_allowance} onChange={(e) => setForm({...form, transport_allowance: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('nationalId')}</label>
                  <input type="text" value={form.national_id} onChange={(e) => setForm({...form, national_id: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('bankName')}</label>
                  <input type="text" value={form.bank_name} onChange={(e) => setForm({...form, bank_name: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('bankAccount')}</label>
                  <input type="text" value={form.bank_account} onChange={(e) => setForm({...form, bank_account: e.target.value})} dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('notes')}</label>
                <textarea value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium">
                  {saving ? t('saving') : t('create')}
                </button>
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">{t('cancel')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && selectedEmp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{selectedEmp.full_name}</h3>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500 dark:text-gray-400">{t('employeeNumber')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.employee_number}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('department')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.department_name || '-'}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('position')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.position || '-'}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('hireDate')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.hire_date}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('email')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.email || '-'}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('phone')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.phone || '-'}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('status')}:</span>
                  <p className="font-medium"><span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_COLORS[selectedEmp.status]}`}>{STATUS_LABELS[selectedEmp.status]}</span></p>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('salaryAllowances')}</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('basicSalary')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.salary)}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('housingAllowance')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.housing_allowance)}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">{t('transportAllowance')}:</span><span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.transport_allowance)}</span></div>
                  <div className="flex justify-between border-t dark:border-gray-600 pt-1 font-bold"><span className="text-gray-900 dark:text-gray-100">{t('total')}:</span><span className="text-accent-500 dark:text-accent-400">{formatAmount(selectedEmp.total_salary)}</span></div>
                </div>
              </div>
              {/* Attachments */}
              <div className="border-t dark:border-gray-600 pt-4">
                <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <Paperclip className="w-4 h-4" />
                  {t('attachments')}
                </h4>
                <AttachmentManager
                  contentType="hr.employee"
                  objectId={selectedEmp.id}
                  category="employee"
                />
              </div>
              <button onClick={() => setShowDetail(false)}
                className="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">{t('close')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
