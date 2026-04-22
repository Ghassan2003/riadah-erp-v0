/**
 * Error Log Page - Centralized error logging system.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle, AlertCircle, CheckCircle2, Bug, Filter,
  RefreshCw, XCircle, Info, Check, Trash2, Eye, ShieldAlert,
  Search,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { errorLogAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';

export default function ErrorLogPage() {
  const { t, locale } = useI18n();
  const [errors, setErrors] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ level: '', source: '', is_resolved: '', search: '' });
  const [selectedErrors, setSelectedErrors] = useState([]);
  const [showDetail, setShowDetail] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [resolveNotes, setResolveNotes] = useState('');
  const [showBatchResolve, setShowBatchResolve] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, ordering: '-created_at' };
      if (filters.level) params.level = filters.level;
      if (filters.source) params.source = filters.source;
      if (filters.is_resolved !== '') params.is_resolved = filters.is_resolved;
      if (filters.search) params.search = filters.search;

      const [listRes, statsRes] = await Promise.all([
        errorLogAPI.list(params),
        errorLogAPI.stats(),
      ]);
      const data = listRes.data;
      setErrors(data.results || data);
      setTotalPages(Math.ceil((data.count || 0) / 20));
      setStats(statsRes.data);
    } catch {
      toast.error(t('error') + ': ' + t('loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [page, filters, t]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleResolve = async (id) => {
    try {
      await errorLogAPI.resolve(id, { resolution_notes: resolveNotes });
      toast.success(t('errorResolved'));
      setShowDetail(null);
      setResolveNotes('');
      fetchData();
    } catch {
      toast.error(t('error') + ': ' + t('updateFailed'));
    }
  };

  const handleBatchResolve = async () => {
    if (selectedErrors.length === 0) {
      toast.error(t('noData'));
      return;
    }
    try {
      const res = await errorLogAPI.batchResolve({
        error_ids: selectedErrors,
        resolution_notes: resolveNotes,
      });
      toast.success(res.data.message);
      setShowBatchResolve(false);
      setSelectedErrors([]);
      setResolveNotes('');
      fetchData();
    } catch {
      toast.error(t('resolveAll') + ' ' + t('error').toLowerCase());
    }
  };

  const handleClearOld = async () => {
    if (!confirm(t('confirm'))) return;
    try {
      const res = await errorLogAPI.clear(30);
      toast.success(res.data.message);
      fetchData();
    } catch {
      toast.error(t('clearErrors') + ' ' + t('error').toLowerCase());
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const res = await errorLogAPI.detail(id);
      setDetailData(res.data);
      setShowDetail(id);
    } catch {
      toast.error(t('error') + ': ' + t('loadFailed'));
    }
  };

  const toggleSelect = (id) => {
    setSelectedErrors(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const levelIcons = {
    debug: <Info className="w-4 h-4 text-gray-500 dark:text-gray-400" />,
    info: <Info className="w-4 h-4 text-accent-500" />,
    warning: <AlertTriangle className="w-4 h-4 text-amber-500" />,
    error: <AlertCircle className="w-4 h-4 text-red-500" />,
    critical: <ShieldAlert className="w-4 h-4 text-red-700" />,
  };

  const levelColors = {
    debug: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    info: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
    warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    critical: 'bg-red-200 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  };

  const levelLabels = {
    debug: t('debug'), info: t('info'), warning: t('warning'), error: t('error'), critical: t('critical'),
  };

  const sourceLabels = {
    backend: t('backend'), frontend: t('frontend'), api: t('api'),
    cron: t('cronJobs'), backup: t('backup'), database: t('database'),
    auth: t('auth'), other: t('other'),
  };

  if (loading && errors.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Bug className="w-7 h-7 text-red-600" />
            {t('errorLogTitle')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('errorLogDesc')}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleClearOld} className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors text-sm">
            <Trash2 className="w-4 h-4" /> {t('clearErrors')}
          </button>
          {selectedErrors.length > 0 && (
            <button onClick={() => setShowBatchResolve(true)} className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors text-sm">
              <CheckCircle2 className="w-4 h-4" /> {t('resolveAll')} ({selectedErrors.length})
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: t('totalErrors'), value: stats.total, color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' },
            { label: t('unresolvedErrors'), value: stats.unresolved, color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' },
            { label: t('critical'), value: stats.critical_unresolved, color: 'bg-red-200 text-red-900 dark:bg-red-900/40 dark:text-red-200' },
            { label: t('error'), value: stats.errors_unresolved, color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' },
            { label: t('warning'), value: stats.warnings_unresolved, color: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300' },
            { label: t('recentWeek'), value: stats.recent_week, color: 'bg-riadah-100 text-riadah-800 dark:bg-riadah-900/30 dark:text-accent-300' },
          ].map((s, i) => (
            <div key={i} className={`${s.color} rounded-xl p-3 text-center`}>
              <p className="text-2xl font-bold">{s.value?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              <p className="text-xs mt-1 opacity-80">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Filter className="w-4 h-4" /> {t('filter')}:
          </div>
          <select value={filters.level} onChange={(e) => setFilters(f => ({ ...f, level: e.target.value }))}
            className="border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
            <option value="">{t('allLevels')}</option>
            <option value="critical">{t('critical')}</option>
            <option value="error">{t('error')}</option>
            <option value="warning">{t('warning')}</option>
            <option value="info">{t('info')}</option>
          </select>
          <select value={filters.source} onChange={(e) => setFilters(f => ({ ...f, source: e.target.value }))}
            className="border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
            <option value="">{t('allSources')}</option>
            <option value="backend">{t('backend')}</option>
            <option value="api">{t('api')}</option>
            <option value="cron">{t('cronJobs')}</option>
            <option value="backup">{t('backup')}</option>
            <option value="database">{t('database')}</option>
          </select>
          <select value={filters.is_resolved} onChange={(e) => setFilters(f => ({ ...f, is_resolved: e.target.value }))}
            className="border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
            <option value="">{t('all')}</option>
            <option value="false">{t('unresolved')}</option>
            <option value="true">{t('resolved')}</option>
          </select>
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input value={filters.search} onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
              placeholder={t('search')}
              className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg pr-9 pl-3 py-2 text-sm focus:ring-2 focus:ring-accent-500" />
          </div>
          <button onClick={() => setFilters({ level: '', source: '', is_resolved: '', search: '' })}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">{t('clear')}</button>
        </div>
      </div>

      {/* Errors Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800/70">
              <tr>
                <th className="px-4 py-3 text-right w-10">
                  <input type="checkbox" checked={selectedErrors.length === errors.length && errors.length > 0}
                    onChange={() => setSelectedErrors(selectedErrors.length === errors.length ? [] : errors.map(e => e.id))}
                    className="rounded" />
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('errorLevel')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('errorMessage')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('errorSource')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('path')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('status')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('date')}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {errors.length > 0 ? errors.map((error) => (
                <tr key={error.id} className={`hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${!error.is_resolved ? 'bg-red-50/30 dark:bg-red-900/10' : ''}`}>
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selectedErrors.includes(error.id)}
                      onChange={() => toggleSelect(error.id)} className="rounded" />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${levelColors[error.level]}`}>
                      {levelIcons[error.level]} {levelLabels[error.level]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm text-gray-900 dark:text-gray-100 truncate max-w-[300px]">{error.message}</p>
                    {error.code && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{error.code}</p>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{sourceLabels[error.source] || error.source}</td>
                  <td className="px-4 py-3 text-sm text-gray-400 dark:text-gray-500 truncate max-w-[150px]" title={error.url_path}>
                    {error.url_path || '-'}
                  </td>
                  <td className="px-4 py-3">
                    {error.is_resolved ? (
                      <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5" /> {t('resolved')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-600 dark:text-red-400 text-xs">
                        <XCircle className="w-3.5 h-3.5" /> {t('unresolved')}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{error.created_at}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button onClick={() => handleViewDetail(error.id)} title={t('details')}
                        className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      {!error.is_resolved && (
                        <button onClick={() => { setShowDetail(error.id); setDetailData(error); }}
                          title={t('resolveError')} className="p-1.5 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-colors">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="8" className="px-4 py-12 text-center text-gray-400 dark:text-gray-500">
                    <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-green-300 dark:text-green-600" />
                    <p>{t('noErrors')}</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg disabled:opacity-50">{t('previous')}</button>
            <span className="text-sm text-gray-600 dark:text-gray-400">{t('page')} {page} {t('of')} {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg disabled:opacity-50">{t('next')}</button>
          </div>
        )}
      </div>

      {/* Detail / Resolve Modal */}
      {showDetail && detailData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                {levelIcons[detailData.level]}
                {t('errorLogTitle')} #{detailData.id}
              </h3>
              <button onClick={() => { setShowDetail(null); setDetailData(null); }}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><XCircle className="w-5 h-5 text-gray-500 dark:text-gray-400" /></button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500 dark:text-gray-400">{t('errorLevel')}:</span> <span className={`px-2 py-0.5 rounded-full text-xs ${levelColors[detailData.level]}`}>{levelLabels[detailData.level]}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">{t('errorSource')}:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{sourceLabels[detailData.source]}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">{t('code')}:</span> <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-0.5 rounded">{detailData.code || '-'}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">{t('status')}:</span> {detailData.is_resolved ? <span className="text-green-600 dark:text-green-400">{t('resolved')}</span> : <span className="text-red-600 dark:text-red-400">{t('unresolved')}</span>}</div>
              <div><span className="text-gray-500 dark:text-gray-400">IP:</span> <span className="text-gray-900 dark:text-gray-100">{detailData.ip_address || '-'}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">{t('method')}:</span> <span className="text-gray-900 dark:text-gray-100">{detailData.request_method || '-'}</span></div>
              <div className="col-span-2"><span className="text-gray-500 dark:text-gray-400">{t('path')}:</span> <span className="font-mono text-xs text-gray-900 dark:text-gray-100">{detailData.url_path}</span></div>
              <div className="col-span-2"><span className="text-gray-500 dark:text-gray-400">{t('user')}:</span> <span className="text-gray-900 dark:text-gray-100">{detailData.user_name || '-'}</span></div>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{t('errorMessage')}:</p>
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-800 dark:text-red-300">{detailData.message}</div>
            </div>

            {detailData.stack_trace && (
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{t('stackTrace')}:</p>
                <pre className="bg-gray-900 text-green-400 rounded-lg p-3 text-xs overflow-x-auto max-h-40" dir="ltr">{detailData.stack_trace}</pre>
              </div>
            )}

            {!detailData.is_resolved && (
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700 space-y-3">
                <h4 className="font-medium text-gray-700 dark:text-gray-300">{t('resolveError')}</h4>
                <textarea value={resolveNotes} onChange={(e) => setResolveNotes(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg px-3 py-2 text-sm h-16 resize-none focus:ring-2 focus:ring-accent-500"
                  placeholder={t('addResolutionNotes')} />
                <div className="flex gap-2 justify-end">
                  <button onClick={() => { setShowDetail(null); setDetailData(null); }}
                    className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">{t('close')}</button>
                  <button onClick={() => handleResolve(detailData.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800">{t('resolveError')}</button>
                </div>
              </div>
            )}

            {detailData.is_resolved && (
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('resolutionNotes')}:</p>
                <p className="text-sm text-green-700 dark:text-green-400 mt-1">{detailData.resolution_notes || '-'}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">{t('resolvedBy')}: {detailData.resolved_by_name} - {detailData.resolved_at}</p>
                <div className="flex justify-end mt-3">
                  <button onClick={() => { setShowDetail(null); setDetailData(null); }}
                    className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">{t('close')}</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Batch Resolve Modal */}
      {showBatchResolve && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('resolveAll')} ({selectedErrors.length})</h3>
            <textarea value={resolveNotes} onChange={(e) => setResolveNotes(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg px-3 py-2 text-sm h-20 resize-none focus:ring-2 focus:ring-accent-500"
              placeholder={t('addResolutionNotes')} />
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowBatchResolve(false)} className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">{t('cancel')}</button>
              <button onClick={handleBatchResolve} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800">{t('resolveAll')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
