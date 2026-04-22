/**
 * Journal Entries page - create and manage accounting journal entries.
 * Supports creating entries with multiple debit/credit lines (double-entry).
 */

import { useState, useEffect } from 'react';
import { journalEntriesAPI, accountsAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import {
  Search, Plus, X, FileText, Check, Ban, Eye,
  Filter, AlertCircle, ArrowLeftRight,
} from 'lucide-react';

export default function JournalEntriesPage() {
  const { t, locale } = useI18n();

  const ENTRY_TYPE_LABELS = {
    manual: t('manual'),
    sale: t('saleTransaction'),
    payment: t('paymentTransaction'),
    adjustment: t('adjustment'),
  };

  const ENTRY_TYPE_COLORS = {
    manual: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    sale: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    payment: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
    adjustment: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  };

  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterPosted, setFilterPosted] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [postingId, setPostingId] = useState(null);

  const userRole = JSON.parse(localStorage.getItem('user') || '{}')?.role;
  const canManage = userRole === 'admin' || userRole === 'accountant';

  // Form state for creating entry
  const [entryForm, setEntryForm] = useState({
    description: '', reference: '', entry_date: new Date().toISOString().split('T')[0], entry_type: 'manual',
  });
  const [transactions, setTransactions] = useState([
    { account: '', transaction_type: 'debit', amount: '', description: '' },
    { account: '', transaction_type: 'credit', amount: '', description: '' },
  ]);

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (filterType) params.entry_type = filterType;
      if (filterPosted) params.is_posted = filterPosted;
      const res = await journalEntriesAPI.list(params);
      setEntries(res.data.results || res.data);
      setTotalCount(res.data.count || entries.length);
    } catch {
      toast.error(t('errorLoadingEntries'));
    } finally {
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await accountsAPI.list({ page_size: 200 });
      setAccounts(res.data.results || res.data);
    } catch {
      // Accounts may not load, modal will handle
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [search, filterType, filterPosted, page]);

  const openCreate = () => {
    fetchAccounts();
    setEntryForm({ description: '', reference: '', entry_date: new Date().toISOString().split('T')[0], entry_type: 'manual' });
    setTransactions([
      { account: '', transaction_type: 'debit', amount: '', description: '' },
      { account: '', transaction_type: 'credit', amount: '', description: '' },
    ]);
    setShowCreateModal(true);
  };

  const openDetail = async (entry) => {
    try {
      const res = await journalEntriesAPI.get(entry.id);
      setSelectedEntry(res.data);
      setShowDetailModal(true);
    } catch {
      toast.error(t('errorLoadingEntryDetails'));
    }
  };

  const addTransactionLine = () => {
    setTransactions([...transactions, { account: '', transaction_type: 'debit', amount: '', description: '' }]);
  };

  const removeTransactionLine = (index) => {
    if (transactions.length <= 2) {
      toast.error(t('minTwoTransactions'));
      return;
    }
    setTransactions(transactions.filter((_, i) => i !== index));
  };

  const updateTransaction = (index, field, value) => {
    const updated = [...transactions];
    updated[index][field] = value;
    setTransactions(updated);
  };

  const totalDebit = transactions.filter(t => t.transaction_type === 'debit').reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
  const totalCredit = transactions.filter(t => t.transaction_type === 'credit').reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
  const isBalanced = totalDebit > 0 && totalCredit > 0 && Math.abs(totalDebit - totalCredit) < 0.01;

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {
        ...entryForm,
        transactions: transactions.map(t => ({
          account: parseInt(t.account),
          transaction_type: t.transaction_type,
          amount: parseFloat(t.amount),
          description: t.description,
        })),
      };
      await journalEntriesAPI.create(data);
      toast.success(t('entryCreated'));
      setShowCreateModal(false);
      fetchEntries();
    } catch (err) {
      const msg = err.response?.data?.non_field_errors?.[0] || err.response?.data?.transactions?.[0] || t('errorCreatingEntry');
      toast.error(Array.isArray(msg) ? msg[0] : msg);
    } finally {
      setSaving(false);
    }
  };

  const handlePost = async (id) => {
    setPostingId(id);
    try {
      await journalEntriesAPI.post(id);
      toast.success(t('entryPosted'));
      fetchEntries();
      if (selectedEntry?.id === id) {
        const res = await journalEntriesAPI.get(id);
        setSelectedEntry(res.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || t('errorPostingEntry'));
    } finally {
      setPostingId(null);
    }
  };

  const handleReverse = async (id) => {
    if (!confirm(t('confirmReverseEntry'))) return;
    try {
      await journalEntriesAPI.reverse(id);
      toast.success(t('entryReversed'));
      fetchEntries();
      if (selectedEntry?.id === id) {
        const res = await journalEntriesAPI.get(id);
        setSelectedEntry(res.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || t('errorReversingEntry'));
    }
  };

  const formatAmount = (val) => Number(val || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('journalEntries')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageJournalEntries')}</p>
        </div>
        {canManage && (
          <button onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm">
            <Plus className="w-5 h-5" />
            {t('addEntry')}
          </button>
        )}
      </div>

      {/* Search & Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input type="text" placeholder={t('searchEntries')} value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
          </div>
          <select value={filterType} onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
            <option value="">{t('allTypes')}</option>
            {Object.entries(ENTRY_TYPE_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <select value={filterPosted} onChange={(e) => { setFilterPosted(e.target.value); setPage(1); }}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
            <option value="">{t('allStatuses')}</option>
            <option value="true">{t('posted')}</option>
            <option value="false">{t('draft')}</option>
          </select>
        </div>
      </div>

      {/* Entries Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 dark:text-gray-500">{t('loading')}</div>
        ) : entries.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">{t('noEntries')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">{t('entryNumber')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('description')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('type')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('date')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('debit')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('credit')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">{entry.entry_number}</td>
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100 max-w-xs truncate">{entry.description}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ENTRY_TYPE_COLORS[entry.entry_type] || 'bg-gray-100 dark:bg-gray-700'}`}>
                        {ENTRY_TYPE_LABELS[entry.entry_type] || entry.entry_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{entry.entry_date}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{formatAmount(entry.total_debit)}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{formatAmount(entry.total_credit)}</td>
                    <td className="px-4 py-3">
                      {entry.is_posted ? (
                        <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-xs font-medium">
                          <Check className="w-4 h-4" /> {t('posted')}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-orange-600 dark:text-orange-400 text-xs font-medium">
                          <AlertCircle className="w-4 h-4" /> {t('draft')}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => openDetail(entry)}
                          className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        {canManage && !entry.is_posted && (
                          <button onClick={() => handlePost(entry.id)} disabled={postingId === entry.id}
                            className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/30 transition-colors disabled:opacity-50">
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        {canManage && entry.is_posted && (
                          <button onClick={() => handleReverse(entry.id)}
                            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors">
                            <Ban className="w-4 h-4" />
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

      {/* Pagination */}
      {totalCount > 20 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300">{t('previous')}</button>
          <span className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">{t('page')} {page}</span>
          <button onClick={() => setPage(page + 1)} disabled={entries.length < 20}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300">{t('next')}</button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('addNewEntry')}</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4">
              {/* Entry header fields */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('entryDescription')} *</label>
                  <input type="text" value={entryForm.description}
                    onChange={(e) => setEntryForm({ ...entryForm, description: e.target.value })}
                    placeholder={t('entryDescriptionPlaceholder')}
                    required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('reference')}</label>
                  <input type="text" value={entryForm.reference}
                    onChange={(e) => setEntryForm({ ...entryForm, reference: e.target.value })}
                    placeholder={t('referencePlaceholder')}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('entryDate')} *</label>
                  <input type="date" value={entryForm.entry_date}
                    onChange={(e) => setEntryForm({ ...entryForm, entry_date: e.target.value })}
                    required
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('entryType')}</label>
                  <select value={entryForm.entry_type}
                    onChange={(e) => setEntryForm({ ...entryForm, entry_type: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700">
                    {Object.entries(ENTRY_TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Transaction lines */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('transactions')} *</label>
                  <button type="button" onClick={addTransactionLine}
                    className="text-sm text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 font-medium flex items-center gap-1">
                    <Plus className="w-4 h-4" /> {t('addTransaction')}
                  </button>
                </div>
                <div className="space-y-2">
                  {transactions.map((txn, i) => (
                    <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <select value={txn.transaction_type}
                        onChange={(e) => updateTransaction(i, 'transaction_type', e.target.value)}
                        className="w-24 px-2 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-white outline-none">
                        <option value="debit">{t('debit')}</option>
                        <option value="credit">{t('credit')}</option>
                      </select>
                      <select value={txn.account}
                        onChange={(e) => updateTransaction(i, 'account', e.target.value)}
                        required
                        className="flex-1 px-2 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-white outline-none">
                        <option value="">{t('selectAccount')}</option>
                        {accounts.map(acc => (
                          <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                        ))}
                      </select>
                      <input type="number" step="0.01" min="0" value={txn.amount}
                        onChange={(e) => updateTransaction(i, 'amount', e.target.value)}
                        placeholder={t('amount')}
                        required
                        className="w-32 px-2 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg text-sm outline-none" />
                      {transactions.length > 2 && (
                        <button type="button" onClick={() => removeTransactionLine(i)}
                          className="text-red-400 dark:text-red-500 hover:text-red-600 dark:hover:text-red-400 p-1">
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                {/* Balance indicator */}
                <div className={`flex items-center justify-between mt-3 p-3 rounded-lg text-sm ${isBalanced ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'}`}>
                  <span>{t('debitTotal')}: <strong>{formatAmount(totalDebit)}</strong></span>
                  <ArrowLeftRight className="w-4 h-4" />
                  <span>{t('creditTotal')}: <strong>{formatAmount(totalCredit)}</strong></span>
                  <span className="font-bold">{isBalanced ? t('balanced') : `${t('difference')}: ${formatAmount(Math.abs(totalDebit - totalCredit))}`}</span>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving || !isBalanced}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium">
                  {saving ? t('saving') : t('createEntry')}
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

      {/* Detail Modal */}
      {showDetailModal && selectedEntry && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{selectedEntry.entry_number}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{selectedEntry.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${ENTRY_TYPE_COLORS[selectedEntry.entry_type]}`}>
                  {ENTRY_TYPE_LABELS[selectedEntry.entry_type]}
                </span>
                <button onClick={() => setShowDetailModal(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div><span className="text-gray-500 dark:text-gray-400">{t('date')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEntry.entry_date}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('reference')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEntry.reference || '-'}</p></div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('status')}:</span>
                  <p className={`font-medium ${selectedEntry.is_posted ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`}>
                    {selectedEntry.is_posted ? t('posted') : t('draft')}
                  </p>
                </div>
                <div><span className="text-gray-500 dark:text-gray-400">{t('createdBy')}:</span><p className="font-medium text-gray-900 dark:text-gray-100">{selectedEntry.created_by_name || '-'}</p></div>
              </div>

              {/* Transactions */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('transactions')}</h4>
                <table className="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-800/70">
                      <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{t('accountName')}</th>
                      <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{t('description')}</th>
                      <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{t('debit')}</th>
                      <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{t('credit')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedEntry.transactions?.map((txn) => (
                      <tr key={txn.id} className="border-t dark:border-gray-700">
                        <td className="px-3 py-2">
                          <span className="text-gray-600 dark:text-gray-400">{txn.account_code}</span> - <span className="text-gray-900 dark:text-gray-100">{txn.account_name}</span>
                        </td>
                        <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{txn.description || '-'}</td>
                        <td className="px-3 py-2 text-right font-medium text-gray-900 dark:text-gray-100">
                          {txn.transaction_type === 'debit' ? formatAmount(txn.amount) : '-'}
                        </td>
                        <td className="px-3 py-2 text-right font-medium text-gray-900 dark:text-gray-100">
                          {txn.transaction_type === 'credit' ? formatAmount(txn.amount) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 dark:bg-gray-800/70 font-bold">
                      <td colSpan={2} className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">{t('total')}</td>
                      <td className="px-3 py-2 text-right text-gray-900 dark:text-gray-100">{formatAmount(selectedEntry.total_debit)}</td>
                      <td className="px-3 py-2 text-right text-gray-900 dark:text-gray-100">{formatAmount(selectedEntry.total_credit)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {canManage && !selectedEntry.is_posted && (
                  <button onClick={() => handlePost(selectedEntry.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors text-sm font-medium">
                    <Check className="w-4 h-4" /> {t('postEntry')}
                  </button>
                )}
                {canManage && selectedEntry.is_posted && (
                  <button onClick={() => handleReverse(selectedEntry.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 dark:bg-red-700 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-800 transition-colors text-sm font-medium">
                    <Ban className="w-4 h-4" /> {t('reverseEntry')}
                  </button>
                )}
                <button onClick={() => setShowDetailModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
                  {t('close')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
