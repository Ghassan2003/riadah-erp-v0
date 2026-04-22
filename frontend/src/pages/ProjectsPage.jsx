/**
 * Projects page - project management with tasks and expenses.
 * Features: project cards, task management, expense tracking, filters.
 * Supports dark mode and i18n.
 */

import { useState, useEffect, useCallback } from 'react';
import { projectsAPI, projectTasksAPI, projectExpensesAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import { useI18n } from '../i18n/I18nContext';
import {
  FolderKanban, Plus, Search, Edit3, Trash2, X, Save, Loader2,
  AlertTriangle, Filter, ChevronDown, ChevronUp,
  CheckCircle, Clock, Circle, DollarSign, User,
  CalendarDays, Target, ListTodo, Receipt, Download, Paperclip,
} from 'lucide-react';
import toast from 'react-hot-toast';
import AttachmentManager from '../components/AttachmentManager';

const emptyProjectForm = {
  name: '',
  description: '',
  status: 'planning',
  priority: 'medium',
  start_date: '',
  end_date: '',
  budget: '',
  manager: '',
};

const emptyTaskForm = {
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  assignee: '',
  due_date: '',
};

const emptyExpenseForm = {
  description: '',
  amount: '',
  category: '',
  date: '',
};

export default function ProjectsPage() {
  const { t, locale } = useI18n();

  const STATUS_CONFIG = {
    planning:  { label: t('planning'),  color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',     barColor: 'bg-gray-400' },
    active:    { label: t('active'),    color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300',   barColor: 'bg-riadah-500' },
    on_hold:   { label: t('onHold'),    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', barColor: 'bg-yellow-500' },
    completed: { label: t('completed'), color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', barColor: 'bg-green-500' },
    cancelled: { label: t('cancelled'), color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',       barColor: 'bg-red-500' },
  };

  const PRIORITY_CONFIG = {
    low:      { label: t('low'),      color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
    medium:   { label: t('medium'),   color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300' },
    high:     { label: t('high'),     color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300' },
    critical: { label: t('critical'), color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' },
  };

  const TASK_STATUS_CONFIG = {
    todo:        { label: t('notStarted'), color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',   icon: Circle },
    in_progress: { label: t('inProgress'), color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300', icon: Clock },
    done:        { label: t('completed'),  color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: CheckCircle },
  };

  const numLocale = locale === 'ar' ? 'ar-SA' : 'en-US';

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Project modal
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [projectForm, setProjectForm] = useState(emptyProjectForm);
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Expanded project
  const [expandedProject, setExpandedProject] = useState(null);
  const [projectTasks, setProjectTasks] = useState([]);
  const [projectExpenses, setProjectExpenses] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Task modal
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskForm, setTaskForm] = useState(emptyTaskForm);
  const [taskLoading, setTaskLoading] = useState(false);

  // Expense modal
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseForm, setExpenseForm] = useState(emptyExpenseForm);
  const [expenseLoading, setExpenseLoading] = useState(false);

  // Active detail tab
  const [detailTab, setDetailTab] = useState('tasks');
  const [attachmentsTab, setAttachmentsTab] = useState(false);

  // Export state
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.projects();
      downloadBlob(new Blob([response.data]), 'projects.xlsx');
      toast.success(t('dataExported'));
    } catch (error) {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        search: searchTerm || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      };
      const response = await projectsAPI.list(params);
      const data = response.data;
      setProjects(data.results || (Array.isArray(data) ? data : []));
    } catch {
      toast.error(t('failedLoadingProjects'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter, priorityFilter, t]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  // Fetch project details (tasks + expenses)
  const fetchProjectDetails = async (projectId) => {
    setLoadingDetails(true);
    setDetailTab('tasks');
    setAttachmentsTab(false);
    try {
      const [tasksRes, expensesRes] = await Promise.all([
        projectTasksAPI.list({ project: projectId }),
        projectExpensesAPI.list({ project: projectId }),
      ]);
      const tasksData = tasksRes.data;
      const expensesData = expensesRes.data;
      setProjectTasks(tasksData.results || (Array.isArray(tasksData) ? tasksData : []));
      setProjectExpenses(expensesData.results || (Array.isArray(expensesData) ? expensesData : []));
    } catch {
      toast.error(t('failedLoadingProjectDetails'));
    } finally {
      setLoadingDetails(false);
    }
  };

  const toggleExpand = (project) => {
    if (expandedProject === project.id) {
      setExpandedProject(null);
    } else {
      setExpandedProject(project.id);
      fetchProjectDetails(project.id);
    }
  };

  // Project form handling
  const openCreateProject = () => {
    setEditingProject(null);
    setProjectForm(emptyProjectForm);
    setFormErrors({});
    setShowProjectModal(true);
  };

  const openEditProject = (project) => {
    setEditingProject(project);
    setProjectForm({
      name: project.name,
      description: project.description || '',
      status: project.status,
      priority: project.priority,
      start_date: project.start_date || '',
      end_date: project.end_date || '',
      budget: project.budget || '',
      manager: project.manager || '',
    });
    setFormErrors({});
    setShowProjectModal(true);
  };

  const closeProjectModal = () => {
    setShowProjectModal(false);
    setEditingProject(null);
    setProjectForm(emptyProjectForm);
    setFormErrors({});
  };

  const validateProjectForm = () => {
    const errors = {};
    if (!projectForm.name.trim()) errors.name = t('projectNameRequired');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleProjectSubmit = async (e) => {
    e.preventDefault();
    if (!validateProjectForm()) return;
    setFormLoading(true);
    try {
      const payload = { ...projectForm };
      if (payload.budget) payload.budget = parseFloat(payload.budget);
      if (editingProject) {
        await projectsAPI.update(editingProject.id, payload);
        toast.success(t('projectUpdated'));
      } else {
        await projectsAPI.create(payload);
        toast.success(t('projectCreated'));
      }
      closeProjectModal();
      fetchProjects();
    } catch (error) {
      const data = error.response?.data;
      if (data) {
        const fieldErrors = {};
        Object.keys(data).forEach((key) => {
          if (key !== 'message' && key !== 'error') {
            fieldErrors[key] = Array.isArray(data[key]) ? data[key][0] : data[key];
          }
        });
        if (Object.keys(fieldErrors).length > 0) setFormErrors(fieldErrors);
        else toast.error(data.message || data.error || t('operationFailed'));
      } else {
        toast.error(t('operationFailed'));
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Delete
  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await projectsAPI.delete(deleteConfirm.id);
      toast.success(t('projectDeleted'));
      setDeleteConfirm(null);
      if (expandedProject === deleteConfirm.id) setExpandedProject(null);
      fetchProjects();
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedDeletingProject'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // Task handling
  const openCreateTask = () => {
    setTaskForm({ ...emptyTaskForm, project: expandedProject });
    setShowTaskModal(true);
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();
    if (!taskForm.title.trim()) {
      toast.error(t('taskNameRequired'));
      return;
    }
    setTaskLoading(true);
    try {
      await projectTasksAPI.create({ ...taskForm, project: expandedProject });
      toast.success(t('taskCreated'));
      setShowTaskModal(false);
      setTaskForm(emptyTaskForm);
      fetchProjectDetails(expandedProject);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedCreatingTask'));
    } finally {
      setTaskLoading(false);
    }
  };

  const handleTaskStatusChange = async (task, newStatus) => {
    try {
      await projectTasksAPI.update(task.id, { status: newStatus });
      toast.success(t('taskStatusUpdated'));
      fetchProjectDetails(expandedProject);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedUpdatingTaskStatus'));
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await projectTasksAPI.delete(taskId);
      toast.success(t('taskDeleted'));
      fetchProjectDetails(expandedProject);
    } catch {
      toast.error(t('failedDeletingTask'));
    }
  };

  // Expense handling
  const openCreateExpense = () => {
    setExpenseForm({ ...emptyExpenseForm, project: expandedProject });
    setShowExpenseModal(true);
  };

  const handleExpenseSubmit = async (e) => {
    e.preventDefault();
    if (!expenseForm.description.trim() || !expenseForm.amount) {
      toast.error(t('fillRequiredFields'));
      return;
    }
    setExpenseLoading(true);
    try {
      await projectExpensesAPI.create({
        ...expenseForm,
        project: expandedProject,
        amount: parseFloat(expenseForm.amount),
      });
      toast.success(t('expenseCreated'));
      setShowExpenseModal(false);
      setExpenseForm(emptyExpenseForm);
      fetchProjectDetails(expandedProject);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedCreatingExpense'));
    } finally {
      setExpenseLoading(false);
    }
  };

  const handleDeleteExpense = async (expenseId) => {
    try {
      await projectExpensesAPI.delete(expenseId);
      toast.success(t('expenseDeleted'));
      fetchProjectDetails(expandedProject);
    } catch {
      toast.error(t('failedDeletingExpense'));
    }
  };

  const formatAmount = (val) => Number(val || 0).toLocaleString(numLocale, { minimumFractionDigits: 0, maximumFractionDigits: 0 });

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageProjects')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageProjectsDesc')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 dark:bg-green-700 hover:bg-green-700 dark:hover:bg-green-800 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('exporting')}...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                {t('exportExcel')}
              </>
            )}
          </button>
          <button
            onClick={openCreateProject}
            className="flex items-center gap-2 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            {t('addNewProject')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder={t('searchProjects')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
          />
        </div>
        <div className="relative">
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="appearance-none pr-9 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
          >
            <option value="">{t('allStatuses')}</option>
            {Object.entries(STATUS_CONFIG).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
        </div>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="appearance-none px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
        >
          <option value="">{t('allPriorities')}</option>
          {Object.entries(PRIORITY_CONFIG).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
      </div>

      {/* Projects list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-20 text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
          <FolderKanban className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
          <p className="text-lg font-medium">{t('noProjects')}</p>
          <p className="text-sm mt-1">{searchTerm ? t('noResults') : t('createFirstProject')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => {
            const statusCfg = STATUS_CONFIG[project.status] || STATUS_CONFIG.planning;
            const priorityCfg = PRIORITY_CONFIG[project.priority] || PRIORITY_CONFIG.medium;
            const progress = project.progress || 0;
            const isExpanded = expandedProject === project.id;

            return (
              <div key={project.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                {/* Project card header */}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{project.name}</h3>
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.color}`}>
                          {statusCfg.label}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${priorityCfg.color}`}>
                          {priorityCfg.label}
                        </span>
                      </div>
                      {project.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 truncate">{project.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
                        {project.manager && (
                          <span className="flex items-center gap-1"><User className="w-3.5 h-3.5" /> {project.manager}</span>
                        )}
                        {project.start_date && (
                          <span className="flex items-center gap-1"><CalendarDays className="w-3.5 h-3.5" /> {project.start_date}</span>
                        )}
                        {project.end_date && (
                          <span className="flex items-center gap-1"><Target className="w-3.5 h-3.5" /> {project.end_date}</span>
                        )}
                        {project.budget > 0 && (
                          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 font-medium"><DollarSign className="w-3.5 h-3.5" /> {formatAmount(project.budget)} {t('currency')}</span>
                        )}
                      </div>
                      {/* Progress bar */}
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                          <span>{t('progress')}</span>
                          <span className="font-medium">{progress}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${statusCfg.barColor}`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button onClick={() => openEditProject(project)} className="p-1.5 text-accent-500 hover:bg-riadah-50 dark:text-accent-400 dark:hover:bg-riadah-900/20 rounded-lg transition-colors" title={t('edit')}>
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button onClick={() => setDeleteConfirm(project)} className="p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors" title={t('delete')}>
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => toggleExpand(project)} className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title={t('details')}>
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30">
                    {/* Detail tabs */}
                    <div className="flex gap-2 px-5 pt-4">
                      <button
                        onClick={() => setDetailTab('tasks')}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          detailTab === 'tasks' ? 'bg-riadah-500 dark:bg-riadah-700 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                        }`}
                      >
                        <ListTodo className="w-4 h-4" />
                        {t('tasks')} ({projectTasks.length})
                      </button>
                      <button
                        onClick={() => setDetailTab('expenses')}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          detailTab === 'expenses' ? 'bg-riadah-500 dark:bg-riadah-700 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                        }`}
                      >
                        <Receipt className="w-4 h-4" />
                        {t('expenses')} ({projectExpenses.length})
                      </button>
                      <button
                        onClick={() => { setDetailTab('attachments'); setAttachmentsTab(true); }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          detailTab === 'attachments' ? 'bg-riadah-500 dark:bg-riadah-700 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                        }`}
                      >
                        <Paperclip className="w-4 h-4" />
                        {t('attachments')}
                      </button>
                    </div>

                    <div className="p-5">
                      {loadingDetails ? (
                        <div className="flex items-center justify-center py-10">
                          <Loader2 className="w-6 h-6 animate-spin text-accent-500" />
                        </div>
                      ) : detailTab === 'tasks' ? (
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-gray-800 dark:text-gray-200">{t('projectTasks')}</h4>
                            <button
                              onClick={openCreateTask}
                              className="flex items-center gap-1 text-sm font-medium text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300"
                            >
                              <Plus className="w-4 h-4" /> {t('addTask')}
                            </button>
                          </div>
                          {projectTasks.length === 0 ? (
                            <p className="text-center text-gray-400 dark:text-gray-500 py-8 text-sm">{t('noTasksYet')}</p>
                          ) : (
                            <div className="space-y-2">
                              {projectTasks.map((task) => {
                                const taskCfg = TASK_STATUS_CONFIG[task.status] || TASK_STATUS_CONFIG.todo;
                                const TaskIcon = taskCfg.icon;
                                return (
                                  <div key={task.id} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                    <div className="flex items-center gap-3 min-w-0">
                                      <button
                                        onClick={() => {
                                          const next = task.status === 'todo' ? 'in_progress' : task.status === 'in_progress' ? 'done' : 'todo';
                                          handleTaskStatusChange(task, next);
                                        }}
                                        className="flex-shrink-0"
                                        title={t('changeStatus')}
                                      >
                                        <TaskIcon className={`w-5 h-5 ${task.status === 'done' ? 'text-green-600 dark:text-green-400' : task.status === 'in_progress' ? 'text-accent-500 dark:text-accent-400' : 'text-gray-400 dark:text-gray-500'}`} />
                                      </button>
                                      <div className="min-w-0">
                                        <p className={`text-sm font-medium ${task.status === 'done' ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-900 dark:text-gray-100'}`}>{task.title}</p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                          <span className={`text-xs px-2 py-0.5 rounded-full ${taskCfg.color}`}>{taskCfg.label}</span>
                                          {task.priority && (
                                            <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_CONFIG[task.priority]?.color || ''}`}>
                                              {PRIORITY_CONFIG[task.priority]?.label || task.priority}
                                            </span>
                                          )}
                                          {task.due_date && (
                                            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
                                              <CalendarDays className="w-3 h-3" /> {task.due_date}
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                    <button
                                      onClick={() => handleDeleteTask(task.id)}
                                      className="p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg flex-shrink-0"
                                    >
                                      <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-gray-800 dark:text-gray-200">{t('projectExpenses')}</h4>
                            <button
                              onClick={openCreateExpense}
                              className="flex items-center gap-1 text-sm font-medium text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300"
                            >
                              <Plus className="w-4 h-4" /> {t('addExpense')}
                            </button>
                          </div>
                          {projectExpenses.length === 0 ? (
                            <p className="text-center text-gray-400 dark:text-gray-500 py-8 text-sm">{t('noExpensesYet')}</p>
                          ) : (
                            <>
                              <div className="space-y-2">
                                {projectExpenses.map((expense) => (
                                  <div key={expense.id} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                    <div>
                                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{expense.description}</p>
                                      <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                                        {expense.category && <span>{expense.category}</span>}
                                        {expense.date && <span>{expense.date}</span>}
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-sm font-bold text-red-600 dark:text-red-400" dir="ltr">{formatAmount(expense.amount)} {t('currency')}</span>
                                      <button
                                        onClick={() => handleDeleteExpense(expense.id)}
                                        className="p-1 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg"
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                              <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex justify-end">
                                <span className="text-base font-bold text-gray-900 dark:text-gray-100">
                                  {t('total')}: <span className="text-red-600 dark:text-red-400" dir="ltr">{formatAmount(projectExpenses.reduce((s, e) => s + (e.amount || 0), 0))} {t('currency')}</span>
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      ) : detailTab === 'attachments' ? (
                        <AttachmentManager
                          contentType="projects.project"
                          objectId={project.id}
                          category="project"
                        />
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Project Modal */}
      {showProjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={closeProjectModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingProject ? t('editProject') : t('addNewProject')}
              </h3>
              <button onClick={closeProjectModal} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleProjectSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('projectName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={projectForm.name}
                  onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 ${
                    formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/20' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder={t('projectNamePlaceholder')}
                />
                {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
                <textarea
                  value={projectForm.description}
                  onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
                  placeholder={t('projectDescriptionPlaceholder')}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('projectStatus')}</label>
                  <select
                    value={projectForm.status}
                    onChange={(e) => setProjectForm({ ...projectForm, status: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  >
                    {Object.entries(STATUS_CONFIG).map(([key, val]) => (
                      <option key={key} value={key}>{val.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('priority')}</label>
                  <select
                    value={projectForm.priority}
                    onChange={(e) => setProjectForm({ ...projectForm, priority: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  >
                    {Object.entries(PRIORITY_CONFIG).map(([key, val]) => (
                      <option key={key} value={key}>{val.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('startDate')}</label>
                  <input
                    type="date"
                    value={projectForm.start_date}
                    onChange={(e) => setProjectForm({ ...projectForm, start_date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('endDate')}</label>
                  <input
                    type="date"
                    value={projectForm.end_date}
                    onChange={(e) => setProjectForm({ ...projectForm, end_date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('budget')} ({t('currency')})</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={projectForm.budget}
                    onChange={(e) => setProjectForm({ ...projectForm, budget: e.target.value })}
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('projectManager')}</label>
                  <input
                    type="text"
                    value={projectForm.manager}
                    onChange={(e) => setProjectForm({ ...projectForm, manager: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    placeholder={t('managerNamePlaceholder')}
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {formLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</>
                  ) : (
                    <><Save className="w-4 h-4" /> {editingProject ? t('updateProject') : t('createProject')}</>
                  )}
                </button>
                <button
                  type="button"
                  onClick={closeProjectModal}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Task Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setShowTaskModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('addTask')}</h3>
              <button onClick={() => setShowTaskModal(false)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleTaskSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('taskName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  placeholder={t('taskNamePlaceholder')}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
                <textarea
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('priority')}</label>
                  <select
                    value={taskForm.priority}
                    onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  >
                    {Object.entries(PRIORITY_CONFIG).map(([key, val]) => (
                      <option key={key} value={key}>{val.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('dueDate')}</label>
                  <input
                    type="date"
                    value={taskForm.due_date}
                    onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={taskLoading}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {taskLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</> : <><Save className="w-4 h-4" /> {t('addTask')}</>}
                </button>
                <button
                  type="button"
                  onClick={() => setShowTaskModal(false)}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Expense Modal */}
      {showExpenseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setShowExpenseModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('addExpense')}</h3>
              <button onClick={() => setShowExpenseModal(false)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleExpenseSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('description')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={expenseForm.description}
                  onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  placeholder={t('expenseDescriptionPlaceholder')}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('amount')} ({t('currency')}) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={expenseForm.amount}
                    onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })}
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('date')}</label>
                  <input
                    type="date"
                    value={expenseForm.date}
                    onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('category')}</label>
                <input
                  type="text"
                  value={expenseForm.category}
                  onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  placeholder={t('categoryPlaceholder')}
                />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={expenseLoading}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {expenseLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</> : <><Save className="w-4 h-4" /> {t('addExpense')}</>}
                </button>
                <button
                  type="button"
                  onClick={() => setShowExpenseModal(false)}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirm')}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                {t('confirmDeleteProject')} <span className="font-semibold text-gray-900 dark:text-gray-100"> "{deleteConfirm.name}"</span>?
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteLoading}
                  className="flex-1 bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {deleteLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</> : <><Trash2 className="w-4 h-4" /> {t('deleteProject')}</>}
                </button>
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
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
