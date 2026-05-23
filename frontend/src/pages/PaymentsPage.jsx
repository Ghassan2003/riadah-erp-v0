/**
 * Payments Page – إدارة المدفوعات
 * Tabs: Transactions, Accounts, Cheques, Reconciliations
 * Uses real paymentsAPI for all operations.
 */
import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { paymentsAPI } from '../api';
import {
  Wallet, ArrowDownCircle, ArrowUpCircle, ArrowLeftRight, CreditCard,
  Plus, Search, Download, X, Building2, FileCheck, CheckSquare,
  Eye, Trash2, Edit3, Save, Loader2, ChevronLeft, ChevronRight,
  AlertTriangle, RefreshCw, Pencil,
} from 'lucide-react';
import toast from 'react-hot-toast';
/* eslint-disable react/prop-types */

// ─── Lookup Maps ──────────────────────────────────────────────────
const TYPE_MAP = {
  receipt:     ['قبض',   'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'],
  payment:     ['دفع',   'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  transfer:    ['تحويل', 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'],
  adjustment:  ['تسوية', 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
};

const TXN_STATUS = {
  completed: ['مكتمل', 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'],
  pending:   ['معلق', 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
  cancelled: ['ملغي',  'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
};

const CHEQUE_STATUS = {
  received:  ['مستلم',  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'],
  deposited: ['مودع',  'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
  cleared:   ['مصروف', 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'],
  bounced:   ['مرتجع', 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  cancelled: ['ملغي',  'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
};

const RECON_STATUS = {
  draft:       ['مسودة', 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
  reconciled:  ['مطابق', 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'],
  discrepancy: ['فرق',   'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
};

const METHOD_MAP = {
  bank_transfer: 'تحويل بنكي',
  cash:          'نقدي',
  cheque:        'شيك',
  card:          'بطاقة',
  mobile:        'محفظة إلكترونية',
};

const ACCT_TYPE_MAP = {
  bank_account:  'حساب بنكي',
  cash_box:      'صندوق نقدي',
  mobile_wallet: 'محفظة إلكترونية',
};

const ACCT_TYPE_COLORS = {
  bank_account:  'from-riadah-400 to-riadah-500',
  cash_box:      'from-emerald-500 to-emerald-600',
  mobile_wallet: 'from-violet-500 to-violet-600',
};

// ─── Shared Helpers ───────────────────────────────────────────────
const badge = (map, key) => {
  const [label, cls] = map[key] || [key, ''];
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
};

const TH = 'text-right px-3 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap';

const inp = 'w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-500 transition';

// ─── Modal Component ─────────────────────────────────────────────
function Modal({ title, onClose, children, wide }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full ${wide ? 'max-w-2xl' : 'max-w-lg'} max-h-[90vh] overflow-y-auto`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-800 dark:text-white">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

// ─── Delete Confirmation ─────────────────────────────────────────
function DeleteConfirm({ message, onConfirm, loading, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={onCancel} />
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">تأكيد الحذف</h3>
          <p className="text-gray-600 dark:text-gray-300 mb-5">{message}</p>
          <div className="flex gap-3">
            <button onClick={onConfirm} disabled={loading} className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحذف...</> : <><Trash2 className="w-4 h-4" /> حذف</>}
            </button>
            <button onClick={onCancel} className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Empty State ─────────────────────────────────────────────────
function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-500">
      <Icon className="w-16 h-16 mb-3 opacity-40" />
      <p className="font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <p className="text-sm mt-1">{description}</p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════════════
export default function PaymentsPage() {
  const { t, locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const fmtInt = (v) => Number(v || 0).toLocaleString(nl);

  const [tab, setTab] = useState('transactions');
  const tabs = [
    { key: 'transactions',    label: t('payTransactions'),     icon: Wallet },
    { key: 'accounts',        label: t('payAccounts'),         icon: CreditCard },
    { key: 'cheques',         label: t('payCheques'),          icon: FileCheck },
    { key: 'reconciliations', label: t('payReconciliations'),  icon: CheckSquare },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
          <Wallet className="w-7 h-7" /> {t('payManagePayments')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('payManagePaymentsDesc')}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((tb) => (
          <button key={tb.key} onClick={() => setTab(tb.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === tb.key ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}>
            <tb.icon className="w-4 h-4" />{tb.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'transactions'    && <TransactionsTab t={t} fmt={fmt} fmtInt={fmtInt} />}
      {tab === 'accounts'        && <AccountsTab t={t} fmt={fmt} />}
      {tab === 'cheques'         && <ChequesTab t={t} fmt={fmt} />}
      {tab === 'reconciliations' && <ReconciliationsTab t={t} fmt={fmt} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// TAB 1 — Transactions
// ═══════════════════════════════════════════════════════════════════
function TransactionsTab({ t, fmt, fmtInt }) {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({});
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const ps = 20;
  const [exporting, setExporting] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);
  const [aLoading, setALoading] = useState(false);
  const [form, setForm] = useState({ type: 'receipt', account: '', to_account: '', amount: '', currency: 'SAR', customer: '', supplier: '', description: '', date: '', payment_method: 'bank_transfer', reference: '', reference_type: '', status: 'completed' });
  const [fLoading, setFLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const r = await paymentsAPI.getStats();
      setStats(r.data);
    } catch { toast.error(t('payLoadStatsFailed')); } finally { setStatsLoading(false); }
  }, [t]);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, search: search || undefined, type: typeFilter || undefined, status: statusFilter || undefined };
      const r = await paymentsAPI.getTransactions(params);
      const d = r.data;
      setTransactions(d.results || (Array.isArray(d) ? d : []));
      setTotal(d.count || d.length || 0);
      setPage(p);
    } catch { toast.error(t('payLoadTransactionsFailed')); } finally { setLoading(false); }
  }, [search, typeFilter, statusFilter, t]);

  const fetchAccounts = useCallback(async () => {
    try {
      const r = await paymentsAPI.getAccounts({ page_size: 200 });
      setAccounts(r.data.results || (Array.isArray(r.data) ? r.data : []));
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchStats(); fetch(1); fetchAccounts(); }, [fetchStats, fetch, fetchAccounts]);

  const handleExport = async () => {
    try {
      setExporting(true);
      const r = await paymentsAPI.export();
      const u = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'transactions.xlsx'; a.click(); a.remove();
      toast.success(t('dataExported'));
    } catch { toast.error(t('exportError')); } finally { setExporting(false); }
  };

  const openDetail = async (txn) => {
    setALoading(true);
    try {
      const r = await paymentsAPI.getTransaction(txn.id);
      setDetailData(r.data);
      setShowDetail(txn.id);
    } catch { toast.error(t('error')); } finally { setALoading(false); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try {
      await paymentsAPI.deleteTransaction(delConf.id);
      toast.success(t('payTransactionDeleted'));
      setDelConf(null);
      fetch(page);
      fetchStats();
    } catch (e) { toast.error(e.response?.data?.error || t('error')); } finally { setDelLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.account || !form.amount) { toast.error(t('required')); return; }
    setFLoading(true);
    try {
      const payload = { ...form, amount: Number(form.amount) };
      if (form.type !== 'transfer') delete payload.to_account;
      await paymentsAPI.createTransaction(payload);
      toast.success(t('payTransactionCreated'));
      setShowCreate(false);
      setForm({ type: 'receipt', account: '', to_account: '', amount: '', currency: 'SAR', customer: '', supplier: '', description: '', date: '', payment_method: 'bank_transfer', reference: '', reference_type: '', status: 'completed' });
      fetch(1);
      fetchStats();
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); } finally { setFLoading(false); }
  };

  const tp = Math.ceil(total / ps);
  const statCards = [
    [t('payTotalReceipts'), fmtInt(stats.total_receipts), ArrowDownCircle, 'from-emerald-500 to-emerald-600'],
    [t('payTotalPayments'), fmtInt(stats.total_payments), ArrowUpCircle, 'from-red-500 to-red-600'],
    [t('payTransfers'), fmtInt(stats.total_transfers), ArrowLeftRight, 'from-riadah-400 to-riadah-500'],
    [t('payAccountBalances'), fmtInt(stats.account_balances), CreditCard, 'from-violet-500 to-violet-600'],
  ];

  const ths = [t('payTransactionNumber'), t('payTransactionType'), t('payAccount'), t('payAmount'), t('payTransactionDate'), t('payPaymentMethod'), t('payReference'), t('payDescription'), t('status'), t('payActions')];

  return (
    <div className="space-y-4">
      {/* Stats */}
      {statsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{[...Array(4)].map((_, i) => <div key={i} className="h-24 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />)}</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {statCards.map(([label, value, Icon, gradient], i) => (
            <div key={i} className={`bg-gradient-to-br ${gradient} rounded-xl p-4 text-white shadow-lg`}>
              <div className="flex items-center justify-between mb-2"><Icon className="w-5 h-5 opacity-80" /><span className="text-xs opacity-80">{label}</span></div>
              <p className="text-xl font-bold">{value ?? '—'}</p>
            </div>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button onClick={() => { setSearch(''); setTypeFilter(''); setStatusFilter(''); setPage(1); }} className="text-sm text-gray-500 hover:text-accent-500 dark:text-gray-400 dark:hover:text-accent-400">{t('clearSearch')}</button>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} {t('exportExcel')}
          </button>
          <button onClick={() => setShowCreate(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
            <Plus className="w-4 h-4" /> {t('payNewTransaction')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder={t('paySearchTransactions')} className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm focus:ring-2 focus:ring-accent-500" />
        </div>
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">{t('payAllTypes')}</option>{Object.entries(TYPE_MAP).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">{t('payAllStatuses')}</option>{Object.entries(TXN_STATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
        ) : transactions.length === 0 ? (
          <EmptyState icon={Wallet} title={t('payNoTransactions')} description={t('payStartAdding')} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{ths.map((h) => <th key={h} className={TH}>{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {transactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-3 py-2.5"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300 bg-riadah-50 dark:bg-riadah-900/30 px-2 py-0.5 rounded">{txn.transaction_number}</span></td>
                    <td className="px-3 py-2.5">{badge(TYPE_MAP, txn.type)}</td>
                    <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100">{txn.account_name || '—'}</td>
                    <td className={`px-3 py-2.5 text-sm font-semibold ${txn.type === 'receipt' ? 'text-emerald-600 dark:text-emerald-400' : txn.type === 'payment' ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`} dir="ltr">
                      {txn.type === 'receipt' ? '+' : txn.type === 'payment' ? '-' : ''}{fmt(txn.amount)}
                    </td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{txn.date}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{METHOD_MAP[txn.payment_method] || txn.payment_method || '—'}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-500">{txn.reference || '—'}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300 max-w-[150px] truncate">{txn.description || '—'}</td>
                    <td className="px-3 py-2.5">{badge(TXN_STATUS, txn.status)}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1">
                        <button onClick={() => openDetail(txn)} className="p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" title={t('view')}><Eye className="w-4 h-4" /></button>
                        <button onClick={() => setDelConf(txn)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title={t('delete')}><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {tp > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">{((page - 1) * ps) + 1} - {Math.min(page * ps, total)} {t('of')} {total}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetch(page - 1)} disabled={page <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">{page} / {tp}</span>
              <button onClick={() => fetch(page + 1)} disabled={page >= tp} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <Modal title={t('payNewTransaction')} onClose={() => setShowCreate(false)} wide>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payTransactionType')} <span className="text-red-500">*</span></label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  {Object.entries(TYPE_MAP).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccount')} <span className="text-red-500">*</span></label>
                <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required>
                  <option value="">{t('search')}...</option>
                  {accounts.map((a) => <option key={a.id} value={a.id}>{a.account_name}</option>)}
                </select>
              </div>
            </div>
            {form.type === 'transfer' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payToAccount')}</label>
                <select value={form.to_account} onChange={(e) => setForm({ ...form, to_account: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  <option value="">{t('search')}...</option>
                  {accounts.filter((a) => String(a.id) !== form.account).map((a) => <option key={a.id} value={a.id}>{a.account_name}</option>)}
                </select>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAmount')} <span className="text-red-500">*</span></label>
                <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payCurrency')}</label>
                <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  <option value="SAR">SAR</option><option value="USD">USD</option><option value="EUR">EUR</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payTransactionDate')}</label>
                <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payPaymentMethod')}</label>
                <select value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  {Object.entries(METHOD_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payCustomer')}</label>
                <input value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paySupplier')}</label>
                <input value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payReference')}</label>
                <input value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payReferenceType')}</label>
                <input value={form.reference_type} onChange={(e) => setForm({ ...form, reference_type: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payDescription')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm resize-none" rows={2} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('status')}</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                {Object.entries(TXN_STATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}</> : <><Save className="w-4 h-4" /> {t('create')}</>}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Detail Modal */}
      {showDetail && detailData && (
        <Modal title={`${t('payTransactionDetails')} — ${detailData.transaction_number}`} onClose={() => { setShowDetail(null); setDetailData(null); }} wide>
          <div className="space-y-4 max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                [t('payTransactionType'), badge(TYPE_MAP, detailData.type)],
                [t('payAccount'), detailData.account_name || '—'],
                [t('payToAccount'), detailData.to_account_name || '—'],
                [t('payAmount'), fmt(detailData.amount)],
                [t('payCurrency'), detailData.currency || 'SAR'],
                [t('payTransactionDate'), detailData.date || '—'],
                [t('payPaymentMethod'), METHOD_MAP[detailData.payment_method] || '—'],
                [t('payReference'), detailData.reference || '—'],
                [t('payReferenceType'), detailData.reference_type || '—'],
                [t('payCustomer'), detailData.customer || '—'],
                [t('paySupplier'), detailData.supplier || '—'],
                [t('status'), badge(TXN_STATUS, detailData.status)],
              ].map(([label, value], i) => (
                <div key={i} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{label}</p>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{value}</p>
                </div>
              ))}
            </div>
            {detailData.description && (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{t('payDescription')}</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">{detailData.description}</p>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <DeleteConfirm message={`${t('payDeleteTransaction')} (${delConf.transaction_number})?`} onConfirm={handleDelete} loading={delLoading} onCancel={() => setDelConf(null)} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// TAB 2 — Accounts
// ═══════════════════════════════════════════════════════════════════
function AccountsTab({ t, fmt }) {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editAcct, setEditAcct] = useState(null);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);
  const [fLoading, setFLoading] = useState(false);
  const emptyForm = { account_name: '', account_type: 'bank_account', bank_name: '', account_number: '', iban: '', currency: 'SAR', is_default: false };
  const [form, setForm] = useState({ ...emptyForm });

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const r = await paymentsAPI.getAccounts();
      setAccounts(r.data.results || (Array.isArray(r.data) ? r.data : []));
    } catch { toast.error(t('payLoadAccountsFailed')); } finally { setLoading(false); }
  }, [t]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.account_name) { toast.error(t('required')); return; }
    setFLoading(true);
    try {
      await paymentsAPI.createAccount({ ...form, is_default: form.is_default || false });
      toast.success(t('payAccountCreated'));
      setShowCreate(false);
      setForm({ ...emptyForm });
      fetch();
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); } finally { setFLoading(false); }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editAcct) return;
    setFLoading(true);
    try {
      await paymentsAPI.updateAccount(editAcct.id, form);
      toast.success(t('payAccountUpdated'));
      setEditAcct(null);
      setForm({ ...emptyForm });
      fetch();
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); } finally { setFLoading(false); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try {
      await paymentsAPI.deleteAccount(delConf.id);
      toast.success(t('payAccountDeleted'));
      setDelConf(null);
      fetch();
    } catch (e) { toast.error(e.response?.data?.error || t('error')); } finally { setDelLoading(false); }
  };

  const openEdit = (acct) => {
    setEditAcct(acct);
    setForm({ account_name: acct.account_name, account_type: acct.account_type, bank_name: acct.bank_name || '', account_number: acct.account_number || '', iban: acct.iban || '', currency: acct.currency || 'SAR', is_default: acct.is_default || false });
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => { setForm({ ...emptyForm }); setShowCreate(true); }} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
          <Plus className="w-4 h-4" /> {t('payNewAccount')}
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
      ) : accounts.length === 0 ? (
        <EmptyState icon={CreditCard} title={t('payNoAccounts')} description={t('payStartAddingAccounts')} />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((acct) => (
            <div key={acct.id} className={`relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br ${ACCT_TYPE_COLORS[acct.account_type] || 'from-gray-500 to-gray-600'} text-white shadow-lg`}>
              <div className="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-full -translate-x-12 -translate-y-12" />
              <div className="absolute bottom-0 right-0 w-20 h-20 bg-white/5 rounded-full translate-x-8 translate-y-8" />
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg">{acct.account_name}</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-white/20">{ACCT_TYPE_MAP[acct.account_type] || acct.account_type}</span>
                </div>
                {acct.bank_name && <p className="text-sm opacity-80 mb-1">{acct.bank_name}</p>}
                {acct.account_number && <p className="text-xs opacity-60 mb-3 font-mono">{acct.account_number}</p>}
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs opacity-70">{t('payCurrentBalance')}</p>
                    <p className="text-2xl font-bold mt-0.5">{fmt(acct.balance)}</p>
                    <p className="text-xs opacity-60">{acct.currency || 'SAR'}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    {acct.is_default && <span className="text-xs px-2 py-1 rounded-full bg-white/20">⭐</span>}
                    <button onClick={() => openEdit(acct)} className="p-1.5 rounded-lg hover:bg-white/20 transition"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => setDelConf(acct)} className="p-1.5 rounded-lg hover:bg-white/20 transition"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <Modal title={t('payNewAccount')} onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountName')} <span className="text-red-500">*</span></label>
              <input value={form.account_name} onChange={(e) => setForm({ ...form, account_name: e.target.value })} className={inp} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountType')}</label>
                <select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })} className={inp}>
                  {Object.entries(ACCT_TYPE_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payBankName')}</label>
                <input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountNumber')}</label>
                <input value={form.account_number} onChange={(e) => setForm({ ...form, account_number: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payIban')}</label>
                <input value={form.iban} onChange={(e) => setForm({ ...form, iban: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payCurrency')}</label>
                <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} className={inp}>
                  <option value="SAR">SAR</option><option value="USD">USD</option><option value="EUR">EUR</option>
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer py-2.5">
                  <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-riadah-500 focus:ring-accent-500" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{t('payIsDefault')}</span>
                </label>
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}</> : <><Save className="w-4 h-4" /> {t('create')}</>}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Edit Modal */}
      {editAcct && (
        <Modal title={`${t('edit')} — ${editAcct.account_name}`} onClose={() => setEditAcct(null)}>
          <form onSubmit={handleUpdate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountName')} <span className="text-red-500">*</span></label>
              <input value={form.account_name} onChange={(e) => setForm({ ...form, account_name: e.target.value })} className={inp} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountType')}</label>
                <select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })} className={inp}>
                  {Object.entries(ACCT_TYPE_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payBankName')}</label>
                <input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccountNumber')}</label>
                <input value={form.account_number} onChange={(e) => setForm({ ...form, account_number: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payIban')}</label>
                <input value={form.iban} onChange={(e) => setForm({ ...form, iban: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payCurrency')}</label>
                <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} className={inp}>
                  <option value="SAR">SAR</option><option value="USD">USD</option><option value="EUR">EUR</option>
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer py-2.5">
                  <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-riadah-500 focus:ring-accent-500" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{t('payIsDefault')}</span>
                </label>
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}</> : <><Save className="w-4 h-4" /> {t('save')}</>}
              </button>
              <button type="button" onClick={() => setEditAcct(null)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <DeleteConfirm message={`${t('payDeleteAccount')} (${delConf.account_name})?`} onConfirm={handleDelete} loading={delLoading} onCancel={() => setDelConf(null)} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// TAB 3 — Cheques
// ═══════════════════════════════════════════════════════════════════
function ChequesTab({ t, fmt }) {
  const [cheques, setCheques] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const ps = 20;
  const [exporting, setExporting] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);
  const [sLoading, setSLoading] = useState(null);
  const [form, setForm] = useState({ cheque_number: '', bank_name: '', amount: '', due_date: '', payer_name: '', payee_name: '', cheque_type: 'incoming' });
  const [fLoading, setFLoading] = useState(false);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, search: search || undefined, status: statusFilter || undefined };
      const r = await paymentsAPI.getCheques(params);
      const d = r.data;
      setCheques(d.results || (Array.isArray(d) ? d : []));
      setTotal(d.count || d.length || 0);
      setPage(p);
    } catch { toast.error(t('payLoadChequesFailed')); } finally { setLoading(false); }
  }, [search, statusFilter, t]);

  useEffect(() => { fetch(1); }, [fetch]);

  const handleExport = async () => {
    try {
      setExporting(true);
      const r = await paymentsAPI.export();
      const u = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'cheques.xlsx'; a.click(); a.remove();
      toast.success(t('dataExported'));
    } catch { toast.error(t('exportError')); } finally { setExporting(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.cheque_number || !form.amount) { toast.error(t('required')); return; }
    setFLoading(true);
    try {
      await paymentsAPI.createCheque({ ...form, amount: Number(form.amount) });
      toast.success(t('payChequeCreated'));
      setShowCreate(false);
      setForm({ cheque_number: '', bank_name: '', amount: '', due_date: '', payer_name: '', payee_name: '', cheque_type: 'incoming' });
      fetch(1);
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); } finally { setFLoading(false); }
  };

  const updateStatus = async (id, newStatus) => {
    setSLoading(id);
    try {
      await paymentsAPI.updateChequeStatus(id, { status: newStatus });
      toast.success(t('payChequeStatusUpdated'));
      fetch(page);
    } catch (e) { toast.error(e.response?.data?.error || t('error')); } finally { setSLoading(null); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try {
      await paymentsAPI.deleteCheque(delConf.id);
      toast.success(t('payChequeDeleted'));
      setDelConf(null);
      fetch(page);
    } catch (e) { toast.error(e.response?.data?.error || t('error')); } finally { setDelLoading(false); }
  };

  const tp = Math.ceil(total / ps);
  const ths = [t('payChequeNumber'), t('payBankName'), t('payAmount'), t('payDueDate'), t('payPayerName'), t('payChequeType'), t('payChequeStatus'), t('payActions')];
  const typeBadge = (val) => val === 'incoming'
    ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">{t('payIncoming')}</span>
    : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300">{t('payOutgoing')}</span>;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button onClick={() => { setSearch(''); setStatusFilter(''); setPage(1); }} className="text-sm text-gray-500 hover:text-accent-500 dark:text-gray-400 dark:hover:text-accent-400">{t('clearSearch')}</button>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} {t('exportExcel')}
          </button>
          <button onClick={() => setShowCreate(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
            <Plus className="w-4 h-4" /> {t('payNewCheque')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder={t('paySearchCheques')} className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm focus:ring-2 focus:ring-accent-500" />
        </div>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">{t('payAllStatuses')}</option>{Object.entries(CHEQUE_STATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
        ) : cheques.length === 0 ? (
          <EmptyState icon={FileCheck} title={t('payNoCheques')} description={t('payStartAddingCheques')} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{ths.map((h) => <th key={h} className={TH}>{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {cheques.map((ch) => (
                  <tr key={ch.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-3 py-2.5"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300 bg-riadah-50 dark:bg-riadah-900/30 px-2 py-0.5 rounded">{ch.cheque_number}</span></td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{ch.bank_name || '—'}</td>
                    <td className="px-3 py-2.5 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(ch.amount)}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{ch.due_date}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{ch.payer_name || ch.payee_name || '—'}</td>
                    <td className="px-3 py-2.5">{typeBadge(ch.cheque_type)}</td>
                    <td className="px-3 py-2.5">{badge(CHEQUE_STATUS, ch.status)}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1 flex-wrap">
                        {ch.status === 'received' && (
                          <button onClick={() => updateStatus(ch.id, 'deposited')} disabled={sLoading === ch.id} className="text-xs px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 rounded-lg hover:bg-amber-100 disabled:opacity-50">
                            {sLoading === ch.id ? <Loader2 className="w-3 h-3 animate-spin inline" /> : t('payDeposit')}
                          </button>
                        )}
                        {ch.status === 'deposited' && (
                          <button onClick={() => updateStatus(ch.id, 'cleared')} disabled={sLoading === ch.id} className="text-xs px-3 py-1.5 bg-riadah-50 dark:bg-riadah-900/20 text-accent-500 rounded-lg hover:bg-riadah-100 disabled:opacity-50">
                            {sLoading === ch.id ? <Loader2 className="w-3 h-3 animate-spin inline" /> : t('payClearCheque')}
                          </button>
                        )}
                        <button onClick={() => setDelConf(ch)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {tp > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">{((page - 1) * ps) + 1} - {Math.min(page * ps, total)} {t('of')} {total}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetch(page - 1)} disabled={page <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">{page} / {tp}</span>
              <button onClick={() => fetch(page + 1)} disabled={page >= tp} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <Modal title={t('payNewCheque')} onClose={() => setShowCreate(false)} wide>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payChequeNumber')} <span className="text-red-500">*</span></label>
                <input value={form.cheque_number} onChange={(e) => setForm({ ...form, cheque_number: e.target.value })} className={inp} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payBankName')}</label>
                <input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAmount')} <span className="text-red-500">*</span></label>
                <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className={inp} dir="ltr" min="0" step="0.01" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payDueDate')}</label>
                <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payPayerName')}</label>
                <input value={form.payer_name} onChange={(e) => setForm({ ...form, payer_name: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payPayeeName')}</label>
                <input value={form.payee_name} onChange={(e) => setForm({ ...form, payee_name: e.target.value })} className={inp} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payChequeType')}</label>
              <select value={form.cheque_type} onChange={(e) => setForm({ ...form, cheque_type: e.target.value })} className={inp}>
                <option value="incoming">{t('payIncoming')}</option>
                <option value="outgoing">{t('payOutgoing')}</option>
              </select>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}</> : <><Save className="w-4 h-4" /> {t('create')}</>}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <DeleteConfirm message={`${t('payDeleteCheque')} (${delConf.cheque_number})?`} onConfirm={handleDelete} loading={delLoading} onCancel={() => setDelConf(null)} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// TAB 4 — Reconciliations
// ═══════════════════════════════════════════════════════════════════
function ReconciliationsTab({ t, fmt }) {
  const [reconciliations, setReconciliations] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const ps = 20;
  const [exporting, setExporting] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);
  const [form, setForm] = useState({ account: '', period_start: '', period_end: '', system_balance: '', actual_balance: '', notes: '' });
  const [fLoading, setFLoading] = useState(false);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, search: search || undefined };
      const r = await paymentsAPI.getReconciliations(params);
      const d = r.data;
      setReconciliations(d.results || (Array.isArray(d) ? d : []));
      setTotal(d.count || d.length || 0);
      setPage(p);
    } catch { toast.error(t('payLoadReconciliationsFailed')); } finally { setLoading(false); }
  }, [search, t]);

  const fetchAccounts = useCallback(async () => {
    try {
      const r = await paymentsAPI.getAccounts({ page_size: 200 });
      setAccounts(r.data.results || (Array.isArray(r.data) ? r.data : []));
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetch(1); fetchAccounts(); }, [fetch, fetchAccounts]);

  const handleExport = async () => {
    try {
      setExporting(true);
      const r = await paymentsAPI.export();
      const u = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = u; a.download = 'reconciliations.xlsx'; a.click(); a.remove();
      toast.success(t('dataExported'));
    } catch { toast.error(t('exportError')); } finally { setExporting(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.account) { toast.error(t('required')); return; }
    setFLoading(true);
    try {
      await paymentsAPI.createReconciliation({
        ...form,
        system_balance: Number(form.system_balance) || 0,
        actual_balance: Number(form.actual_balance) || 0,
      });
      toast.success(t('payReconciliationCreated'));
      setShowCreate(false);
      setForm({ account: '', period_start: '', period_end: '', system_balance: '', actual_balance: '', notes: '' });
      fetch(1);
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); } finally { setFLoading(false); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try {
      await paymentsAPI.deleteReconciliation(delConf.id);
      toast.success(t('payReconciliationDeleted'));
      setDelConf(null);
      fetch(page);
    } catch (e) { toast.error(e.response?.data?.error || t('error')); } finally { setDelLoading(false); }
  };

  const tp = Math.ceil(total / ps);
  const ths = [t('payAccount'), t('payPeriodStart'), t('payPeriodEnd'), t('paySystemBalance'), t('payActualBalance'), t('payDifference'), t('status'), t('payActions')];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button onClick={() => { setSearch(''); setPage(1); }} className="text-sm text-gray-500 hover:text-accent-500 dark:text-gray-400 dark:hover:text-accent-400">{t('clearSearch')}</button>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} {t('exportExcel')}
          </button>
          <button onClick={() => { setForm({ account: '', period_start: '', period_end: '', system_balance: '', actual_balance: '', notes: '' }); setShowCreate(true); }} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
            <Plus className="w-4 h-4" /> {t('payNewReconciliation')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder={t('search')} className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm focus:ring-2 focus:ring-accent-500" />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
        ) : reconciliations.length === 0 ? (
          <EmptyState icon={CheckSquare} title={t('payNoReconciliations')} description={t('payStartAddingReconciliations')} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{ths.map((h) => <th key={h} className={TH}>{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {reconciliations.map((rec) => {
                  const diff = rec.difference;
                  return (
                    <tr key={rec.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100">{rec.account_name || '—'}</td>
                      <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{rec.period_start || '—'}</td>
                      <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{rec.period_end || '—'}</td>
                      <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100" dir="ltr">{fmt(rec.system_balance)}</td>
                      <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100" dir="ltr">{rec.actual_balance != null ? fmt(rec.actual_balance) : '—'}</td>
                      <td className="px-3 py-2.5">
                        {diff != null ? (
                          <span className={`text-sm font-bold ${diff === 0 ? 'text-emerald-500' : diff < 0 ? 'text-red-500' : 'text-amber-500'}`}>
                            {diff === 0 ? t('payMatched') : fmt(diff)}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-3 py-2.5">{badge(RECON_STATUS, rec.status)}</td>
                      <td className="px-3 py-2.5">
                        <button onClick={() => setDelConf(rec)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {tp > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">{((page - 1) * ps) + 1} - {Math.min(page * ps, total)} {t('of')} {total}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetch(page - 1)} disabled={page <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">{page} / {tp}</span>
              <button onClick={() => fetch(page + 1)} disabled={page >= tp} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <Modal title={t('payNewReconciliation')} onClose={() => setShowCreate(false)} wide>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payAccount')} <span className="text-red-500">*</span></label>
              <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })} className={inp} required>
                <option value="">{t('search')}...</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.account_name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payPeriodStart')}</label>
                <input type="date" value={form.period_start} onChange={(e) => setForm({ ...form, period_start: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payPeriodEnd')}</label>
                <input type="date" value={form.period_end} onChange={(e) => setForm({ ...form, period_end: e.target.value })} className={inp} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paySystemBalance')}</label>
                <input type="number" value={form.system_balance} onChange={(e) => setForm({ ...form, system_balance: e.target.value })} className={inp} dir="ltr" min="0" step="0.01" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payActualBalance')}</label>
                <input type="number" value={form.actual_balance} onChange={(e) => setForm({ ...form, actual_balance: e.target.value })} className={inp} dir="ltr" min="0" step="0.01" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('payReconciliationNotes')}</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={`${inp} resize-none`} rows={3} />
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}</> : <><Save className="w-4 h-4" /> {t('create')}</>}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <DeleteConfirm message={`${t('confirmDeleteMessage')} ${t('payReconciliation')}?`} onConfirm={handleDelete} loading={delLoading} onCancel={() => setDelConf(null)} />}
    </div>
  );
}
