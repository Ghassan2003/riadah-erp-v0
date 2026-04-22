/**
 * Backup Page - Create and manage backups.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Database, Download, Upload, Trash2, Plus, RefreshCw,
  HardDrive, Shield, Clock, FileArchive, AlertTriangle,
  CheckCircle2, XCircle, Info,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { backupAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';

export default function BackupPage() {
  const { t, locale } = useI18n();
  const [backups, setBackups] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [notes, setNotes] = useState('');
  const [backupType, setBackupType] = useState('manual');

  const fetchData = useCallback(async () => {
    try {
      const [listRes, statsRes] = await Promise.all([
        backupAPI.list({ ordering: '-created_at' }),
        backupAPI.stats(),
      ]);
      setBackups(listRes.data.results || listRes.data);
      setStats(statsRes.data);
    } catch (err) {
      toast.error(t('error') + ': ' + (err.response?.data?.error || t('backupFailed')));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      await backupAPI.create({ notes, backup_type: backupType });
      toast.success(t('backupCreated'));
      setShowCreate(false);
      setNotes('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.error || t('backupFailed'));
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = async (backup) => {
    try {
      const res = await backupAPI.download(backup.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = backup.filename;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(t('downloadBackup'));
    } catch {
      toast.error(t('backupFailed'));
    }
  };

  const handleRestore = async (id) => {
    if (!confirm(t('restoreConfirm'))) return;
    setRestoring(id);
    try {
      await backupAPI.restore(id);
      toast.success(t('backupRestored'));
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.error || t('backupFailed'));
    } finally {
      setRestoring(null);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm(t('deleteBackup'))) return;
    try {
      await backupAPI.delete(id);
      toast.success(t('backupDeleted'));
      fetchData();
    } catch {
      toast.error(t('backupFailed'));
    }
  };

  const statusColors = {
    completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    restoring: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  };

  const statusLabels = {
    completed: t('completed') || 'completed',
    failed: t('failed') || 'failed',
    restoring: t('restoring') || 'restoring',
    pending: t('pending') || 'pending',
  };

  const typeLabels = {
    manual: t('manualBackup'),
    auto_daily: t('daily'),
    auto_weekly: t('weekly'),
    auto_monthly: t('monthly'),
  };

  if (loading) {
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
            <Database className="w-7 h-7 text-accent-500" />
            {t('backupTitle')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('backupDesc')}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            <RefreshCw className="w-4 h-4" /> {t('refresh')}
          </button>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors">
            <Plus className="w-4 h-4" /> {t('createBackup')}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-riadah-100 dark:bg-riadah-900/30 rounded-lg">
                <FileArchive className="w-5 h-5 text-accent-500 dark:text-accent-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalBackups')}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.total_backups?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('success')}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.completed_backups?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('error')}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.failed_backups?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <HardDrive className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('backupSize')}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.total_size_mb?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')} MB</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Backup Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('createBackup')}</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('backupType')}</label>
              <select value={backupType} onChange={(e) => setBackupType(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500">
                <option value="manual">{t('manualBackup')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg px-3 py-2 text-sm h-20 resize-none focus:ring-2 focus:ring-accent-500"
                placeholder={t('description')} />
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">{t('cancel')}</button>
              <button onClick={handleCreate} disabled={creating}
                className="px-4 py-2 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:opacity-50 flex items-center gap-2">
                {creating && <RefreshCw className="w-4 h-4 animate-spin" />}
                {t('createBackup')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backups Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/70">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Shield className="w-5 h-5" /> {t('backupTitle')}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800/70">
              <tr>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">#</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('name')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('type')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('status')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('backupSize')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('total')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('date')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {backups.length > 0 ? backups.map((backup, i) => (
                <tr key={backup.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{i + 1}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileArchive className="w-4 h-4 text-accent-500" />
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{backup.filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600 dark:text-gray-300">{typeLabels[backup.backup_type] || backup.backup_type}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${statusColors[backup.status]}`}>
                      {statusLabels[backup.status] || backup.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{backup.file_size_mb?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')} MB</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{backup.records_count?.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US')}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{backup.created_at}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {backup.file_exists && (
                        <button onClick={() => handleDownload(backup)} title={t('downloadBackup')}
                          className="p-1.5 text-accent-500 hover:bg-riadah-50 dark:hover:bg-riadah-900/30 rounded-lg transition-colors">
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                      {backup.status === 'completed' && backup.file_exists && (
                        <button onClick={() => handleRestore(backup.id)} disabled={restoring === backup.id}
                          title={t('restoreBackup')} className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-colors disabled:opacity-50">
                          {restoring === backup.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                        </button>
                      )}
                      <button onClick={() => handleDelete(backup.id)} title={t('delete')}
                        className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="8" className="px-4 py-12 text-center text-gray-400 dark:text-gray-500">
                    <Database className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>{t('noBackups')}</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warning */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-800 dark:text-amber-300">{t('restoreWarning')}</p>
          <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
            {t('restoreDesc')}
          </p>
        </div>
      </div>
    </div>
  );
}
