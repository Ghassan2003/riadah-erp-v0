/**
 * Employees Management page - HR module.
 * List, create, edit, and manage employees with department filtering.
 * Supports soft-delete & restore, dark mode, and i18n (RTL Arabic/English).
 */

import { useState, useEffect } from 'react';
import { employeesAPI, departmentsAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import toast from 'react-hot-toast';
import {
  Search, Plus, X, Edit2, Eye, Users, Filter, Download, Paperclip,
  Trash2, RotateCcw, Save,
} from 'lucide-react';
import AttachmentManager from '../components/AttachmentManager';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  on_leave: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  suspended: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  terminated: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

const EMPTY_FORM = {
  first_name: '', last_name: '', email: '', phone: '', department: '',
  position: '', hire_date: '', salary: '', housing_allowance: '',
  transport_allowance: '', bank_name: '', bank_account: '',
  national_id: '', notes: '', status: 'active',
};

export default function EmployeesPage() {
  const { t, locale } = useI18n();
  const { isHR } = useAuth();
  const canManage = isHR;

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

  /* ── modal states ── */
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);

  /* ── confirm dialog ── */
  const [confirmAction, setConfirmAction] = useState(null); // { type: 'delete'|'restore', emp }

  const [form, setForm] = useState({ ...EMPTY_FORM });

  // ──────────────────────── Data Fetching ────────────────────────

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
    } catch { /* silent */ }
  };

  useEffect(() => { fetchEmployees(); }, [search, filterDept, filterStatus, page]);
  useEffect(() => { fetchDepartments(); }, []);

  // ──────────────────────── Actions ────────────────────────

  const openCreate = () => {
    setForm({ ...EMPTY_FORM });
    setShowCreateModal(true);
  };

  const openEdit = async (emp) => {
    try {
      const res = await employeesAPI.get(emp.id);
      const d = res.data;
      setForm({
        first_name: d.first_name || '',
        last_name: d.last_name || '',
        email: d.email || '',
        phone: d.phone || '',
        department: d.department || '',
        position: d.position || '',
        hire_date: d.hire_date || '',
        salary: d.salary ?? '',
        housing_allowance: d.housing_allowance ?? '',
        transport_allowance: d.transport_allowance ?? '',
        bank_name: d.bank_name || '',
        bank_account: d.bank_account || '',
        national_id: d.national_id || '',
        notes: d.notes || '',
        status: d.status || 'active',
      });
      setSelectedEmp(d);
      setShowEditModal(true);
    } catch {
      toast.error(t('errorLoadingEmployeeDetails'));
    }
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

  const handleCreate = async (e) => {
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
      setShowCreateModal(false);
      fetchEmployees();
    } catch (err) {
      const msg = err.response?.data?.email?.[0]
        || err.response?.data?.non_field_errors?.[0]
        || t('errorSavingData');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!selectedEmp) return;
    setSaving(true);
    try {
      const data = { ...form };
      data.salary = parseFloat(data.salary) || 0;
      data.housing_allowance = parseFloat(data.housing_allowance) || 0;
      data.transport_allowance = parseFloat(data.transport_allowance) || 0;
      data.department = data.department || null;
      await employeesAPI.update(selectedEmp.id, data);
      toast.success(t('employeeUpdated'));
      setShowEditModal(false);
      setSelectedEmp(null);
      fetchEmployees();
    } catch (err) {
      const msg = err.response?.data?.email?.[0]
        || err.response?.data?.non_field_errors?.[0]
        || t('errorSavingData');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmAction?.emp) return;
    try {
      await employeesAPI.delete(confirmAction.emp.id);
      toast.success(t('employeeDeleted'));
      fetchEmployees();
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setConfirmAction(null);
    }
  };

  const handleRestore = async () => {
    if (!confirmAction?.emp) return;
    try {
      await employeesAPI.restore(confirmAction.emp.id);
      toast.success(t('employeeRestored'));
      fetchEmployees();
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setConfirmAction(null);
    }
  };

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

  // ──────────────────────── Helpers ────────────────────────

  const numLocale = locale === 'ar' ? 'ar-SA' : 'en-US';
  const formatAmount = (val) => Number(val || 0).toLocaleString(numLocale, { minimumFractionDigits: 2 });

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const isSoftDeleted = (emp) => emp.is_deleted === true;

  // ──────────────────────── Shared Form JSX ────────────────────────

  const inputClass =
    'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none transition-colors';
  const selectClass =
    'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 transition-colors';
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  const renderFormFields = (includeStatus = false) => (
    <div className="space-y-4">
      {/* ── Basic Info ── */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
          {locale === 'ar' ? 'المعلومات الأساسية' : 'Basic Information'}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>{t('firstName')} *</label>
            <input type="text" value={form.first_name} onChange={(e) => updateField('first_name', e.target.value)} required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('lastName')} *</label>
            <input type="text" value={form.last_name} onChange={(e) => updateField('last_name', e.target.value)} required className={inputClass} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>{t('email')}</label>
          <input type="email" value={form.email} onChange={(e) => updateField('email', e.target.value)} dir="ltr" className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>{t('phone')}</label>
          <input type="text" value={form.phone} onChange={(e) => updateField('phone', e.target.value)} className={inputClass} />
        </div>
      </div>

      {/* ── Work Info ── */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
          {locale === 'ar' ? 'معلومات العمل' : 'Work Information'}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>{t('department')}</label>
            <select value={form.department} onChange={(e) => updateField('department', e.target.value)} className={selectClass}>
              <option value="">{t('selectDepartment')}</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>{t('position')}</label>
            <input type="text" value={form.position} onChange={(e) => updateField('position', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('hireDate')} *</label>
            <input type="date" value={form.hire_date} onChange={(e) => updateField('hire_date', e.target.value)} required className={inputClass} />
          </div>
        </div>
      </div>

      {includeStatus && (
        <div>
          <label className={labelClass}>{t('status')}</label>
          <select value={form.status} onChange={(e) => updateField('status', e.target.value)} className={selectClass}>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      )}

      {/* ── Salary & Allowances ── */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
          {locale === 'ar' ? 'الراتب والبدلات' : 'Salary & Allowances'}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>{t('basicSalary')} *</label>
            <input type="number" step="0.01" value={form.salary} onChange={(e) => updateField('salary', e.target.value)} required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('housingAllowance')}</label>
            <input type="number" step="0.01" value={form.housing_allowance} onChange={(e) => updateField('housing_allowance', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('transportAllowance')}</label>
            <input type="number" step="0.01" value={form.transport_allowance} onChange={(e) => updateField('transport_allowance', e.target.value)} className={inputClass} />
          </div>
        </div>
      </div>

      {/* ── Banking & ID ── */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
          {locale === 'ar' ? 'المصرفية والهوية' : 'Banking & ID'}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>{t('nationalId')}</label>
            <input type="text" value={form.national_id} onChange={(e) => updateField('national_id', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('bankName')}</label>
            <input type="text" value={form.bank_name} onChange={(e) => updateField('bank_name', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>{t('bankAccount')}</label>
            <input type="text" value={form.bank_account} onChange={(e) => updateField('bank_account', e.target.value)} dir="ltr" className={inputClass} />
          </div>
        </div>
      </div>

      {/* ── Notes ── */}
      <div>
        <label className={labelClass}>{t('notes')}</label>
        <textarea value={form.notes} onChange={(e) => updateField('notes', e.target.value)} rows={2}
          className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none transition-colors" />
      </div>
    </div>
  );

  const Spinner = () => (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
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
            {exporting ? (<><Spinner /> {t('exporting')}</>) : (<><Download className="h-4 w-4" /> {t('exportExcel')}</>)}
          </button>
          {canManage && (
            <button onClick={openCreate}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm font-medium">
              <Plus className="w-5 h-5" />
              {t('addNewEmployee')}
            </button>
          )}
        </div>
      </div>

      {/* ── Search & Filter ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input type="text" placeholder={t('searchEmployees')} value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none" />
          </div>
          <select value={filterDept} onChange={(e) => { setFilterDept(e.target.value); setPage(1); }}
            className={selectClass}>
            <option value="">{t('allDepartments')}</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className={selectClass}>
            <option value="">{t('allStatuses')}</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
            <Spinner /><span>{t('loading')}</span>
          </div>
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
                  <tr
                    key={emp.id}
                    className={`border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${
                      isSoftDeleted(emp) ? 'opacity-60' : ''
                    }`}
                  >
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
                      <div className="flex items-center gap-1">
                        {/* View */}
                        <button onClick={() => openDetail(emp)} title={t('view') || 'View'}
                          className="text-riadah-500 dark:text-riadah-400 hover:text-riadah-700 dark:hover:text-riadah-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>

                        {canManage && !isSoftDeleted(emp) && (
                          <>
                            {/* Edit */}
                            <button onClick={() => openEdit(emp)} title={t('editEmployee')}
                              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {/* Delete */}
                            <button onClick={() => setConfirmAction({ type: 'delete', emp })} title={t('delete')}
                              className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}

                        {canManage && isSoftDeleted(emp) && (
                          /* Restore */
                          <button onClick={() => setConfirmAction({ type: 'restore', emp })} title={t('restore')}
                            className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 p-1.5 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors">
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Pagination ── */}
      {totalCount > 20 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-colors">
            {t('previous')}
          </button>
          <span className="px-3 py-2 text-sm text-gray-600 dark:text-gray-300">{t('page')} {page}</span>
          <button onClick={() => setPage(page + 1)} disabled={employees.length < 20}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-colors">
            {t('next')}
          </button>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          MODALS
         ═══════════════════════════════════════════════════════════ */}

      {/* ── Create Modal ── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Plus className="w-5 h-5 text-riadah-500" />
                {t('addNewEmployee')}
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5">
              {renderFormFields(false)}
              <div className="flex gap-3 pt-4 mt-4 border-t dark:border-gray-700">
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium flex items-center justify-center gap-2">
                  {saving ? <><Spinner /> {t('saving')}</> : t('create')}
                </button>
                <button type="button" onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Edit Modal ── */}
      {showEditModal && selectedEmp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowEditModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-blue-500" />
                {t('editEmployee')}
                <span className="text-sm font-normal text-gray-400 dark:text-gray-500">— {selectedEmp.full_name}</span>
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleUpdate} className="p-5">
              {renderFormFields(true)}
              <div className="flex gap-3 pt-4 mt-4 border-t dark:border-gray-700">
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 font-medium flex items-center justify-center gap-2">
                  {saving ? <><Spinner /> {t('saving')}</> : <><Save className="w-4 h-4" /> {t('save')}</>}
                </button>
                <button type="button" onClick={() => setShowEditModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Detail Modal ── */}
      {showDetail && selectedEmp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowDetail(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Users className="w-5 h-5 text-riadah-500" />
                {selectedEmp.full_name}
              </h3>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-5">
              {/* Basic Info Grid */}
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('employeeNumber')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.employee_number}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('department')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.department_name || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('position')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.position || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('hireDate')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.hire_date}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('email')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.email || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('phone')}</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.phone || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t('status')}</span>
                  <p className="font-medium mt-0.5">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[selectedEmp.status]}`}>
                      {STATUS_LABELS[selectedEmp.status]}
                    </span>
                  </p>
                </div>
                {selectedEmp.national_id && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">{t('nationalId')}</span>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.national_id}</p>
                  </div>
                )}
              </div>

              {/* Salary Breakdown */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">{t('salaryAllowances')}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">{t('basicSalary')}</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.salary)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">{t('housingAllowance')}</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.housing_allowance)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">{t('transportAllowance')}</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{formatAmount(selectedEmp.transport_allowance)}</span>
                  </div>
                  <div className="flex justify-between border-t dark:border-gray-600 pt-2 mt-2 font-bold text-base">
                    <span className="text-gray-900 dark:text-gray-100">{t('total')}</span>
                    <span className="text-riadah-600 dark:text-riadah-400">{formatAmount(selectedEmp.total_salary)}</span>
                  </div>
                </div>
              </div>

              {/* Bank Info */}
              {(selectedEmp.bank_name || selectedEmp.bank_account) && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    {locale === 'ar' ? 'معلومات مصرفية' : 'Bank Information'}
                  </h4>
                  <div className="space-y-2 text-sm">
                    {selectedEmp.bank_name && (
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">{t('bankName')}</span>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{selectedEmp.bank_name}</span>
                      </div>
                    )}
                    {selectedEmp.bank_account && (
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">{t('bankAccount')}</span>
                        <span className="font-medium text-gray-900 dark:text-gray-100 font-mono" dir="ltr">{selectedEmp.bank_account}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Notes */}
              {selectedEmp.notes && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('notes')}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{selectedEmp.notes}</p>
                </div>
              )}

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

              {/* Action buttons in detail view */}
              {canManage && (
                <div className="flex gap-2 pt-2 border-t dark:border-gray-600">
                  <button onClick={() => { setShowDetail(false); openEdit(selectedEmp); }}
                    className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2 text-sm">
                    <Edit2 className="w-4 h-4" />
                    {t('editEmployee')}
                  </button>
                  {!isSoftDeleted(selectedEmp) ? (
                    <button onClick={() => { setShowDetail(false); setConfirmAction({ type: 'delete', emp: selectedEmp }); }}
                      className="flex items-center justify-center gap-2 px-4 py-2.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors font-medium text-sm">
                      <Trash2 className="w-4 h-4" />
                      {t('delete')}
                    </button>
                  ) : (
                    <button onClick={() => { setShowDetail(false); setConfirmAction({ type: 'restore', emp: selectedEmp }); }}
                      className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors font-medium text-sm">
                      <RotateCcw className="w-4 h-4" />
                      {t('restore')}
                    </button>
                  )}
                </div>
              )}

              <button onClick={() => setShowDetail(false)}
                className="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Confirm Dialog ── */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4" onClick={() => setConfirmAction(null)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 text-center space-y-4">
              {/* Icon */}
              <div className={`mx-auto w-14 h-14 rounded-full flex items-center justify-center ${
                confirmAction.type === 'delete'
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : 'bg-emerald-100 dark:bg-emerald-900/30'
              }`}>
                {confirmAction.type === 'delete'
                  ? <Trash2 className="w-7 h-7 text-red-600 dark:text-red-400" />
                  : <RotateCcw className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
                }
              </div>

              {/* Message */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {confirmAction.type === 'delete' ? t('confirmDelete') : t('confirmRestore')}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {confirmAction.emp.full_name}
                </p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={confirmAction.type === 'delete' ? handleDelete : handleRestore}
                  className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors text-white ${
                    confirmAction.type === 'delete'
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-emerald-600 hover:bg-emerald-700'
                  }`}
                >
                  {confirmAction.type === 'delete' ? t('delete') : t('restore')}
                </button>
                <button onClick={() => setConfirmAction(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">
                  {t('cancel')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
