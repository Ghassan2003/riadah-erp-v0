/**
 * Departments Management page - HR module.
 * List, create, edit, delete/restore departments with tree view.
 * Supports RTL, dark mode, and i18n.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { departmentsAPI, employeesAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Search, Plus, X, Edit2, Trash2, RotateCcw,
  Building2, Users, TreePine, List, ChevronRight, ChevronDown,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Tree Node helper – recursive render                                */
/* ------------------------------------------------------------------ */
function TreeNode({
  node,
  level = 0,
  expandedIds,
  toggleExpand,
  onEdit,
  onDelete,
  onRestore,
  canManage,
  t,
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedIds.has(node.id);
  const indent = level * 24;

  return (
    <div>
      <div
        className="flex items-center gap-3 px-4 py-3 border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
        style={{ paddingRight: 16 + indent }}
      >
        {/* Expand / collapse toggle */}
        <button
          onClick={() => hasChildren && toggleExpand(node.id)}
          className={`w-5 h-5 flex items-center justify-center rounded ${
            hasChildren
              ? 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
              : 'invisible'
          }`}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>

        {/* Department name */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
            {node.name}
            {node.name_en && (
              <span className="text-xs text-gray-400 dark:text-gray-500 mr-2 font-normal">
                {node.name_en}
              </span>
            )}
          </p>
          {node.description && (
            <p className="text-xs text-gray-400 dark:text-gray-500 truncate mt-0.5">
              {node.description}
            </p>
          )}
        </div>

        {/* Manager */}
        <div className="hidden md:block w-36 text-sm text-gray-600 dark:text-gray-300 truncate">
          {node.manager_name || '—'}
        </div>

        {/* Employees count */}
        <div className="hidden sm:flex items-center gap-1.5 w-20 justify-center">
          <Users className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-300">
            {node.employees_count ?? 0}
          </span>
        </div>

        {/* Status */}
        <span
          className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
            node.is_active
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
          }`}
        >
          {node.is_active ? t('active') : t('inactive')}
        </span>

        {/* Actions */}
        {canManage && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => onEdit(node)}
              title={t('editDepartment')}
              className="p-1.5 rounded text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              <Edit2 className="w-4 h-4" />
            </button>

            {node.is_active ? (
              <button
                onClick={() => onDelete(node)}
                title={t('delete')}
                className="p-1.5 rounded text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => onRestore(node)}
                title={t('restore')}
                className="p-1.5 rounded text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              onEdit={onEdit}
              onDelete={onDelete}
              onRestore={onRestore}
              canManage={canManage}
              t={t}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */
export default function DepartmentsPage() {
  const { t, locale } = useI18n();
  const { isHR } = useAuth();
  const canManage = isHR;

  /* ---- State ---- */
  const [departments, setDepartments] = useState([]);
  const [departmentTree, setDepartmentTree] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'tree'
  const [expandedIds, setExpandedIds] = useState(new Set());

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [form, setForm] = useState({
    name: '',
    name_en: '',
    parent: '',
    manager: '',
    description: '',
  });

  /* ---- Fetch helpers ---- */
  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.is_active = statusFilter;
      const res = await departmentsAPI.list(params);
      setDepartments(res.data.results || res.data);
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, t]);

  const fetchDepartmentTree = useCallback(async () => {
    try {
      const res = await departmentsAPI.getDepartmentTree();
      setDepartmentTree(res.data || []);
    } catch {
      /* tree is a nice-to-have; silently ignore */
    }
  }, []);

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await employeesAPI.list({ page_size: 500 });
      const list = res.data.results || res.data || [];
      setEmployees(list);
    } catch {
      /* non-critical */
    }
  }, []);

  /* ---- Effects ---- */
  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  useEffect(() => {
    if (viewMode === 'tree') fetchDepartmentTree();
  }, [viewMode, fetchDepartmentTree]);

  /* ---- Computed: parent options (exclude self & descendants when editing) ---- */
  const parentOptions = useMemo(() => {
    if (!editingDept) return departments.filter((d) => d.is_active !== false);
    const descendantIds = new Set();
    const collectDescendants = (id) => {
      departments.forEach((d) => {
        if (d.parent === id) {
          descendantIds.add(d.id);
          collectDescendants(d.id);
        }
      });
    };
    collectDescendants(editingDept.id);
    descendantIds.add(editingDept.id);
    return departments.filter((d) => !descendantIds.has(d.id));
  }, [departments, editingDept]);

  /* ---- Computed: filtered list for table view ---- */
  const filteredDepartments = useMemo(() => {
    return departments;
    // Backend already handles search + filter; we show all results
  }, [departments]);

  /* ---- Total employees count ---- */
  const totalEmployees = useMemo(() => {
    return departments.reduce((sum, d) => sum + (d.employees_count || 0), 0);
  }, [departments]);

  /* ---- Modal helpers ---- */
  const openCreate = () => {
    setEditingDept(null);
    setForm({ name: '', name_en: '', parent: '', manager: '', description: '' });
    setShowModal(true);
  };

  const openEdit = (dept) => {
    setEditingDept(dept);
    setForm({
      name: dept.name || '',
      name_en: dept.name_en || '',
      parent: dept.parent || '',
      manager: dept.manager || '',
      description: dept.description || '',
    });
    setShowModal(true);
  };

  /* ---- CRUD handlers ---- */
  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        name_en: form.name_en || undefined,
        parent: form.parent || null,
        manager: form.manager || null,
        description: form.description || undefined,
      };

      if (editingDept) {
        await departmentsAPI.update(editingDept.id, payload);
        toast.success(t('departmentUpdated'));
      } else {
        await departmentsAPI.create(payload);
        toast.success(t('departmentCreated'));
      }
      setShowModal(false);
      fetchDepartments();
      if (viewMode === 'tree') fetchDepartmentTree();
    } catch (err) {
      const firstError =
        err.response?.data?.name?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        t('errorSavingData');
      toast.error(Array.isArray(firstError) ? firstError[0] : firstError);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (dept) => {
    if (!window.confirm(t('confirmDelete'))) return;
    try {
      await departmentsAPI.delete(dept.id);
      toast.success(t('departmentDeleted'));
      fetchDepartments();
      if (viewMode === 'tree') fetchDepartmentTree();
    } catch {
      toast.error(t('errorSavingData'));
    }
  };

  const handleRestore = async (dept) => {
    try {
      await departmentsAPI.restore(dept.id);
      toast.success(t('departmentRestored'));
      fetchDepartments();
      if (viewMode === 'tree') fetchDepartmentTree();
    } catch {
      toast.error(t('errorSavingData'));
    }
  };

  /* ---- Tree expand/collapse ---- */
  const toggleExpand = useCallback((id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const expandAll = useCallback(() => {
    const ids = new Set();
    const walk = (nodes) => {
      nodes.forEach((n) => {
        if (n.children && n.children.length) {
          ids.add(n.id);
          walk(n.children);
        }
      });
    };
    walk(departmentTree);
    setExpandedIds(ids);
  }, [departmentTree]);

  const collapseAll = useCallback(() => {
    setExpandedIds(new Set());
  }, []);

  /* ---- Find department name by id ---- */
  const getDeptName = (id) => {
    if (!id) return null;
    const dept = departments.find((d) => d.id === id);
    return dept ? dept.name : null;
  };

  const getEmployeeName = (id) => {
    if (!id) return null;
    const emp = employees.find((e) => e.id === id);
    return emp ? emp.full_name || `${emp.first_name} ${emp.last_name}` : null;
  };

  /* ================================================================ */
  /*  RENDER                                                          */
  /* ================================================================ */
  return (
    <div className="space-y-6">
      {/* ---------- Header ---------- */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('departments')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <Building2 className="w-4 h-4" />
              {departments.length}
            </span>
            <span className="text-gray-300 dark:text-gray-600">|</span>
            <span className="flex items-center gap-1.5">
              <Users className="w-4 h-4" />
              {totalEmployees} {t('totalEmployees')}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          {canManage && (
            <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('list')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                <List className="w-4 h-4" />
                {t('listView')}
              </button>
              <button
                onClick={() => setViewMode('tree')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'tree'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                <TreePine className="w-4 h-4" />
                {t('orgChart')}
              </button>
            </div>
          )}

          {canManage && (
            <button
              onClick={openCreate}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm font-medium"
            >
              <Plus className="w-5 h-5" />
              {t('addDepartment')}
            </button>
          )}
        </div>
      </div>

      {/* ---------- Search & Filter ---------- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
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

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
          >
            <option value="">{t('allStatuses')}</option>
            <option value="true">{t('active')}</option>
            <option value="false">{t('inactive')}</option>
          </select>
        </div>
      </div>

      {/* ---------- Content Area ---------- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 dark:text-gray-500">
            <div className="flex flex-col items-center gap-3">
              <svg
                className="animate-spin h-8 w-8 text-riadah-500"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              {t('loading')}
            </div>
          </div>
        ) : departments.length === 0 ? (
          <div className="p-12 text-center">
            <Building2 className="w-16 h-16 text-gray-200 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              {t('noDepartments')}
            </p>
          </div>
        ) : viewMode === 'list' ? (
          /* ============ LIST (TABLE) VIEW ============ */
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">
                    {t('departmentName')}
                  </th>
                  <th className="px-4 py-3 text-right font-medium hidden md:table-cell">
                    {t('parentDepartment')}
                  </th>
                  <th className="px-4 py-3 text-right font-medium hidden lg:table-cell">
                    {t('manager')}
                  </th>
                  <th className="px-4 py-3 text-center font-medium hidden sm:table-cell">
                    {t('employees')}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t('status')}
                  </th>
                  {canManage && (
                    <th className="px-4 py-3 text-right font-medium">
                      {t('actions')}
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredDepartments.map((dept) => (
                  <tr
                    key={dept.id}
                    className={`border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${
                      !dept.is_active ? 'opacity-60' : ''
                    }`}
                  >
                    {/* Name */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-riadah-50 dark:bg-riadah-900/20 flex items-center justify-center flex-shrink-0">
                          <Building2 className="w-4 h-4 text-riadah-500" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                            {dept.name}
                          </p>
                          {dept.name_en && (
                            <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                              {dept.name_en}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Parent */}
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300 hidden md:table-cell">
                      {dept.parent_name || getDeptName(dept.parent) || (
                        <span className="text-gray-300 dark:text-gray-600">
                          {t('noParent')}
                        </span>
                      )}
                    </td>

                    {/* Manager */}
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300 hidden lg:table-cell">
                      {dept.manager_name || getEmployeeName(dept.manager) || '—'}
                    </td>

                    {/* Employees count */}
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <div className="flex items-center justify-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                        <span className="text-gray-700 dark:text-gray-300 font-medium">
                          {dept.employees_count ?? 0}
                        </span>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          dept.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {dept.is_active ? t('active') : t('inactive')}
                      </span>
                    </td>

                    {/* Actions */}
                    {canManage && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openEdit(dept)}
                            title={t('editDepartment')}
                            className="p-1.5 rounded text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>

                          {dept.is_active ? (
                            <button
                              onClick={() => handleDelete(dept)}
                              title={t('delete')}
                              className="p-1.5 rounded text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleRestore(dept)}
                              title={t('restore')}
                              className="p-1.5 rounded text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                            >
                              <RotateCcw className="w-4 h-4" />
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
        ) : (
          /* ============ TREE VIEW ============ */
          <div>
            {/* Tree toolbar */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/70">
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
                <span className="font-medium flex items-center gap-1.5">
                  <TreePine className="w-4 h-4" />
                  {t('orgChart')}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={expandAll}
                  className="px-2.5 py-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                >
                  {locale === 'ar' ? 'توسيع الكل' : 'Expand All'}
                </button>
                <span className="text-gray-300 dark:text-gray-600 mx-0.5">|</span>
                <button
                  onClick={collapseAll}
                  className="px-2.5 py-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                >
                  {locale === 'ar' ? 'طي الكل' : 'Collapse All'}
                </button>
              </div>
            </div>

            {/* Tree header row */}
            <div
              className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
            >
              <span className="w-5" /> {/* spacer for toggle */}
              <span className="flex-1">{t('departmentName')}</span>
              <span className="hidden md:block w-36">{t('manager')}</span>
              <span className="hidden sm:flex items-center w-20 justify-center gap-1.5">
                <Users className="w-3 h-3" />
                {t('employees')}
              </span>
              <span>{t('status')}</span>
              {canManage && <span className="w-20 text-center">{t('actions')}</span>}
            </div>

            {/* Tree nodes */}
            {departmentTree.length > 0 ? (
              <div>
                {departmentTree.map((node) => (
                  <TreeNode
                    key={node.id}
                    node={node}
                    expandedIds={expandedIds}
                    toggleExpand={toggleExpand}
                    onEdit={openEdit}
                    onDelete={handleDelete}
                    onRestore={handleRestore}
                    canManage={canManage}
                    t={t}
                  />
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-400 dark:text-gray-500 text-sm">
                {t('noDepartments')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ================================================================ */}
      {/*  CREATE / EDIT MODAL                                              */}
      {/* ================================================================ */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingDept ? t('editDepartment') : t('addDepartment')}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSave} className="p-5 space-y-4">
              {/* Arabic name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('departmentName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  autoFocus
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>

              {/* English name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('departmentNameEn')}
                </label>
                <input
                  type="text"
                  value={form.name_en}
                  onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                  dir="ltr"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-left"
                />
              </div>

              {/* Parent & Manager */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Parent department */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('parentDepartment')}
                  </label>
                  <select
                    value={form.parent}
                    onChange={(e) => setForm({ ...form, parent: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                  >
                    <option value="">{t('noParent')}</option>
                    {parentOptions.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Manager */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('manager')}
                  </label>
                  <select
                    value={form.manager}
                    onChange={(e) => setForm({ ...form, manager: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                  >
                    <option value="">{t('selectDepartment')}</option>
                    {employees.map((emp) => (
                      <option key={emp.id} value={emp.id}>
                        {emp.full_name ||
                          `${emp.first_name || ''} ${emp.last_name || ''}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('description')}
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  rows={3}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none"
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving || !form.name.trim()}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors disabled:opacity-50 font-medium flex items-center justify-center gap-2"
                >
                  {saving && (
                    <svg
                      className="animate-spin h-4 w-4"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                  )}
                  {saving ? t('saving') : editingDept ? t('save') : t('create')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
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
