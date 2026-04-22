/**
 * Cron Jobs Page - Manage and track automated tasks.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Clock, Play, Pause, Trash2, Plus, RefreshCw, Settings,
  CheckCircle2, XCircle, AlertTriangle, Zap, Calendar,
  Edit3, Activity, BarChart3,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cronJobAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';

const TASK_OPTIONS = [
  { value: 'auto_backup_daily', label: 'dailyBackup' },
  { value: 'auto_backup_weekly', label: 'weeklyBackup' },
  { value: 'auto_backup_monthly', label: 'monthlyBackup' },
  { value: 'inventory_alerts', label: 'lowStockAlerts' },
  { value: 'recurring_invoices', label: 'recurringInvoices' },
  { value: 'clean_old_logs', label: 'cleanOldLogs' },
  { value: 'clean_old_backups', label: 'cleanOldBackups' },
  { value: 'employee_attendance_reminder', label: 'attendanceReminder' },
  { value: 'expense_alerts', label: 'expenseAlerts' },
  { value: 'project_deadline_alerts', label: 'projectDeadlineAlerts' },
];

const FREQUENCY_OPTIONS = [
  { value: 'every_5_minutes', label: 'every5Minutes' },
  { value: 'every_15_minutes', label: 'every15Minutes' },
  { value: 'every_30_minutes', label: 'every30Minutes' },
  { value: 'hourly', label: 'hourly' },
  { value: 'every_6_hours', label: 'every6Hours' },
  { value: 'daily', label: 'daily' },
  { value: 'weekly', label: 'weekly' },
  { value: 'monthly', label: 'monthly' },
];

const TASK_CONFIGS = {
  inventory_alerts: [
    { key: 'low_stock_threshold', label: 'lowStockThreshold', type: 'number', default: 10 },
  ],
  clean_old_logs: [
    { key: 'keep_days', label: 'keepDaysErrors', type: 'number', default: 90 },
    { key: 'audit_keep_days', label: 'keepDaysAudit', type: 'number', default: 180 },
  ],
  clean_old_backups: [
    { key: 'keep_count', label: 'keepBackupCount', type: 'number', default: 30 },
  ],
  expense_alerts: [
    { key: 'expense_threshold', label: 'expenseThreshold', type: 'number', default: 50000 },
  ],
  project_deadline_alerts: [
    { key: 'days_before_deadline', label: 'daysBeforeDeadline', type: 'number', default: 7 },
  ],
};

export default function CronJobsPage() {
  const { t, locale } = useI18n();
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(null);
  const [runningJob, setRunningJob] = useState(null);
  const [formData, setFormData] = useState({
    name: '', task: 'inventory_alerts', frequency: 'daily', config: {},
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [listRes, statsRes] = await Promise.all([
        cronJobAPI.list({ ordering: '-created_at' }),
        cronJobAPI.stats(),
      ]);
      setJobs(listRes.data.results || listRes.data);
      setStats(statsRes.data);
    } catch {
      toast.error(t('error') + ': ' + t('loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    try {
      const config = formData.config;
      await cronJobAPI.create({ ...formData, config });
      toast.success(t('jobCreated'));
      setShowCreate(false);
      setFormData({ name: '', task: 'inventory_alerts', frequency: 'daily', config: {} });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.error || t('createFailed'));
    }
  };

  const handleUpdate = async () => {
    if (!showEdit) return;
    try {
      await cronJobAPI.update(showEdit.id, {
        name: formData.name,
        frequency: formData.frequency,
        config: formData.config,
      });
      toast.success(t('jobUpdated'));
      setShowEdit(null);
      fetchData();
    } catch {
      toast.error(t('updateFailed'));
    }
  };

  const handleToggle = async (job) => {
    const action = job.status === 'active' || job.status === 'failed' ? 'pause' : 'activate';
    try {
      await cronJobAPI.toggle(job.id, { action });
      toast.success(action === 'activate' ? t('jobEnabled') : t('jobDisabled'));
      fetchData();
    } catch {
      toast.error(t('updateFailed'));
    }
  };

  const handleRunNow = async (job) => {
    setRunningJob(job.id);
    try {
      const res = await cronJobAPI.runNow(job.id);
      if (res.data.status === 'success') {
        toast.success(res.data.message);
      } else {
        toast.error(res.data.message);
      }
      fetchData();
    } catch {
      toast.error(t('executeFailed'));
    } finally {
      setRunningJob(null);
    }
  };

  const handleDelete = async (job) => {
    if (!confirm(t('confirm') + ': ' + job.name)) return;
    try {
      await cronJobAPI.delete(job.id);
      toast.success(t('jobDeleted'));
      fetchData();
    } catch {
      toast.error(t('deleteFailed'));
    }
  };

  const handleTaskChange = (task) => {
    const taskLabel = TASK_OPTIONS.find(t => t.value === task)?.label || task;
    setFormData(prev => ({
      ...prev,
      task,
      name: prev.name || taskLabel,
      config: {},
    }));
  };

  const updateConfig = (key, value) => {
    setFormData(prev => ({
      ...prev,
      config: { ...prev.config, [key]: value },
    }));
  };

  const openEdit = (job) => {
    setShowEdit(job);
    setFormData({
      name: job.name,
      task: job.task,
      frequency: job.frequency,
      config: job.config || {},
    });
  };

  const statusColors = {
    active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    paused: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    running: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };

  const statusLabels = {
    active: t('active'),
    paused: t('inactive'),
    running: t('running'),
    failed: t('failed'),
  };

  const statusIcons = {
    active: <CheckCircle2 className="w-3.5 h-3.5" />,
    paused: <Pause className="w-3.5 h-3.5" />,
    running: <RefreshCw className="w-3.5 h-3.5" />,
    failed: <XCircle className="w-3.5 h-3.5" />,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  const ConfigForm = ({ task, config, onChange }) => {
    const configs = TASK_CONFIGS[task] || [];
    if (configs.length === 0) return null;
    return (
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4 space-y-3">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
          <Settings className="w-4 h-4" /> {t('jobSettings')}
        </p>
        {configs.map(c => (
          <div key={c.key} className="space-y-1">
            <label className="block text-sm text-gray-600 dark:text-gray-400">{t(c.label)}</label>
            <input
              type={c.type}
              value={config[c.key] ?? c.default}
              onChange={(e) => onChange(c.key, e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500"
            />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Clock className="w-7 h-7 text-purple-600" />
            {t('cronJobsTitle')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('cronJobsDesc')}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm">
            <RefreshCw className="w-4 h-4" /> {t('refresh')}
          </button>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors text-sm">
            <Plus className="w-4 h-4" /> {t('addCronJob')}
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: t('totalJobs'), value: stats.total_jobs, color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
            { label: t('activeJobs'), value: stats.active_jobs, color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
            { label: t('inactive'), value: stats.paused_jobs, color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' },
            { label: t('failed'), value: stats.failed_jobs, color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' },
            { label: t('totalExecutions'), value: stats.total_executions, color: 'bg-riadah-100 text-riadah-800 dark:bg-riadah-900/30 dark:text-accent-300' },
            { label: t('totalFailures'), value: stats.total_failures, color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' },
          ].map((s, i) => (
            <div key={i} className={`${s.color} rounded-xl p-3 text-center`}>
              <p className="text-2xl font-bold">{s.value?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              <p className="text-xs mt-1 opacity-80">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* No jobs */}
      {jobs.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
          <p className="text-gray-500 dark:text-gray-400">{t('noCronJobs')}</p>
        </div>
      )}

      {/* Jobs Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map(job => (
          <div key={job.id} className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-5 space-y-3 transition-all hover:shadow-md ${
            job.status === 'failed' ? 'border-red-200 dark:border-red-800' : job.status === 'active' ? 'border-green-200 dark:border-green-800' : ''
          }`}>
            {/* Card Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className={`p-2 rounded-lg ${job.status === 'active' ? 'bg-green-100 dark:bg-green-900/30' : job.status === 'failed' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-700'}`}>
                  <Zap className={`w-4 h-4 ${job.status === 'active' ? 'text-green-600 dark:text-green-400' : job.status === 'failed' ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{job.name}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{job.task_display}</p>
                </div>
              </div>
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColors[job.status]}`}>
                {statusIcons[job.status]} {statusLabels[job.status]}
              </span>
            </div>

            {/* Info */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
                <p className="text-gray-500 dark:text-gray-400">{t('jobSchedule')}</p>
                <p className="font-medium text-gray-700 dark:text-gray-200">{job.frequency_display}</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
                <p className="text-gray-500 dark:text-gray-400">{t('successRate')}</p>
                <p className={`font-medium ${job.success_rate >= 90 ? 'text-green-600 dark:text-green-400' : job.success_rate >= 70 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
                  {job.success_rate?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}%
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
                <p className="text-gray-500 dark:text-gray-400">{t('runCount')}</p>
                <p className="font-medium text-gray-700 dark:text-gray-200">{job.run_count?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
                <p className="text-gray-500 dark:text-gray-400">{t('jobNextRun')}</p>
                <p className="font-medium text-gray-700 dark:text-gray-200">{job.next_run ? new Date(job.next_run).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US') : '-'}</p>
              </div>
            </div>

            {/* Last Run */}
            {job.last_run && (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">{t('jobLastRun')}</span>
                  <span className={job.last_run_status === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                    {job.last_run_status === 'success' ? t('success') : t('failed')}
                  </span>
                </div>
                <div className="flex justify-between mt-0.5">
                  <span className="text-gray-500 dark:text-gray-400">{t('duration')}</span>
                  <span className="text-gray-700 dark:text-gray-200">{job.last_run_duration ? `${job.last_run_duration.toFixed(1)}s` : '-'}</span>
                </div>
                <div className="flex justify-between mt-0.5">
                  <span className="text-gray-500 dark:text-gray-400">{t('date')}</span>
                  <span className="text-gray-700 dark:text-gray-200">{new Date(job.last_run).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US')}</span>
                </div>
              </div>
            )}

            {/* Error */}
            {job.error_message && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-2 text-xs text-red-700 dark:text-red-400 flex items-start gap-1">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <p className="truncate">{job.error_message}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-1 pt-2 border-t border-gray-100 dark:border-gray-700">
              <button onClick={() => handleRunNow(job)} disabled={runningJob === job.id}
                title={t('runNow')} className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-riadah-50 dark:bg-riadah-900/20 text-riadah-700 dark:text-accent-400 rounded-lg hover:bg-riadah-100 dark:hover:bg-riadah-900/40 disabled:opacity-50 transition-colors">
                {runningJob === job.id ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                {t('runNow')}
              </button>
              <button onClick={() => handleToggle(job)} title={job.status === 'paused' ? t('enableJob') : t('disableJob')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded-lg transition-colors ${
                  job.status === 'paused'
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40'
                    : 'bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                }`}>
                {job.status === 'paused' ? <><Play className="w-3.5 h-3.5" /> {t('enableJob')}</> : <><Pause className="w-3.5 h-3.5" /> {t('disableJob')}</>}
              </button>
              <button onClick={() => openEdit(job)} title={t('edit')}
                className="flex items-center justify-center px-2 py-1.5 text-xs bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors">
                <Edit3 className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => handleDelete(job)} title={t('delete')}
                className="flex items-center justify-center px-2 py-1.5 text-xs bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create/Edit Modal */}
      {(showCreate || showEdit) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {showEdit ? t('editJob') : t('addCronJob')}
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('jobName')}</label>
                <input value={formData.name} onChange={(e) => setFormData(f => ({ ...f, name: e.target.value }))}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500"
                  placeholder={t('jobName')} />
              </div>

              {!showEdit && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('jobType')}</label>
                  <select value={formData.task} onChange={(e) => handleTaskChange(e.target.value)}
                    className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
                    {TASK_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{t(opt.label)}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('jobSchedule')}</label>
                <select value={formData.frequency} onChange={(e) => setFormData(f => ({ ...f, frequency: e.target.value }))}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
                  {FREQUENCY_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{t(opt.label)}</option>
                  ))}
                </select>
              </div>

              <ConfigForm task={formData.task} config={formData.config} onChange={updateConfig} />
            </div>

            <div className="flex gap-3 justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
              <button onClick={() => { setShowCreate(false); setShowEdit(null); }}
                className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">{t('cancel')}</button>
              <button onClick={showEdit ? handleUpdate : handleCreate}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800">
                {showEdit ? t('save') : t('add')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
