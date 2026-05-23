/**
 * Chart of Accounts page - displays all financial accounts.
 * Allows viewing, creating, updating, deleting accounts and Excel export (accountant/admin only).
 * Supports detail view, pagination, soft-delete, dark mode, and i18n (RTL Arabic/English).
 */

import { useState, useEffect, useCallback } from 'react';
import { accountsAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Search, Plus, Edit2, X, BookOpen, ChevronDown, ChevronLeft, Filter,
  Trash2, Eye, Download,
} from 'lucide-react';

export default function ChartOfAccountsPage() {
  const { t, locale } = useI18n();
  const { user } = useAuth();
  const isAccountant = user?.role === 'admin' || user?.role === 'accountant';

  const ACCOUNT_TYPE_LABELS = {
    asset: t('asset'),
    liability: t('liability'),
    equity: t('equity'),
    income: t('revenue'),
    expense: t('expense'),
  };

  const ACCOUNT_TYPE_COLORS = {
    asset: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
    liability: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    equity: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    income: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    expense: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  };

  /* ── state ── */
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [expandedAccounts, setExpandedAccounts] = useState(new Set());
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  /* ── detail modal ── */
  const [showDetail, setShowDetail] = useState(false);
  const [detailAccount, setDetailAccount] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  /* ── confirm dialog ── */
  const [confirmAction, setConfirmAction] = useState(null);

  const [form, setForm] = useState({
    code: '', name: '', name_en: '', account_type: 'asset', parent: '', description: '',
  });

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (filterType) params.account_type = filterType;
      const res = await accountsAPI.list(params);
      setAccounts(res.data.results || res.data);
      setTotalCount(res.data.count || (res.data.results || res.data).length);
    } catch {
      toast.error(t('errorLoadingAccounts'));
    } finally {
      setLoading(false);
    }
  }, [search, filterType, page, t]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // Reset page when search or filter changes
  useEffect(() => {
    setPage(1);
  }, [search, filterType]);

  // ──────────────────────── Helpers ────────────────────────

  const formatAmount = (val) =>
    Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', {
      minimumFractionDigits: 2,
    });

  const toggleExpand = (id) => {
    setExpandedAccounts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ──────────────────────── Create / Edit ────────────────────────

  const openCreate = () => {
    setEditingAccount(null);
    setForm({ code: '', name: '', name_en: '', account_type: 'asset', parent: '', description: '' });
    setShowModal(true);
  };

  const openEdit = (account) => {
    setEditingAccount(account);
    setForm({
      code: account.code,
      name: account.name,
      name_en: account.name_en || '',
      account_type: account.account_type,
      parent: account.parent || '',
      description: account.description || '',
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {
        code: form.code,
        name: form.name,
        name_en: form.name_en,
        account_type: form.account_type,
        parent: form.parent || null,
        description: form.description,
      };
      if (editingAccount) {
        const { code, ...updateData } = data;
        await accountsAPI.update(editingAccount.id, updateData);
        toast.success(t('accountUpdated'));
      } else {
        await accountsAPI.create(data);
        toast.success(t('accountCreated'));
      }
      setShowModal(false);
      fetchAccounts();
    } catch (err) {
      const msg =
        err.response?.data?.code?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.error ||
        t('errorSavingAccount');
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // ──────────────────────── Detail View ────────────────────────

  const openDetail = async (account) => {
    try {
      setDetailLoading(true);
      setDetailAccount(null);
      setShowDetail(true);
      const res = await accountsAPI.get(account.id);
      setDetailAccount(res.data);
    } catch {
      toast.error(t('errorLoadingAccounts'));
      setShowDetail(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // ──────────────────────── Delete / Deactivate ────────────────────────

  const handleDelete = async () => {
    if (!confirmAction?.account) return;
    try {
      await accountsAPI.delete(confirmAction.account.id);
      toast.success(t('accountDeleted'));
      fetchAccounts();
    } catch {
      toast.error(t('errorSavingAccount'));
    } finally {
      setConfirmAction(null);
    }
  };

  // ──────────────────────── Excel Export ────────────────────────

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.accounts();
      downloadBlob(new Blob([response.data]), 'accounts.xlsx');
      toast.success(t('dataExported'));
    } catch {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('chartOfAccounts')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('manageCompanyAccounts')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            {exporting ? t('exporting') : t('exportExcel')}
          </button>
          {isAccountant && (
            <button
              onClick={openCreate}
              className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm"
            >
              <Plus className="w-5 h-5" />
              {t('addAccount')}
            </button>
          )}
        </div>
      </div>

      {/* ── Search & Filter ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder={t('searchAccounts')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
            >
              <option value="">{t('allTypes')}</option>
              {Object.entries(ACCOUNT_TYPE_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ── Accounts Table ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 dark:text-gray-500">{t('loading')}</div>
        ) : accounts.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">{t('noAccounts')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">{t('accountCode')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('accountName')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('type')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('balance')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                  {(isAccountant || true) && (
                    <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {accounts.map((account) => (
                  <tr
                    key={account.id}
                    className={`border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${
                      !account.is_active ? 'opacity-60' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">
                      {account.code}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {account.has_children && (
                          <button
                            onClick={() => toggleExpand(account.id)}
                            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
                          >
                            {expandedAccounts.has(account.id) ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronLeft className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {account.name}
                        </span>
                      </div>
                      {account.name_en && (
                        <span className="text-xs text-gray-400 dark:text-gray-500 block">
                          {account.name_en}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          ACCOUNT_TYPE_COLORS[account.account_type] ||
                          'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {ACCOUNT_TYPE_LABELS[account.account_type] || account.account_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                      {formatAmount(account.current_balance)} {t('currency')}
                    </td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1.5">
                        <span
                          className={`w-2 h-2 rounded-full inline-block ${
                            account.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                          }`}
                        />
                        <span
                          className={`text-xs font-medium ${
                            account.is_active
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-gray-500 dark:text-gray-400'
                          }`}
                        >
                          {account.is_active ? t('active') : t('inactive')}
                        </span>
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {/* View */}
                        <button
                          onClick={() => openDetail(account)}
                          title={t('accountDetails')}
                          className="text-gray-500 dark:text-gray-400 hover:text-riadah-600 dark:hover:text-riadah-400 p-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {/* Edit */}
                        {isAccountant && (
                          <button
                            onClick={() => openEdit(account)}
                            title={t('editAccount')}
                            className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                        {/* Delete (only for active accounts) */}
                        {isAccountant && account.is_active === true && (
                          <button
                            onClick={() =>
                              setConfirmAction({ type: 'delete', account })
                            }
                            title={t('deleteAccount')}
                            className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
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
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-colors"
          >
            {t('previous')}
          </button>
          <span className="px-3 py-2 text-sm text-gray-600 dark:text-gray-300">
            {t('page')} {page}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={accounts.length < 20}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-colors"
          >
            {t('next')}
          </button>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Create / Edit Modal
         ═══════════════════════════════════════════════════════════ */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingAccount ? t('editAccount') : t('addAccount')}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('accountCode')} *
                </label>
                <input
                  type="text"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  disabled={!!editingAccount}
                  placeholder={t('codeExample')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none disabled:bg-gray-50 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('accountNameAr')} *
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder={t('accountNameArPlaceholder')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('accountNameEn')}
                </label>
                <input
                  type="text"
                  value={form.name_en}
                  onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                  placeholder={t('accountNameEnPlaceholder')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  dir="ltr"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('accountType')} *
                </label>
                <select
                  value={form.account_type}
                  onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                >
                  {Object.entries(ACCOUNT_TYPE_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('parentAccount')}
                </label>
                <select
                  value={form.parent}
                  onChange={(e) => setForm({ ...form, parent: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                >
                  <option value="">{t('noParentAccount')}</option>
                  {accounts
                    .filter(
                      (a) =>
                        a.account_type === form.account_type &&
                        a.id !== editingAccount?.id
                    )
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.code} - {a.name}
                      </option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('description')}
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder={t('accountDescriptionPlaceholder')}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? t('saving') : editingAccount ? t('save') : t('create')}
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

      {/* ═══════════════════════════════════════════════════════════
          Detail Modal
         ═══════════════════════════════════════════════════════════ */}
      {showDetail && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowDetail(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {detailLoading ? (
              <div className="p-12 text-center text-gray-400 dark:text-gray-500">
                <span className="w-8 h-8 border-2 border-gray-300 dark:border-gray-600 border-t-riadah-500 rounded-full animate-spin inline-block" />
                <p className="mt-3">{t('loading')}</p>
              </div>
            ) : detailAccount ? (
              <>
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-riadah-500" />
                    {detailAccount.name}
                  </h3>
                  <button
                    onClick={() => setShowDetail(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="p-5 space-y-5">
                  {/* Info Grid */}
                  <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('accountCode')}</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100 font-mono">
                        {detailAccount.code}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('type')}</span>
                      <p className="font-medium mt-0.5">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            ACCOUNT_TYPE_COLORS[detailAccount.account_type] ||
                            'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {ACCOUNT_TYPE_LABELS[detailAccount.account_type] ||
                            detailAccount.account_type}
                        </span>
                      </p>
                    </div>
                    {detailAccount.name_en && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">{t('accountNameEn')}</span>
                        <p className="font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                          {detailAccount.name_en}
                        </p>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('balance')}</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {formatAmount(detailAccount.current_balance)} {t('currency')}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('status')}</span>
                      <p className="font-medium mt-0.5">
                        <span className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full inline-block ${
                              detailAccount.is_active
                                ? 'bg-green-500'
                                : 'bg-gray-300 dark:bg-gray-600'
                            }`}
                          />
                          <span
                            className={`text-xs font-medium ${
                              detailAccount.is_active
                                ? 'text-green-600 dark:text-green-400'
                                : 'text-gray-500 dark:text-gray-400'
                            }`}
                          >
                            {detailAccount.is_active ? t('active') : t('inactive')}
                          </span>
                        </span>
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">{t('parentAccount')}</span>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {detailAccount.parent_name || t('noParentAccount')}
                      </p>
                    </div>
                  </div>

                  {/* Description */}
                  {detailAccount.description && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
                        {t('description')}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {detailAccount.description}
                      </p>
                    </div>
                  )}

                  {/* Children Accounts */}
                  {detailAccount.children && detailAccount.children.length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">
                        {t('childrenAccounts')}
                      </h4>
                      <div className="space-y-2">
                        {detailAccount.children.map((child) => (
                          <div
                            key={child.id}
                            className="flex items-center justify-between text-sm bg-white dark:bg-gray-800 rounded-lg px-3 py-2 border border-gray-100 dark:border-gray-600"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-gray-500 dark:text-gray-400 text-xs">
                                {child.code}
                              </span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {child.name}
                              </span>
                            </div>
                            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                              {formatAmount(child.current_balance)} {t('currency')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {isAccountant && (
                    <div className="flex gap-3 pt-2 border-t dark:border-gray-700">
                      <button
                        onClick={() => {
                          setShowDetail(false);
                          openEdit(detailAccount);
                        }}
                        className="flex-1 px-4 py-2.5 bg-accent-500 dark:bg-accent-600 text-white rounded-lg hover:bg-accent-600 dark:hover:bg-accent-700 transition-colors font-medium flex items-center justify-center gap-2"
                      >
                        <Edit2 className="w-4 h-4" />
                        {t('editAccount')}
                      </button>
                      {detailAccount.is_active && (
                        <button
                          onClick={() => {
                            setShowDetail(false);
                            setConfirmAction({ type: 'delete', account: detailAccount });
                          }}
                          className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium flex items-center justify-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          {t('deleteAccount')}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="p-12 text-center">
                <p className="text-gray-500 dark:text-gray-400">{t('noData')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Delete Confirmation Dialog
         ═══════════════════════════════════════════════════════════ */}
      {confirmAction && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-[60] p-4"
          onClick={() => setConfirmAction(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 text-center">
              {/* Icon */}
              <div className="mx-auto w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
                <Trash2 className="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>

              {/* Message */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {t('confirmDelete')}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {t('confirmDeleteMsg')}
                </p>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-2">
                  {confirmAction.account.name}
                  <span className="text-gray-400 dark:text-gray-500 font-mono mr-2">
                    ({confirmAction.account.code})
                  </span>
                </p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setConfirmAction(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  {t('cancel')}
                </button>
                <button
                  onClick={handleDelete}
                  className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
                >
                  {t('delete')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
