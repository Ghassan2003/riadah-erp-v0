/**
 * Chart of Accounts page - displays all financial accounts.
 * Allows viewing, creating, and updating accounts (accountant/admin only).
 */

import { useState, useEffect } from 'react';
import { accountsAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import {
  Search, Plus, Edit2, X, BookOpen, ChevronDown, ChevronLeft,
  Filter,
} from 'lucide-react';

export default function ChartOfAccountsPage() {
  const { t, locale } = useI18n();

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

  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [expandedAccounts, setExpandedAccounts] = useState(new Set());
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    code: '', name: '', name_en: '', account_type: 'asset', parent: '', description: '',
  });

  const userRole = JSON.parse(localStorage.getItem('user') || '{}')?.role;
  const canManage = userRole === 'admin' || userRole === 'accountant';

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (filterType) params.account_type = filterType;
      const res = await accountsAPI.list(params);
      setAccounts(res.data.results || res.data);
    } catch {
      toast.error(t('errorLoadingAccounts'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [search, filterType]);

  const toggleExpand = (id) => {
    setExpandedAccounts(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

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
        // Update: don't send code
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
      const msg = err.response?.data?.code?.[0] || err.response?.data?.non_field_errors?.[0] || err.response?.data?.error || t('errorSavingAccount');
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const formatAmount = (val) => Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('chartOfAccounts')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageCompanyAccounts')}</p>
        </div>
        {canManage && (
          <button onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm">
            <Plus className="w-5 h-5" />
            {t('addAccount')}
          </button>
        )}
      </div>

      {/* Search & Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input type="text" placeholder={t('searchAccounts')} value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
              <option value="">{t('allTypes')}</option>
              {Object.entries(ACCOUNT_TYPE_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Accounts Table */}
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
                  {canManage && <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {accounts.map((account) => (
                  <tr key={account.id}
                    className="border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">{account.code}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {account.has_children && (
                          <button onClick={() => toggleExpand(account.id)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
                            {expandedAccounts.has(account.id) ? <ChevronDown className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                          </button>
                        )}
                        <span className="font-medium text-gray-900 dark:text-gray-100">{account.name}</span>
                      </div>
                      {account.name_en && (
                        <span className="text-xs text-gray-400 dark:text-gray-500 block">{account.name_en}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ACCOUNT_TYPE_COLORS[account.account_type] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'}`}>
                        {ACCOUNT_TYPE_LABELS[account.account_type] || account.account_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                      {formatAmount(account.current_balance)} {t('currency')}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`w-2 h-2 rounded-full inline-block ${account.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                    </td>
                    {canManage && (
                      <td className="px-4 py-3">
                        <button onClick={() => openEdit(account)}
                          className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors">
                          <Edit2 className="w-4 h-4" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingAccount ? t('editAccount') : t('addNewAccount')}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('accountCode')} *</label>
                <input type="text" value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  disabled={!!editingAccount}
                  placeholder={t('codeExample')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none disabled:bg-gray-50 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('accountNameAr')} *</label>
                <input type="text" value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder={t('accountNameArPlaceholder')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('accountNameEn')}</label>
                <input type="text" value={form.name_en}
                  onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                  placeholder={t('accountNameEnPlaceholder')}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" dir="ltr" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('accountType')} *</label>
                <select value={form.account_type}
                  onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                  {Object.entries(ACCOUNT_TYPE_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('parentAccount')}</label>
                <select value={form.parent}
                  onChange={(e) => setForm({ ...form, parent: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                  <option value="">{t('noParentAccount')}</option>
                  {accounts.filter(a => a.account_type === form.account_type && a.id !== editingAccount?.id)
                    .map(a => (
                      <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
                <textarea value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder={t('accountDescriptionPlaceholder')}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium">
                  {saving ? t('saving') : editingAccount ? t('update') : t('create')}
                </button>
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium">
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
