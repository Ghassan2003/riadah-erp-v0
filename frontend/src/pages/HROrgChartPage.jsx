/**
 * Organizational Chart page - HR module.
 * Interactive tree view of departments and employees.
 * Shows visual hierarchy with connecting lines, statistics sidebar,
 * expandable/collapsible departments, and employee cards.
 * Supports dark mode and Arabic text throughout.
 */

import { useState, useEffect } from 'react';
import { hrReportsAPI, departmentsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Search, ChevronDown, ChevronRight, Users, Building2,
  User, UserCircle, Network, ArrowDown, RefreshCw, BarChart3,
  Layers, Eye, X, Briefcase, Mail, Phone,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/* ── Constants ── */

const DEPT_COLORS = [
  'border-r-riadah-500 dark:border-r-riadah-400',
  'border-r-blue-500 dark:border-r-blue-400',
  'border-r-emerald-500 dark:border-r-emerald-400',
  'border-r-amber-500 dark:border-r-amber-400',
  'border-r-purple-500 dark:border-r-purple-400',
  'border-r-rose-500 dark:border-r-rose-400',
  'border-r-cyan-500 dark:border-r-cyan-400',
  'border-r-indigo-500 dark:border-r-indigo-400',
];

export default function HROrgChartPage() {
  const { isHR } = useAuth();

  const [loading, setLoading] = useState(true);
  const [orgData, setOrgData] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [expandedDepts, setExpandedDepts] = useState({});
  const [search, setSearch] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchOrgChart = async () => {
    setLoading(true);
    try {
      const res = await hrReportsAPI.getOrgChart();
      const data = res.data;
      if (data && (data.tree || data.departments || Array.isArray(data))) {
        setOrgData(data.tree || data.departments || data);
      } else {
        // Fallback: build tree from departments API
        const deptRes = await departmentsAPI.list();
        const deptList = deptRes.data.results || deptRes.data || [];
        setDepartments(deptList);
        // Try to get department tree
        try {
          const treeRes = await departmentsAPI.getDepartmentTree();
          const treeData = treeRes.data;
          setOrgData(treeData.tree || treeData.departments || treeData);
        } catch {
          setOrgData(deptList);
        }
      }
      // Auto-expand all top-level departments
      const initialExpand = {};
      const items = data?.tree || data?.departments || Array.isArray(data) ? data : [];
      (Array.isArray(items) ? items : []).forEach((dept) => {
        if (dept.id) initialExpand[dept.id] = true;
      });
      setExpandedDepts(initialExpand);
    } catch {
      toast.error('خطأ في تحميل الهيكل التنظيمي');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOrgChart(); }, []);

  // ──────────────────────── Actions ────────────────────────

  const toggleDepartment = (deptId) => {
    setExpandedDepts((prev) => ({ ...prev, [deptId]: !prev[deptId] }));
  };

  const expandAll = () => {
    const allExpanded = {};
    const collectIds = (items) => {
      if (!Array.isArray(items)) return;
      items.forEach((item) => {
        if (item.id) {
          allExpanded[item.id] = true;
          if (item.children || item.sub_departments) {
            collectIds(item.children || item.sub_departments);
          }
        }
      });
    };
    collectIds(orgData);
    setExpandedDepts(allExpanded);
  };

  const collapseAll = () => {
    setExpandedDepts({});
  };

  const openDetail = (emp) => {
    setSelectedEmployee(emp);
    setShowDetailModal(true);
  };

  // ──────────────────────── Helpers ────────────────────────

  const Spinner = () => (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );

  const flattenEmployees = (items) => {
    const emps = [];
    if (!Array.isArray(items)) return emps;
    items.forEach((item) => {
      if (item.employees) {
        item.employees.forEach((e) => emps.push({ ...e, _dept_name: item.name }));
      }
      if (item.children || item.sub_departments) {
        emps.push(...flattenEmployees(item.children || item.sub_departments));
      }
    });
    return emps;
  };

  const flattenDepts = (items) => {
    const depts = [];
    if (!Array.isArray(items)) return depts;
    items.forEach((item) => {
      if (item.id) depts.push(item);
      if (item.children || item.sub_departments) {
        depts.push(...flattenDepts(item.children || item.sub_departments));
      }
    });
    return depts;
  };

  const allEmployees = orgData ? flattenEmployees(orgData) : [];
  const allDepts = orgData ? flattenDepts(orgData) : [];
  const filteredEmployees = search
    ? allEmployees.filter((e) =>
        (e.full_name || e.name || '').includes(search) ||
        (e.position || '').includes(search) ||
        (e._dept_name || '').includes(search)
      )
    : [];

  /* Calculate statistics */
  const totalEmployees = allEmployees.length;
  const totalDepartments = allDepts.length;
  const managersCount = allDepts.filter((d) => d.manager_name || d.manager).length;

  const calculateDepth = (items, depth = 1) => {
    if (!Array.isArray(items)) return depth;
    let maxDepth = depth;
    items.forEach((item) => {
      const children = item.children || item.sub_departments;
      if (children && children.length > 0) {
        const childDepth = calculateDepth(children, depth + 1);
        if (childDepth > maxDepth) maxDepth = childDepth;
      }
    });
    return maxDepth;
  };
  const orgDepth = orgData ? calculateDepth(orgData) : 0;

  const avgSpanOfControl = totalDepartments > 0
    ? (totalEmployees / totalDepartments).toFixed(1)
    : '0';

  // ──────────────────────── Recursive Tree Renderer ────────────────────────

  const renderTreeNode = (item, level = 0, colorIndex = 0) => {
    const isExpanded = expandedDepts[item.id];
    const hasChildren = (item.children && item.children.length > 0) ||
                        (item.sub_departments && item.sub_departments.length > 0);
    const hasEmployees = item.employees && item.employees.length > 0;
    const employeeCount = item.employees ? item.employees.length : 0;
    const borderColor = DEPT_COLORS[colorIndex % DEPT_COLORS.length];

    const children = item.children || item.sub_departments || [];
    const employees = item.employees || [];

    // Filter employees by search if applicable
    const filteredEmps = search
      ? employees.filter((e) =>
          (e.full_name || e.name || '').includes(search) ||
          (e.position || '').includes(search)
        )
      : employees;

    // Hide node if searching and no matching employees
    if (search && filteredEmps.length === 0 && !children.some((c) => flattenEmployees([c]).some((e) =>
      (e.full_name || e.name || '').includes(search) || (e.position || '').includes(search)
    ))) {
      return null;
    }

    return (
      <div key={item.id} className="relative">
        {/* ── Department Card ── */}
        <div
          className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700
            border-r-4 ${borderColor} transition-all`}
          style={{ marginRight: `${level * 24}px` }}
        >
          {/* Department Header */}
          <button
            onClick={() => toggleDepartment(item.id)}
            className="w-full flex items-center justify-between p-4 text-right hover:bg-gray-50 dark:hover:bg-gray-700/30 rounded-xl transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                <Building2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">{item.name}</h3>
                <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {item.manager_name && (
                    <span className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {item.manager_name}
                    </span>
                  )}
                  {employeeCount > 0 && (
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {employeeCount} موظف
                    </span>
                  )}
                </div>
              </div>
            </div>

            {hasChildren && (
              <div className="flex items-center gap-2">
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </div>
            )}
          </button>

          {/* Expanded: Employees */}
          {isExpanded && (
            <div className="px-4 pb-4">
              {/* ── Employee Cards ── */}
              {filteredEmps.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-2">
                  {filteredEmps.map((emp, empIdx) => (
                    <button
                      key={emp.id || empIdx}
                      onClick={() => openDetail(emp)}
                      className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-right"
                    >
                      {/* Photo Placeholder */}
                      <div className="w-10 h-10 bg-riadah-100 dark:bg-riadah-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                        {emp.photo ? (
                          <img src={emp.photo} alt="" className="w-10 h-10 rounded-full object-cover" />
                        ) : (
                          <UserCircle className="w-6 h-6 text-riadah-500 dark:text-riadah-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 dark:text-gray-100 text-sm truncate">
                          {emp.full_name || emp.name || '-'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {emp.position || emp.job_title || '-'}
                        </p>
                        {emp.email && (
                          <p className="text-xs text-gray-400 dark:text-gray-500 truncate" dir="ltr">
                            {emp.email}
                          </p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* ── Connecting line to sub-departments ── */}
              {hasChildren && children.length > 0 && (
                <div className="mt-3 border-t border-dashed border-gray-200 dark:border-gray-600 pt-3">
                  {children.map((child, idx) => renderTreeNode(child, 0, colorIndex + idx + 1))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // ──────────────────────── Render ────────────────────────

  const topItems = orgData ? (Array.isArray(orgData) ? orgData : []) : [];

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الهيكل التنظيمي</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">عرض تفاعلي للهيكل التنظيمي والأقسام والموظفين</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={expandAll}
            className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
            توسيع الكل
          </button>
          <button onClick={collapseAll}
            className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
            طي الكل
          </button>
          <button onClick={fetchOrgChart} disabled={loading}
            className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* ── Main Content (Tree) ── */}
        <div className="flex-1 space-y-4">
          {/* Search */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input type="text" placeholder="بحث عن موظف أو وظيفة..." value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none" />
            </div>
          </div>

          {/* Search Results (when searching) */}
          {search && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="px-4 py-3 border-b dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  نتائج البحث: {filteredEmployees.length} موظف
                </p>
              </div>
              {filteredEmployees.length === 0 ? (
                <div className="p-8 text-center">
                  <Users className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-500 dark:text-gray-400 text-sm">لا توجد نتائج</p>
                </div>
              ) : (
                <div className="divide-y dark:divide-gray-700 max-h-96 overflow-y-auto">
                  {filteredEmployees.map((emp, idx) => (
                    <button key={emp.id || idx}
                      onClick={() => openDetail(emp)}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors text-right">
                      <div className="w-10 h-10 bg-riadah-100 dark:bg-riadah-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                        {emp.photo ? (
                          <img src={emp.photo} alt="" className="w-10 h-10 rounded-full object-cover" />
                        ) : (
                          <UserCircle className="w-6 h-6 text-riadah-500 dark:text-riadah-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{emp.full_name || emp.name || '-'}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{emp.position || emp.job_title || '-'}</p>
                        <p className="text-xs text-gray-400 dark:text-gray-500">{emp._dept_name || '-'}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tree View */}
          {!search && (
            <div className="space-y-3">
              {loading ? (
                <div className="flex items-center justify-center p-12 text-gray-400 dark:text-gray-500 gap-3">
                  <Spinner /><span>جاري تحميل الهيكل التنظيمي...</span>
                </div>
              ) : topItems.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
                  <Network className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">لا توجد بيانات للهيكل التنظيمي</p>
                </div>
              ) : (
                topItems.map((item, idx) => renderTreeNode(item, 0, idx))
              )}
            </div>
          )}
        </div>

        {/* ── Statistics Sidebar ── */}
        <div className="lg:w-80 space-y-4">
          {/* Stats Cards */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-riadah-500" />
              إحصائيات الهيكل التنظيمي
            </h3>
            <div className="space-y-4">
              {/* Total Employees */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="w-10 h-10 bg-riadah-100 dark:bg-riadah-900/30 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-riadah-600 dark:text-riadah-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalEmployees}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">إجمالي الموظفين</p>
                </div>
              </div>

              {/* Total Departments */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalDepartments}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">عدد الأقسام</p>
                </div>
              </div>

              {/* Average Span of Control */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                  <Layers className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{avgSpanOfControl}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">متوسط نطاق الإشراف</p>
                </div>
              </div>

              {/* Org Depth */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center">
                  <Network className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{orgDepth}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">عمق الهيكل التنظيمي</p>
                </div>
              </div>
            </div>
          </div>

          {/* Departments List (compact) */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-gray-400" />
              الأقسام
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {allDepts.map((dept) => {
                const empCount = dept.employees ? dept.employees.length : 0;
                return (
                  <button
                    key={dept.id}
                    onClick={() => toggleDepartment(dept.id)}
                    className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors text-right"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {expandedDepts[dept.id] ? (
                        <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      )}
                      <span className="text-sm text-gray-700 dark:text-gray-300 truncate">{dept.name}</span>
                    </div>
                    <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full flex-shrink-0">
                      {empCount}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          EMPLOYEE DETAIL MODAL
         ═══════════════════════════════════════════════════════════ */}
      {showDetailModal && selectedEmployee && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowDetailModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <User className="w-5 h-5 text-riadah-500" />
                بيانات الموظف
              </h3>
              <button onClick={() => setShowDetailModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5">
              {/* Employee Header */}
              <div className="flex flex-col items-center text-center mb-5">
                <div className="w-20 h-20 bg-riadah-100 dark:bg-riadah-900/30 rounded-full flex items-center justify-center mb-3">
                  {selectedEmployee.photo ? (
                    <img src={selectedEmployee.photo} alt="" className="w-20 h-20 rounded-full object-cover" />
                  ) : (
                    <UserCircle className="w-12 h-12 text-riadah-500 dark:text-riadah-400" />
                  )}
                </div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {selectedEmployee.full_name || selectedEmployee.name || '-'}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {selectedEmployee.position || selectedEmployee.job_title || '-'}
                </p>
              </div>

              {/* Info Grid */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-3 text-sm">
                {selectedEmployee.employee_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">رقم الموظف</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100 font-mono">{selectedEmployee.employee_number}</span>
                  </div>
                )}
                {selectedEmployee._dept_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">القسم</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{selectedEmployee._dept_name}</span>
                  </div>
                )}
                {selectedEmployee.department_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">القسم</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{selectedEmployee.department_name}</span>
                  </div>
                )}
                {selectedEmployee.email && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400">البريد الإلكتروني</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100" dir="ltr">{selectedEmployee.email}</span>
                  </div>
                )}
                {selectedEmployee.phone && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">الهاتف</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100" dir="ltr">{selectedEmployee.phone}</span>
                  </div>
                )}
                {selectedEmployee.hire_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">تاريخ التعيين</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{selectedEmployee.hire_date}</span>
                  </div>
                )}
                {selectedEmployee.manager_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">المدير المباشر</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{selectedEmployee.manager_name}</span>
                  </div>
                )}
                {selectedEmployee.status && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">الحالة</span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      selectedEmployee.status === 'active'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : selectedEmployee.status === 'on_leave'
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {selectedEmployee.status === 'active' ? 'نشط'
                        : selectedEmployee.status === 'on_leave' ? 'في إجازة'
                        : selectedEmployee.status === 'suspended' ? 'موقوف'
                        : selectedEmployee.status === 'terminated' ? 'منتهي'
                        : selectedEmployee.status}
                    </span>
                  </div>
                )}
              </div>

              <button onClick={() => setShowDetailModal(false)}
                className="w-full mt-4 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
