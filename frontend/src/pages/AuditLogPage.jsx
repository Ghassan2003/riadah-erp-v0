/**
 * Audit Log Viewer page - admin only.
 * Displays system audit logs with filtering, diff view, stats, and clear functionality.
 */

import { useState, useEffect, useCallback } from 'react';
import { auditLogAPI } from '../api';
import {
  Shield, Search, Filter, Loader2, ChevronDown, ChevronLeft, ChevronRight,
  Trash2, AlertTriangle, X, FileText, Clock, Activity, Users, CalendarDays,
  Eye, Database, Cpu,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

/* Action badge color configuration */
const ACTION_COLORS = {
  create: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  update: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
  delete: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  login: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  logout: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  password_change: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
};

const ACTION_LABELS = {
  create: 'createAction',
  update: 'updateAction',
  delete: 'deleteAction',
  login: 'login',
  logout: 'logout',
  password_change: 'password_change',
};

export default function AuditLogPage() {
  const { t, locale } = useI18n();

  // Data state
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;

  // Filter state
  const [actionFilter, setActionFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Expanded row / diff view
  const [expandedRow, setExpandedRow] = useState(null);

  // Clear logs modal
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearDays, setClearDays] = useState(90);
  const [clearLoading, setClearLoading] = useState(false);

  // Available models (extracted from logs)
  const [availableModels, setAvailableModels] = useState([]);
  const [availableActions, setAvailableActions] = useState([]);

  // Fetch audit logs
  const fetchLogs = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = { page };
      if (actionFilter) params.action = actionFilter;
      if (modelFilter) params.model_name = modelFilter;
      if (userFilter) params.username = userFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await auditLogAPI.list(params);
      const data = response.data;
      setLogs(data.results || (Array.isArray(data) ? data : []));
      setTotalCount(data.count || data.length || 0);
      setCurrentPage(page);

      // Extract unique models and actions for filters
      const allLogs = data.results || data;
      if (Array.isArray(allLogs)) {
        const models = [...new Set(allLogs.map(l => l.model_name).filter(Boolean))];
        const actions = [...new Set(allLogs.map(l => l.action_display || l.action).filter(Boolean))];
        setAvailableModels(models);
        setAvailableActions(actions);
      }
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  }, [actionFilter, modelFilter, userFilter, dateFrom, dateTo]);

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await auditLogAPI.stats();
      setStats(response.data);
    } catch {
      // Silent fail for stats
    }
  };

  useEffect(() => {
    fetchLogs(1);
    fetchStats();
  }, [fetchLogs]);

  const handleClearLogs = async () => {
    setClearLoading(true);
    try {
      await auditLogAPI.clear(clearDays);
      toast.success(t('success'));
      setShowClearModal(false);
      fetchLogs(1);
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.error || t('error'));
    } finally {
      setClearLoading(false);
    }
  };

  const resetFilters = () => {
    setActionFilter('');
    setModelFilter('');
    setUserFilter('');
    setDateFrom('');
    setDateTo('');
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const getActionBadge = (action, actionDisplay) => {
    const actionLower = (action || '').toLowerCase();
    const display = actionDisplay || action || '-';
    const color = ACTION_COLORS[actionLower] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${color}`}>
        {display}
      </span>
    );
  };

  const formatChanges = (changes) => {
    if (!changes) return null;
    try {
      if (typeof changes === 'string') return JSON.parse(changes);
      return changes;
    } catch {
      return changes;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('auditLogTitle')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('auditLogDesc')}</p>
        </div>
        <button
          onClick={() => setShowClearModal(true)}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm"
        >
          <Trash2 className="w-4 h-4" />
          {t('clearOldLogs')}
        </button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('total')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats?.total_logs ?? '...'}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-riadah-50 dark:bg-riadah-900/30 flex items-center justify-center">
              <Database className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('date')}</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats?.today_logs ?? '...'}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
              <Clock className="w-5 h-5 text-green-500 dark:text-green-400" />
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">7 {t('days')}</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats?.week_logs ?? '...'}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center">
              <CalendarDays className="w-5 h-5 text-purple-500 dark:text-purple-400" />
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">30 {t('days')}</p>
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{stats?.month_logs ?? '...'}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-orange-50 dark:bg-orange-900/30 flex items-center justify-center">
              <Activity className="w-5 h-5 text-orange-500 dark:text-orange-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t('searchAudit')}</span>
          <button onClick={resetFilters} className="text-xs text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 font-medium mr-auto">
            {t('cancel')}
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Action filter */}
          <select
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 dark:text-white text-sm"
          >
            <option value="">{t('actionType')}</option>
            {Object.entries(ACTION_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{t(label)}</option>
            ))}
          </select>

          {/* Model filter */}
          <select
            value={modelFilter}
            onChange={(e) => { setModelFilter(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 dark:text-white text-sm"
          >
            <option value="">{t('module')}</option>
            {availableModels.map((model) => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>

          {/* User filter */}
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={userFilter}
              onChange={(e) => { setUserFilter(e.target.value); setCurrentPage(1); }}
              placeholder={t('searchAudit')}
              className="w-full pr-9 pl-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-sm"
            />
          </div>

          {/* Date from */}
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => { setDateFrom(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-sm"
            placeholder={t('dateRange')}
          />

          {/* Date to */}
          <input
            type="date"
            value={dateTo}
            onChange={(e) => { setDateTo(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-sm"
            placeholder={t('dateRange')}
          />
        </div>
      </div>

      {/* Logs table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium">{t('noAuditLogs')}</p>
            <p className="text-sm mt-1">{t('noData')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('timestamp')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('user')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('actionType')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('module')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('description')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('ipAddress')}</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('details')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {logs.map((log, index) => {
                  const isExpanded = expandedRow === log.id;
                  const changes = formatChanges(log.changes);
                  return (
                    <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      {/* Date */}
                      <td className="px-4 py-3">
                        <p className="text-sm text-gray-900 dark:text-gray-100">{log.created_at}</p>
                      </td>

                      {/* User */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-riadah-100 dark:bg-riadah-900/40 flex items-center justify-center text-accent-500 dark:text-accent-400 font-bold text-xs">
                            {(log.username || '?')[0]}
                          </div>
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{log.username || '-'}</span>
                        </div>
                      </td>

                      {/* Action */}
                      <td className="px-4 py-3">
                        {getActionBadge(log.action, log.action_display)}
                      </td>

                      {/* Model */}
                      <td className="px-4 py-3">
                        <span className="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-700 dark:text-gray-300 font-medium">
                          {log.model_name || '-'}
                        </span>
                      </td>

                      {/* Object */}
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-700 dark:text-gray-300 truncate max-w-[200px] block" title={log.object_repr}>
                          {log.object_repr || '-'}
                        </span>
                      </td>

                      {/* IP */}
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 px-2 py-1 rounded" dir="ltr">
                          {log.ip_address || '-'}
                        </span>
                      </td>

                      {/* Expand toggle */}
                      <td className="px-4 py-3 text-center">
                        {changes && (
                          <button
                            onClick={() => setExpandedRow(isExpanded ? null : log.id)}
                            className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-riadah-50 dark:hover:bg-riadah-900/30 hover:text-accent-500 dark:hover:text-accent-400 rounded-lg transition-colors"
                            title={t('details')}
                          >
                            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Expanded diff view */}
            {logs.map((log) => {
              const changes = formatChanges(log.changes);
              if (!changes || expandedRow !== log.id) return null;

              let parsedChanges;
              if (typeof changes === 'object' && changes !== null) {
                parsedChanges = changes;
              } else if (typeof changes === 'string') {
                try {
                  parsedChanges = JSON.parse(changes);
                } catch {
                  return null;
                }
              } else {
                return null;
              }

              return (
                <div key={`diff-${log.id}`} className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 px-6 py-4">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t('details')}</span>
                  </div>
                  {typeof parsedChanges === 'object' && !Array.isArray(parsedChanges) ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Old values */}
                      {parsedChanges.old && Object.keys(parsedChanges.old).length > 0 && (
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                          <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">{t('details')}</h4>
                          <div className="space-y-1.5">
                            {Object.entries(parsedChanges.old).map(([key, value]) => (
                              <div key={key} className="flex items-start gap-2 text-sm">
                                <span className="text-red-500 dark:text-red-400 font-medium min-w-[100px]">{key}:</span>
                                <span className="text-red-800 dark:text-red-300 line-through">
                                  {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value ?? '-')}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* New values */}
                      {parsedChanges.new && Object.keys(parsedChanges.new).length > 0 && (
                        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                          <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">{t('details')}</h4>
                          <div className="space-y-1.5">
                            {Object.entries(parsedChanges.new).map(([key, value]) => (
                              <div key={key} className="flex items-start gap-2 text-sm">
                                <span className="text-green-600 dark:text-green-400 font-medium min-w-[100px]">{key}:</span>
                                <span className="text-green-800 dark:text-green-300">
                                  {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value ?? '-')}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : Array.isArray(parsedChanges) ? (
                    <div className="space-y-2">
                      {parsedChanges.map((change, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm bg-white dark:bg-gray-800 rounded-lg p-2 border border-gray-200 dark:border-gray-700">
                          <span className="text-gray-500 dark:text-gray-400 font-medium">{change.field || `${t('description')} ${i + 1}`}:</span>
                          {change.old !== undefined && (
                            <span className="text-red-600 dark:text-red-400 line-through">{String(change.old)}</span>
                          )}
                          <span className="text-gray-400 dark:text-gray-500 mx-1">→</span>
                          {change.new !== undefined && (
                            <span className="text-green-600 dark:text-green-400">{String(change.new)}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 overflow-x-auto" dir="ltr">
                      {JSON.stringify(parsedChanges, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} / {totalCount}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => fetchLogs(currentPage - 1)}
                disabled={currentPage <= 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-600 dark:text-gray-400"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/30 rounded-lg">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => fetchLogs(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-600 dark:text-gray-400"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Clear logs confirmation modal */}
      {showClearModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowClearModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('clearOldLogs')}</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {t('confirm')}
              </p>

              {/* Days selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('days')}
                </label>
                <select
                  value={clearDays}
                  onChange={(e) => setClearDays(Number(e.target.value))}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
                >
                  <option value={7}>7 {t('days')}</option>
                  <option value={14}>14 {t('days')}</option>
                  <option value={30}>30 {t('days')}</option>
                  <option value={60}>60 {t('days')}</option>
                  <option value={90}>90 {t('days')}</option>
                  <option value={180}>180 {t('days')}</option>
                  <option value={365}>365 {t('days')}</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {clearDays} {t('days')}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleClearLogs}
                  disabled={clearLoading}
                  className="flex-1 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {clearLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</>
                  ) : (
                    <><Trash2 className="w-4 h-4" /> {t('confirm')}</>
                  )}
                </button>
                <button
                  onClick={() => setShowClearModal(false)}
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
