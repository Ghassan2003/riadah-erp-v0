/**
 * Contracts Management Page – إدارة العقود
 * Tabs: Contracts, Milestones, Payments
 * Fully integrated with contractsAPI – no mock data.
 */
import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { contractsAPI } from '../api';
import {
  FileText, Plus, Search, Eye, Loader2, ChevronLeft, ChevronRight, X, Save,
  Trash2, RotateCcw, RefreshCw, Play, Ban, Download, CheckCircle, DollarSign,
  AlertTriangle, Clock, CreditCard, Target,
} from 'lucide-react';
import toast from 'react-hot-toast';
/* eslint-disable react/prop-types */

// ─── Status / Type Maps ─────────────────────────────────────────
const CSTATUS = {
  draft:      ['مسودة',   'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
  active:     ['نشط',     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'],
  expired:    ['منتهي',   'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  terminated: ['ملغى',    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  renewed:    ['مجدّد',   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'],
  cancelled:  ['ملغي',    'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'],
};
const CTYPE = {
  sales:       ['مبيعات',    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'],
  purchase:    ['مشتريات',   'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'],
  service:     ['خدمات',     'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300'],
  rental:      ['إيجار',     'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
  employment:  ['توظيف',     'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300'],
  consultancy: ['استشارات',  'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'],
  maintenance: ['صيانة',     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'],
  other:       ['أخرى',      'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'],
};
const MSTATUS = {
  pending:     ['معلق',      'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
  in_progress: ['قيد التنفيذ', 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'],
  completed:   ['مكتمل',     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'],
  overdue:     ['متأخر',     'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
};
const PSTATUS = {
  pending:        ['معلق',          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
  paid:           ['مدفوع',         'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'],
  partially_paid: ['مدفوع جزئياً',  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'],
  overdue:        ['متأخر',         'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
};
const PMETHOD = { cash: 'نقدي', bank_transfer: 'تحويل بنكي', card: 'بطاقة', check: 'شيك' };

const badge = (map, key) => {
  const [label, cls] = map[key] || [key, ''];
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
};
const IP = 'text-right px-3 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap';

// ─── Shared Modal ──────────────────────────────────────────────
function Modal({ title, onClose, wide, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={onClose} />
      <div className={`relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full ${wide ? 'max-w-3xl' : 'max-w-lg'} max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10 rounded-t-2xl">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><X className="w-5 h-5 text-gray-500 dark:text-gray-400" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Confirm Dialog ────────────────────────────────────────────
function ConfirmDialog({ title, message, onConfirm, onCancel, loading }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={onCancel} />
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
          <p className="text-gray-600 dark:text-gray-300 mb-5">{message}</p>
          <div className="flex gap-3">
            <button onClick={onConfirm} disabled={loading} className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /></> : <><Trash2 className="w-4 h-4" /> حذف</>}
            </button>
            <button onClick={onCancel} className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────
export default function ContractsPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState('contracts');
  const tabs = [
    { key: 'contracts',   label: t('contractsTab'),     icon: FileText },
    { key: 'milestones',  label: t('milestonesTab'),    icon: Target },
    { key: 'payments',    label: t('paymentsTab'),      icon: DollarSign },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageContracts')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('contractsDesc')}</p>
      </div>
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((tItem) => (
          <button key={tItem.key} onClick={() => setTab(tItem.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === tItem.key ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}>
            <tItem.icon className="w-4 h-4" />{tItem.label}
          </button>
        ))}
      </div>
      {tab === 'contracts' && <ContractsTab />}
      {tab === 'milestones' && <MilestonesTab />}
      {tab === 'payments' && <ContractPaymentsTab />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// TAB 1 — CONTRACTS
// ═══════════════════════════════════════════════════════════════
function ContractsTab() {
  const { locale, t } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [contracts, setContracts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sf, setSf] = useState('');
  const [tf, setTf] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const ps = 20;
  const [exporting, setExporting] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [showRenew, setShowRenew] = useState(null);
  const [aLoading, setALoading] = useState(null);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);

  const [form, setForm] = useState({
    title: '', type: 'service', customer_supplier: '', project: '',
    start_date: '', end_date: '', value: '', currency: 'SAR',
    terms: '', notes: '', vat_inclusive: false,
  });
  const [fLoading, setFLoading] = useState(false);
  const [renewForm, setRenewForm] = useState({ new_start_date: '', new_end_date: '' });
  const [renewLoading, setRenewLoading] = useState(false);

  const fetchContracts = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = {
        page: p, search: search || undefined, status: sf || undefined, type: tf || undefined,
      };
      const [cr, sr] = await Promise.all([contractsAPI.getContracts(params), contractsAPI.getStats()]);
      const d = cr.data;
      setContracts(d.results || (Array.isArray(d) ? d : []));
      setTotal(d.count || d.length || 0);
      setStats(sr.data);
      setPage(p);
    } catch {
      toast.error(t('loadContractsFailed'));
    } finally {
      setLoading(false);
    }
  }, [search, sf, tf, t]);

  useEffect(() => { fetchContracts(1); }, [fetchContracts]);
  const resetF = () => { setSearch(''); setSf(''); setTf(''); setPage(1); };

  const handleExport = async () => {
    try {
      setExporting(true);
      const r = await contractsAPI.export();
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'contracts.xlsx'; a.click(); a.remove();
      toast.success(t('exportSuccess'));
    } catch {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  const act = async (id, fn, msg) => {
    setALoading(id);
    try { await fn(); toast.success(msg); fetchContracts(page); }
    catch (e) { toast.error(e.response?.data?.error || t('operationFailed')); }
    finally { setALoading(null); }
  };

  const openDetail = async (c) => {
    try { const r = await contractsAPI.getContract(c.id); setDetailData(r.data); setShowDetail(c.id); }
    catch { toast.error(t('operationFailed')); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error(t('required')); return; }
    setFLoading(true);
    try {
      await contractsAPI.createContract({
        ...form,
        value: Number(form.value) || 0,
        vat_inclusive: form.vat_inclusive,
      });
      toast.success(t('contractCreated'));
      setShowCreate(false);
      setForm({ title: '', type: 'service', customer_supplier: '', project: '', start_date: '', end_date: '', value: '', currency: 'SAR', terms: '', notes: '', vat_inclusive: false });
      fetchContracts(1);
    } catch (err) {
      toast.error(err.response?.data?.error || t('operationFailed'));
    } finally {
      setFLoading(false);
    }
  };

  const handleRenew = async (e) => {
    e.preventDefault();
    if (!renewForm.new_start_date || !renewForm.new_end_date) { toast.error(t('required')); return; }
    setRenewLoading(true);
    try {
      await contractsAPI.renewContract(showRenew.id, renewForm);
      toast.success(t('contractRenewed'));
      setShowRenew(null);
      setRenewForm({ new_start_date: '', new_end_date: '' });
      fetchContracts(page);
    } catch (err) {
      toast.error(err.response?.data?.error || t('operationFailed'));
    } finally {
      setRenewLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try {
      await contractsAPI.deleteContract(delConf.id);
      toast.success(t('contractDeleted'));
      setDelConf(null);
      fetchContracts(page);
    } catch { toast.error(t('operationFailed')); }
    finally { setDelLoading(false); }
  };

  const tp = Math.ceil(total / ps);
  const statCards = [
    [t('totalContracts'), stats.total_contracts, FileText, 'from-riadah-400 to-riadah-500'],
    [t('activeContracts'), stats.active_contracts, CheckCircle, 'from-emerald-500 to-emerald-600'],
    [t('contractsTotalValue'), fmt(stats.total_value), DollarSign, 'from-violet-500 to-violet-600'],
    [t('expiringSoonContracts'), stats.expiring_soon_count, Clock, 'from-amber-500 to-amber-600'],
  ];
  const ths = [t('contractNumber'), t('contractTitle'), t('contractType'), t('contractCustomer'), t('contractStart'), t('contractEnd'), t('contractValue'), t('status'), t('remainingDays'), t('actions')];

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statCards.map(([label, value, Icon, gradient], i) => (
          <div key={i} className={`bg-gradient-to-br ${gradient} rounded-xl p-4 text-white shadow-lg`}>
            <div className="flex items-center justify-between mb-2"><Icon className="w-5 h-5 opacity-80" /><span className="text-xs opacity-80">{label}</span></div>
            <p className="text-xl font-bold">{value ?? '—'}</p>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button onClick={resetF} className="text-sm text-gray-500 hover:text-accent-500 dark:text-gray-400 dark:hover:text-accent-400">{t('clearFilters')}</button>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}{t('exportExcel')}
          </button>
          <button onClick={() => setShowCreate(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
            <Plus className="w-4 h-4" />{t('newContract')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder={t('search')} className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm focus:ring-2 focus:ring-accent-500" />
        </div>
        <select value={sf} onChange={(e) => { setSf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">{t('allStatuses')}</option>
          {Object.entries(CSTATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={tf} onChange={(e) => { setTf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">{t('allTypes')}</option>
          {Object.entries(CTYPE).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
        ) : contracts.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FileText className="w-16 h-16 mx-auto mb-3 opacity-40" />
            <p className="font-medium">{t('noContracts')}</p>
            <p className="text-sm mt-1">{t('noContractsDesc')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  {ths.map((h) => <th key={h} className={IP}>{h}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {contracts.map((c) => (
                  <tr key={c.id} className={`hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${c.is_deleted ? 'opacity-60' : ''}`}>
                    <td className="px-3 py-2.5">
                      <span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300 bg-riadah-50 dark:bg-riadah-900/30 px-2 py-0.5 rounded">{c.contract_number}</span>
                    </td>
                    <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100">{c.title}</td>
                    <td className="px-3 py-2.5">{badge(CTYPE, c.type)}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{c.customer_supplier || '—'}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{c.start_date}</td>
                    <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{c.end_date}</td>
                    <td className="px-3 py-2.5 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(c.value)}</td>
                    <td className="px-3 py-2.5">{badge(CSTATUS, c.status)}</td>
                    <td className="px-3 py-2.5">
                      <span className={c.remaining_days != null && c.remaining_days <= 60 && c.remaining_days > 0 ? 'text-amber-600 font-bold' : c.remaining_days === 0 ? 'text-red-500 font-bold' : 'text-gray-600 dark:text-gray-400'}>
                        {c.remaining_days == null ? '—' : c.remaining_days <= 0 ? t('expiredContract') : `${c.remaining_days}`}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1 flex-wrap">
                        <button onClick={() => openDetail(c)} className="p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" title={t('details')}><Eye className="w-4 h-4" /></button>
                        {c.status === 'draft' && (
                          <button onClick={() => act(c.id, () => contractsAPI.changeStatus(c.id, { status: 'active' }), t('contractStatusChanged'))} disabled={aLoading === c.id} className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg" title="تفعيل"><Play className="w-4 h-4" /></button>
                        )}
                        {(c.status === 'active' || c.status === 'draft') && (
                          <button onClick={() => act(c.id, () => contractsAPI.changeStatus(c.id, { status: 'cancelled' }), t('contractStatusChanged'))} disabled={aLoading === c.id} className="p-1.5 text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg" title={t('cancel')}><Ban className="w-4 h-4" /></button>
                        )}
                        {(c.status === 'expired' || c.status === 'active') && (
                          <button onClick={() => { setShowRenew(c); setRenewForm({ new_start_date: '', new_end_date: '' }); }} disabled={aLoading === c.id} className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg" title={t('renewContract')}><RefreshCw className="w-4 h-4" /></button>
                        )}
                        {c.is_deleted ? (
                          <button onClick={() => act(c.id, () => contractsAPI.restoreContract(c.id), t('contractRestored'))} disabled={aLoading === c.id} className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg" title={t('restore')}><RotateCcw className="w-4 h-4" /></button>
                        ) : (
                          <button onClick={() => setDelConf(c)} disabled={aLoading === c.id} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title={t('delete')}><Trash2 className="w-4 h-4" /></button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tp > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">{((page - 1) * ps) + 1} - {Math.min(page * ps, total)} {t('of')} {total}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetchContracts(page - 1)} disabled={page <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">{page} / {tp}</span>
              <button onClick={() => fetchContracts(page + 1)} disabled={page >= tp} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <Modal title={t('createContract')} onClose={() => setShowCreate(false)} wide>
          <form onSubmit={handleCreate} className="p-5 space-y-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractTitle')} <span className="text-red-500">*</span></label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required /></div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractType')}</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  {Object.entries(CTYPE).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                </select></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractCustomer')} / {t('contractSupplier')}</label>
                <input value={form.customer_supplier} onChange={(e) => setForm({ ...form, customer_supplier: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractProject')} ({t('optional')})</label>
                <input value={form.project} onChange={(e) => setForm({ ...form, project: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractStart')}</label>
                <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractEnd')}</label>
                <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractValue')}</label>
                <input type="number" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractCurrency')}</label>
                <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  <option value="SAR">SAR</option><option value="USD">USD</option><option value="EUR">EUR</option>
                </select></div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={form.vat_inclusive} onChange={(e) => setForm({ ...form, vat_inclusive: e.target.checked })} className="rounded border-gray-300 text-riadah-500 focus:ring-riadah-500" />
              <label className="text-sm text-gray-700 dark:text-gray-300">{t('vatInclusive')}</label>
            </div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractTerms')}</label>
              <textarea value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm h-24 resize-none" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractNotes')}</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm h-16 resize-none" /></div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /></> : <><Save className="w-4 h-4" /></>}{t('createContract')}</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Detail Modal */}
      {showDetail && detailData && (
        <Modal title={`${t('contractDetail')}: ${detailData.contract_number}`} onClose={() => setShowDetail(null)} wide>
          <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[['الحالة', badge(CSTATUS, detailData.status)], [t('contractType'), badge(CTYPE, detailData.type)], [t('contractCustomer'), detailData.customer_supplier || '—'], [t('contractProject'), detailData.project || '—'], [t('contractStart'), detailData.start_date], [t('contractEnd'), detailData.end_date], [t('contractValue'), fmt(detailData.value)], [t('contractCurrency'), detailData.currency]].map(([label, value], i) => (
                <div key={i} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5"><p className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{label}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{value}</p></div>
              ))}
            </div>
            {detailData.terms && <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3"><p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('contractTerms')}</p><p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{detailData.terms}</p></div>}
            {detailData.notes && <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3"><p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('contractNotes')}</p><p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{detailData.notes}</p></div>}
            {detailData.milestones?.length > 0 && (
              <div><h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('milestonesTab')}</h4>
                <div className="space-y-1">{detailData.milestones.map((m) => (
                  <div key={m.id} className="flex justify-between items-center bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2 text-sm"><span className="text-gray-700 dark:text-gray-300">{m.title}</span><div className="flex items-center gap-2"><span dir="ltr" className="text-gray-500 text-xs">{fmt(m.amount)}</span>{badge(MSTATUS, m.status)}</div></div>
                ))}</div>
              </div>
            )}
            {detailData.payments?.length > 0 && (
              <div><h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('paymentsTab')}</h4>
                <div className="space-y-1">{detailData.payments.map((p) => (
                  <div key={p.id} className="flex justify-between items-center bg-green-50 dark:bg-green-900/10 rounded-lg px-3 py-2 text-sm"><span className="text-gray-700 dark:text-gray-300">{p.payment_number || p.description}</span><div className="flex items-center gap-2"><span dir="ltr" className="text-green-700 dark:text-green-400 font-semibold">{fmt(p.amount)}</span>{badge(PSTATUS, p.status)}</div></div>
                ))}</div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Renew Modal */}
      {showRenew && (
        <Modal title={t('renewContract')} onClose={() => setShowRenew(null)}>
          <form onSubmit={handleRenew} className="p-5 space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-300">{t('contractNumber')}: <span className="font-semibold text-gray-900 dark:text-gray-100">{showRenew.contract_number}</span></p>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('renewStartDate')}</label>
              <input type="date" value={renewForm.new_start_date} onChange={(e) => setRenewForm({ ...renewForm, new_start_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('renewDate')}</label>
              <input type="date" value={renewForm.new_end_date} onChange={(e) => setRenewForm({ ...renewForm, new_end_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required /></div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={renewLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {renewLoading ? <><Loader2 className="w-4 h-4 animate-spin" /></> : <><RefreshCw className="w-4 h-4" /></>}{t('renewContract')}</button>
              <button type="button" onClick={() => setShowRenew(null)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <ConfirmDialog title={t('confirmDelete')} message={`${t('confirmDeleteMessage')} "${delConf.contract_number}"?`} onConfirm={handleDelete} onCancel={() => setDelConf(null)} loading={delLoading} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// TAB 2 — MILESTONES
// ═══════════════════════════════════════════════════════════════
function MilestonesTab() {
  const { t } = useI18n();
  const nl = 'ar-SA';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [contracts, setContracts] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [selContract, setSelContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mLoading, setMLoading] = useState(true);
  const [sf, setSf] = useState('');
  const [search, setSearch] = useState('');

  const [showCreate, setShowCreate] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ contract: '', title: '', description: '', due_date: '', amount: '', status: 'pending' });
  const [fLoading, setFLoading] = useState(false);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await contractsAPI.getContracts({ page_size: 200, status: 'active' });
        setContracts(r.data.results || r.data);
      } catch { toast.error(t('loadContractsFailed')); }
      finally { setLoading(false); }
    })();
  }, [t]);

  const loadMilestones = async (contractId) => {
    setMLoading(true);
    try {
      const r = await contractsAPI.getMilestones({ contract: contractId });
      setMilestones(r.data.results || (Array.isArray(r.data) ? r.data : []));
    } catch { toast.error(t('operationFailed')); }
    finally { setMLoading(false); }
  };

  const selectContract = (c) => { setSelContract(c); loadMilestones(c.id); setSearch(''); setSf(''); };

  const openCreate = () => {
    setForm({ contract: selContract?.id || '', title: '', description: '', due_date: '', amount: '', status: 'pending' });
    setEditItem(null);
    setShowCreate(true);
  };

  const openEdit = async (m) => {
    try {
      const r = await contractsAPI.getMilestone(m.id);
      const d = r.data;
      setForm({ contract: d.contract, title: d.title, description: d.description || '', due_date: d.due_date, amount: String(d.amount || ''), status: d.status });
      setEditItem(m);
      setShowCreate(true);
    } catch { toast.error(t('operationFailed')); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.contract) { toast.error(t('required')); return; }
    setFLoading(true);
    const payload = { ...form, amount: Number(form.amount) || 0 };
    try {
      if (editItem) {
        await contractsAPI.updateMilestone(editItem.id, payload);
        toast.success(t('milestoneUpdated'));
      } else {
        await contractsAPI.createMilestone(payload);
        toast.success(t('milestoneCreated'));
      }
      setShowCreate(false);
      if (selContract) loadMilestones(selContract.id);
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); }
    finally { setFLoading(false); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try { await contractsAPI.deleteMilestone(delConf.id); toast.success(t('milestoneDeleted')); setDelConf(null); if (selContract) loadMilestones(selContract.id); }
    catch { toast.error(t('operationFailed')); }
    finally { setDelLoading(false); }
  };

  const changeStatus = async (id, status) => {
    try { await contractsAPI.updateMilestone(id, { status }); toast.success(t('milestoneUpdated')); if (selContract) loadMilestones(selContract.id); }
    catch { toast.error(t('operationFailed')); }
  };

  const filtered = milestones.filter((m) =>
    (sf === '' || m.status === sf) &&
    (m.title.includes(search) || (m.description || '').includes(search))
  );

  const mThs = [t('milestoneTitle'), t('milestoneDueDate'), t('milestoneAmount'), t('milestoneStatus'), t('actions')];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-500 dark:text-gray-400">{t('selectContract')}</p>
        {selContract && <button onClick={openCreate} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" />{t('newMilestone')}</button>}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Contract List */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden max-h-[500px]">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 font-medium text-sm text-gray-700 dark:text-gray-300">{t('activeContracts')}</div>
          {loading ? <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-accent-500" /></div>
            : <div className="overflow-y-auto max-h-[440px]">{contracts.map((c) => (
              <button key={c.id} onClick={() => selectContract(c)} className={`w-full text-right px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 transition-colors ${selContract?.id === c.id ? 'bg-riadah-50 dark:bg-riadah-900/20 border-r-4 border-r-blue-600' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'}`}>
                <div className="flex justify-between items-center"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{c.contract_number}</span>{badge(CSTATUS, c.status)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{c.title} — {c.customer_supplier}</p>
              </button>
            ))}</div>}
        </div>
        {/* Milestones Table */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {!selContract ? (
            <div className="flex items-center justify-center py-20 text-gray-400"><Target className="w-12 h-12 opacity-40 ml-3" /><p>{t('selectContract')}</p></div>
          ) : mLoading ? (
            <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 p-3 border-b border-gray-200 dark:border-gray-700">
                <div className="relative flex-1 min-w-[150px]"><Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('search')} className="w-full pr-9 pl-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
                <select value={sf} onChange={(e) => setSf(e.target.value)} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  <option value="">{t('allStatuses')}</option>
                  {Object.entries(MSTATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              {filtered.length === 0 ? (
                <div className="flex items-center justify-center py-16 text-gray-400"><p>{t('noMilestones')}</p></div>
              ) : (
                <div className="overflow-x-auto"><table className="w-full"><thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{mThs.map((h) => <th key={h} className={IP}>{h}</th>)}</tr></thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{filtered.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-3 py-2.5"><div className="text-sm font-medium text-gray-900 dark:text-gray-100">{m.title}</div>{m.description && <p className="text-xs text-gray-400 mt-0.5 truncate max-w-[200px]">{m.description}</p>}</td>
                      <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{m.due_date}</td>
                      <td className="px-3 py-2.5 text-sm font-semibold" dir="ltr">{fmt(m.amount)}</td>
                      <td className="px-3 py-2.5">{badge(MSTATUS, m.status)}</td>
                      <td className="px-3 py-2.5"><div className="flex items-center gap-1">
                        {m.status === 'pending' && <button onClick={() => changeStatus(m.id, 'in_progress')} className="text-xs px-2 py-1 bg-amber-50 dark:bg-amber-900/20 text-amber-600 rounded-lg hover:bg-amber-100">{t('startMilestone')}</button>}
                        {m.status === 'in_progress' && <button onClick={() => changeStatus(m.id, 'completed')} className="text-xs px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-600 rounded-lg hover:bg-green-100">{t('completeMilestone')}</button>}
                        <button onClick={() => openEdit(m)} className="p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><Eye className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setDelConf(m)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div></td>
                    </tr>
                  ))}</tbody></table></div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Create / Edit Modal */}
      {showCreate && (
        <Modal title={editItem ? t('edit') : t('createMilestone')} onClose={() => setShowCreate(false)}>
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('milestoneTitle')} <span className="text-red-500">*</span></label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('milestoneDescription')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm h-16 resize-none" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('milestoneDueDate')}</label>
                <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('milestoneAmount')}</label>
                <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" required /></div>
            </div>
            {!editItem && (
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractNumber')}</label>
                <select value={form.contract} onChange={(e) => setForm({ ...form, contract: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required disabled>
                  {contracts.map((c) => <option key={c.id} value={c.id}>{c.contract_number} — {c.title}</option>)}
                </select></div>
            )}
            {editItem && (
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('milestoneStatus')}</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  {Object.entries(MSTATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                </select></div>
            )}
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /></> : <><Save className="w-4 h-4" /></>}{editItem ? t('save') : t('createMilestone')}</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <ConfirmDialog title={t('confirmDelete')} message={`${t('confirmDeleteMessage')} "${delConf.title}"?`} onConfirm={handleDelete} onCancel={() => setDelConf(null)} loading={delLoading} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// TAB 3 — CONTRACT PAYMENTS
// ═══════════════════════════════════════════════════════════════
function ContractPaymentsTab() {
  const { t } = useI18n();
  const nl = 'ar-SA';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });

  const [contracts, setContracts] = useState([]);
  const [payments, setPayments] = useState([]);
  const [selContract, setSelContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pLoading, setPLoading] = useState(true);
  const [sf, setSf] = useState('');
  const [search, setSearch] = useState('');

  const [showCreate, setShowCreate] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ contract: '', amount: '', due_date: '', paid_date: '', paid_amount: '', payment_method: 'cash', description: '', status: 'pending' });
  const [fLoading, setFLoading] = useState(false);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await contractsAPI.getContracts({ page_size: 200 });
        setContracts(r.data.results || r.data);
      } catch { toast.error(t('loadContractsFailed')); }
      finally { setLoading(false); }
    })();
  }, [t]);

  const loadPayments = async (contractId) => {
    setPLoading(true);
    try {
      const r = await contractsAPI.getContractPayments({ contract: contractId });
      setPayments(r.data.results || (Array.isArray(r.data) ? r.data : []));
    } catch { toast.error(t('operationFailed')); }
    finally { setPLoading(false); }
  };

  const selectContract = (c) => { setSelContract(c); loadPayments(c.id); setSearch(''); setSf(''); };

  const openCreate = () => {
    setForm({ contract: selContract?.id || '', amount: '', due_date: '', paid_date: '', paid_amount: '', payment_method: 'cash', description: '', status: 'pending' });
    setEditItem(null);
    setShowCreate(true);
  };

  const openEdit = async (p) => {
    try {
      const r = await contractsAPI.getContractPayment(p.id);
      const d = r.data;
      setForm({ contract: d.contract, amount: String(d.amount || ''), due_date: d.due_date || '', paid_date: d.paid_date || '', paid_amount: String(d.paid_amount || ''), payment_method: d.payment_method || 'cash', description: d.description || '', status: d.status || 'pending' });
      setEditItem(p);
      setShowCreate(true);
    } catch { toast.error(t('operationFailed')); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.amount || !form.contract) { toast.error(t('required')); return; }
    setFLoading(true);
    const payload = { ...form, amount: Number(form.amount) || 0, paid_amount: Number(form.paid_amount) || 0 };
    try {
      if (editItem) {
        await contractsAPI.updateContractPayment(editItem.id, payload);
        toast.success(t('paymentUpdated'));
      } else {
        await contractsAPI.createContractPayment(payload);
        toast.success(t('paymentCreated'));
      }
      setShowCreate(false);
      if (selContract) loadPayments(selContract.id);
    } catch (err) { toast.error(err.response?.data?.error || t('operationFailed')); }
    finally { setFLoading(false); }
  };

  const handleDelete = async () => {
    if (!delConf) return;
    setDelLoading(true);
    try { await contractsAPI.deleteContractPayment(delConf.id); toast.success(t('paymentDeleted')); setDelConf(null); if (selContract) loadPayments(selContract.id); }
    catch { toast.error(t('operationFailed')); }
    finally { setDelLoading(false); }
  };

  const markPaid = async (p) => {
    try { await contractsAPI.updateContractPayment(p.id, { status: 'paid', paid_amount: p.amount, paid_date: new Date().toISOString().split('T')[0] }); toast.success(t('paymentUpdated')); if (selContract) loadPayments(selContract.id); }
    catch { toast.error(t('operationFailed')); }
  };

  const progress = (paid, total) => total > 0 ? Math.min(100, (paid / total) * 100) : 0;
  const filtered = payments.filter((p) =>
    (sf === '' || p.status === sf) &&
    ((p.description || '').includes(search) || (p.payment_number || '').includes(search))
  );

  const pThs = [t('contractNumber'), t('paymentAmount'), t('paymentDueDate'), t('paidAmount'), t('payPercentage'), t('paymentMethod'), t('paymentStatus'), t('actions')];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-500 dark:text-gray-400">{t('selectContract')}</p>
        {selContract && <button onClick={openCreate} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" />{t('newPayment')}</button>}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Contract List */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden max-h-[500px]">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 font-medium text-sm text-gray-700 dark:text-gray-300">{t('contractsTab')}</div>
          {loading ? <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-accent-500" /></div>
            : <div className="overflow-y-auto max-h-[440px]">{contracts.map((c) => (
              <button key={c.id} onClick={() => selectContract(c)} className={`w-full text-right px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 transition-colors ${selContract?.id === c.id ? 'bg-riadah-50 dark:bg-riadah-900/20 border-r-4 border-r-blue-600' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'}`}>
                <div className="flex justify-between items-center"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{c.contract_number}</span>{badge(CSTATUS, c.status)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{c.title} — {c.customer_supplier}</p>
              </button>
            ))}</div>}
        </div>
        {/* Payments Table */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {!selContract ? (
            <div className="flex items-center justify-center py-20 text-gray-400"><CreditCard className="w-12 h-12 opacity-40 ml-3" /><p>{t('selectContract')}</p></div>
          ) : pLoading ? (
            <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 p-3 border-b border-gray-200 dark:border-gray-700">
                <div className="relative flex-1 min-w-[150px]"><Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('search')} className="w-full pr-9 pl-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
                <select value={sf} onChange={(e) => setSf(e.target.value)} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  <option value="">{t('allStatuses')}</option>
                  {Object.entries(PSTATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              {filtered.length === 0 ? (
                <div className="flex items-center justify-center py-16 text-gray-400"><p>{t('noPayments')}</p></div>
              ) : (
                <div className="overflow-x-auto"><table className="w-full"><thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{pThs.map((h) => <th key={h} className={IP}>{h}</th>)}</tr></thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{filtered.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-3 py-2.5 font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{p.payment_number || '—'}</td>
                      <td className="px-3 py-2.5 text-sm font-semibold" dir="ltr">{fmt(p.amount)}</td>
                      <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{p.due_date || '—'}</td>
                      <td className="px-3 py-2.5 text-sm" dir="ltr">{fmt(p.paid_amount || 0)}</td>
                      <td className="px-3 py-2.5 w-28">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div className="h-full bg-riadah-500 rounded-full transition-all" style={{ width: `${progress(p.paid_amount || 0, p.amount)}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{Math.round(progress(p.paid_amount || 0, p.amount))}%</span>
                        </div>
                      </td>
                      <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{PMETHOD[p.payment_method] || p.payment_method || '—'}</td>
                      <td className="px-3 py-2.5">{badge(PSTATUS, p.status)}</td>
                      <td className="px-3 py-2.5"><div className="flex items-center gap-1">
                        {p.status !== 'paid' && <button onClick={() => markPaid(p)} className="text-xs px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-600 rounded-lg hover:bg-green-100">{t('paymentMarkPaid')}</button>}
                        <button onClick={() => openEdit(p)} className="p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><Eye className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setDelConf(p)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div></td>
                    </tr>
                  ))}</tbody></table></div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Create / Edit Modal */}
      {showCreate && (
        <Modal title={editItem ? t('edit') : t('createPayment')} onClose={() => setShowCreate(false)} wide>
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {!editItem && (
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('contractNumber')}</label>
                <select value={form.contract} onChange={(e) => setForm({ ...form, contract: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required disabled>
                  {contracts.map((c) => <option key={c.id} value={c.id}>{c.contract_number} — {c.title}</option>)}
                </select></div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paymentAmount')} <span className="text-red-500">*</span></label>
                <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" required /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paymentDueDate')}</label>
                <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paidAmount')}</label>
                <input type="number" value={form.paid_amount} onChange={(e) => setForm({ ...form, paid_amount: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" /></div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paymentMethod')}</label>
                <select value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                  {Object.entries(PMETHOD).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></div>
            </div>
            {editItem && (
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paymentStatus')}</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
                    {Object.entries(PSTATUS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
                  </select></div>
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('paidAmount')} ({t('date')})</label>
                  <input type="date" value={form.paid_date} onChange={(e) => setForm({ ...form, paid_date: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
              </div>
            )}
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm h-16 resize-none" /></div>
            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
                {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /></> : <><Save className="w-4 h-4" /></>}{editItem ? t('save') : t('createPayment')}</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">{t('cancel')}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirm */}
      {delConf && <ConfirmDialog title={t('confirmDelete')} message={`${t('confirmDeleteMessage')} "${delConf.payment_number || delConf.description || ''}"?`} onConfirm={handleDelete} onCancel={() => setDelConf(null)} loading={delLoading} />}
    </div>
  );
}
