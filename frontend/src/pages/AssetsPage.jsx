/**
 * Assets page — Fixed Asset management (RIADAH ERP).
 * Features: tab navigation, stats cards, asset list with search/filter,
 * create-asset modal, categories & maintenance read-only tabs.
 * Supports dark mode, RTL and i18n.
 */

import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { assetsAPI } from '../api';
import {
  Building2, DollarSign, TrendingDown, Wrench, Plus, Search, Download,
  X, Eye, Trash2, Calculator, Loader2, ChevronLeft, ChevronRight,
  PackageOpen,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Shared Components ─────────────────────────────────────────────

const Badge = ({ children, color = 'blue' }) => {
  const colors = {
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    yellow: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    blue: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/40 dark:text-accent-300',
    gray: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300',
    violet: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  };
  return <span className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${colors[color]}`}>{children}</span>;
};

const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className={`relative overflow-hidden rounded-2xl p-4 md:p-5 bg-gradient-to-br ${color} text-white shadow-lg`}>
    <div className="absolute top-0 left-0 w-24 h-24 bg-white/10 rounded-full -translate-x-8 -translate-y-8" />
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-xl bg-white/20"><Icon className="w-5 h-5" /></div>
      <div><p className="text-xs opacity-80">{label}</p><p className="text-xl font-bold mt-0.5">{value}</p></div>
    </div>
  </div>
);

const inputCls = "w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-500 transition";
const btnBase = "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 shadow-sm";
const btnPrimary = `${btnBase} bg-riadah-500 hover:bg-riadah-600 text-white`;
const btnSecondary = `${btnBase} bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700`;
const btnDanger = `${btnBase} bg-red-500 text-white hover:bg-red-600`;

// ─── Empty form template ───────────────────────────────────────────

const emptyAssetForm = {
  name: '',
  category: '',
  location: '',
  purchase_date: '',
  purchase_price: '',
};

// ─── Status / maintenance helpers ──────────────────────────────────

const statusMap = {
  active: { l: 'assetActive', c: 'green' },
  in_maintenance: { l: 'assetInMaintenance', c: 'yellow' },
  disposed: { l: 'assetDisposed', c: 'gray' },
  sold: { l: 'assetSold', c: 'blue' },
};

const mStatusMap = {
  completed: { l: 'completed', c: 'green' },
  in_progress: { l: 'inProgress', c: 'yellow' },
  pending: { l: 'pending', c: 'gray' },
};

// ─── Main Page ─────────────────────────────────────────────────────

export default function AssetsPage() {
  const { t, locale } = useI18n();
  const numberLocale = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (n) => Number(n || 0).toLocaleString(numberLocale);

  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // ── Assets data (Tab 1) ──
  const [assets, setAssets] = useState([]);
  const [loadingAssets, setLoadingAssets] = useState(true);
  const [searchAssets, setSearchAssets] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // ── Categories data (Tab 2) ──
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [searchCategories, setSearchCategories] = useState('');

  // ── Maintenance data (Tab 3) ──
  const [maintenances, setMaintenances] = useState([]);
  const [loadingMaintenances, setLoadingMaintenances] = useState(false);
  const [searchMaintenance, setSearchMaintenance] = useState('');

  // ── Stats ──
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  // ── Create Asset modal ──
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [assetForm, setAssetForm] = useState(emptyAssetForm);
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // ── Delete confirmation ──
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // ── Detail modal ──
  const [detailAsset, setDetailAsset] = useState(null);

  // ── Pagination ──
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // ─── Tab definitions ────────────────────────────────────────────
  const tabs = [
    { label: t('assetTabAssets'), icon: Building2 },
    { label: t('assetTabCategories'), icon: DollarSign },
    { label: t('assetTabMaintenance'), icon: Wrench },
  ];

  // ─── API Calls ──────────────────────────────────────────────────

  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const res = await assetsAPI.getStats();
      setStats(res.data);
    } catch {
      // silent fail
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const fetchAssets = useCallback(async (page = 1) => {
    setLoadingAssets(true);
    try {
      const params = {
        page,
        search: searchAssets || undefined,
        status: statusFilter || undefined,
      };
      const res = await assetsAPI.getAssets(params);
      const data = res.data;
      if (data.results) {
        setAssets(data.results);
        setTotalCount(data.count);
      } else {
        setAssets(Array.isArray(data) ? data : []);
        setTotalCount(data.length || 0);
      }
      setCurrentPage(page);
    } catch {
      toast.error(t('assetLoadFailed'));
    } finally {
      setLoadingAssets(false);
    }
  }, [searchAssets, statusFilter, t]);

  const fetchCategories = useCallback(async () => {
    setLoadingCategories(true);
    try {
      const res = await assetsAPI.getCategories({ search: searchCategories || undefined });
      const data = res.data;
      setCategories(data.results || (Array.isArray(data) ? data : []));
    } catch {
      toast.error(t('assetLoadFailed'));
    } finally {
      setLoadingCategories(false);
    }
  }, [searchCategories, t]);

  const fetchMaintenances = useCallback(async () => {
    setLoadingMaintenances(true);
    try {
      const res = await assetsAPI.getMaintenances({ search: searchMaintenance || undefined });
      const data = res.data;
      setMaintenances(data.results || (Array.isArray(data) ? data : []));
    } catch {
      toast.error(t('assetLoadFailed'));
    } finally {
      setLoadingMaintenances(false);
    }
  }, [searchMaintenance, t]);

  // ─── Effects ────────────────────────────────────────────────────

  useEffect(() => {
    fetchStats();
    fetchAssets(1);
  }, [fetchStats, fetchAssets]);

  useEffect(() => {
    if (activeTab === 1) fetchCategories();
  }, [activeTab, fetchCategories]);

  useEffect(() => {
    if (activeTab === 2) fetchMaintenances();
  }, [activeTab, fetchMaintenances]);

  // ─── Form handling ──────────────────────────────────────────────

  const openCreateModal = () => {
    setAssetForm(emptyAssetForm);
    setFormErrors({});
    setShowCreateModal(true);
  };

  const closeModal = () => {
    setShowCreateModal(false);
    setAssetForm(emptyAssetForm);
    setFormErrors({});
  };

  const validateForm = () => {
    const errors = {};
    if (!assetForm.name.trim()) errors.name = t('required');
    if (!assetForm.purchase_date) errors.purchase_date = t('required');
    if (!assetForm.purchase_price || Number(assetForm.purchase_price) <= 0)
      errors.purchase_price = t('required');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setFormLoading(true);
    try {
      await assetsAPI.createAsset({
        ...assetForm,
        purchase_price: parseFloat(assetForm.purchase_price),
      });
      toast.success(t('assetCreated'));
      closeModal();
      fetchAssets(currentPage);
      fetchStats();
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const fieldErrors = {};
        Object.keys(data).forEach((key) => {
          if (key !== 'message' && key !== 'error') {
            fieldErrors[key] = Array.isArray(data[key]) ? data[key][0] : data[key];
          }
        });
        if (Object.keys(fieldErrors).length > 0) {
          setFormErrors(fieldErrors);
        } else {
          toast.error(data.message || data.error || t('operationFailed'));
        }
      } else {
        toast.error(t('operationFailed'));
      }
    } finally {
      setFormLoading(false);
    }
  };

  // ─── Delete handling ────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await assetsAPI.deleteAsset(deleteConfirm.id);
      toast.success(t('assetDeleted'));
      setDeleteConfirm(null);
      fetchAssets(currentPage);
      fetchStats();
    } catch {
      toast.error(t('operationFailed'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // ─── Depreciate all ─────────────────────────────────────────────

  const handleDepreciate = async () => {
    try {
      await assetsAPI.depreciateAll();
      toast.success(t('assetDepreciateSuccess'));
      fetchStats();
      fetchAssets(currentPage);
    } catch {
      toast.error(t('operationFailed'));
    }
  };

  // ─── Export ─────────────────────────────────────────────────────

  const handleExport = async () => {
    try {
      const res = await assetsAPI.export();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'assets.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(t('dataExported'));
    } catch {
      toast.error(t('exportError'));
    }
  };

  // ─── Pagination ────────────────────────────────────────────────

  const totalPages = Math.ceil(totalCount / pageSize);

  // ─── Render ─────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('assetManageAssets')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('assetManageAssetsDesc')}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleDepreciate}
            className={btnSecondary}
          >
            <Calculator className="w-4 h-4" /> {t('assetDepreciate')}
          </button>
          <button
            onClick={handleExport}
            className={btnSecondary}
          >
            <Download className="w-4 h-4" /> {t('export')}
          </button>
          <button
            onClick={openCreateModal}
            className={btnPrimary}
          >
            <Plus className="w-4 h-4" /> {t('assetNewAsset')}
          </button>
        </div>
      </div>

      {/* Stats cards */}
      {loadingStats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-gray-200 dark:bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={Building2}
            label={t('assetTotalAssets')}
            value={stats.total_assets ?? 0}
            color="from-riadah-400 to-riadah-500"
          />
          <StatCard
            icon={DollarSign}
            label={t('assetTotalValue')}
            value={`${fmt(stats.total_value ?? 0)} ${t('sar')}`}
            color="from-emerald-500 to-emerald-600"
          />
          <StatCard
            icon={TrendingDown}
            label={t('assetDepreciatedValue')}
            value={`${fmt(stats.depreciated_value ?? 0)} ${t('sar')}`}
            color="from-amber-500 to-amber-600"
          />
          <StatCard
            icon={Wrench}
            label={t('assetMaintenanceCount')}
            value={stats.maintenance_count ?? 0}
            color="from-violet-500 to-violet-600"
          />
        </div>
      ) : null}

      {/* Tabs container */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          {tabs.map((tab, i) => (
            <button
              key={i}
              onClick={() => setActiveTab(i)}
              className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium whitespace-nowrap transition-all border-b-2 ${
                activeTab === i
                  ? 'border-accent-500 text-accent-500 dark:text-accent-400 bg-riadah-50/50 dark:bg-riadah-900/20'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>

        <div className="p-4 md:p-6">
          {/* ── Tab 1: Assets ── */}
          {activeTab === 0 && (
            <div className="space-y-4">
              {/* Search & filter bar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <div className="relative flex-1">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    value={searchAssets}
                    onChange={(e) => { setSearchAssets(e.target.value); setCurrentPage(1); }}
                    className={`${inputCls} !pr-10`}
                    placeholder={t('assetSearchAssets')}
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
                  className={inputCls}
                  style={{ maxWidth: 180 }}
                >
                  <option value="">{t('assetAllStatuses')}</option>
                  {Object.entries(statusMap).map(([k, v]) => (
                    <option key={k} value={k}>{t(v.l)}</option>
                  ))}
                </select>
              </div>

              {/* Table */}
              {loadingAssets ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
                </div>
              ) : assets.length === 0 ? (
                <div className="text-center py-20 text-gray-400 dark:text-gray-500">
                  <PackageOpen className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                  <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('assetNoAssets')}</p>
                  <p className="text-sm mt-1 text-gray-400 dark:text-gray-500">
                    {searchAssets ? t('noSearchResults') : t('tryAgain')}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-400">
                        {[t('assetNumber'), t('assetName'), t('assetCategory'), t('assetPurchaseDate'), t('assetPurchasePrice'), t('assetCurrentValue'), t('assetStatus'), t('assetLocation'), t('actions')].map((h) => (
                          <th key={h} className="px-3 py-3 text-right font-medium whitespace-nowrap text-xs uppercase">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {assets.map((a) => (
                        <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                          <td className="px-3 py-3 text-accent-500 font-medium font-mono">{a.asset_number || '—'}</td>
                          <td className="px-3 py-3 font-medium text-gray-800 dark:text-white">{a.name}</td>
                          <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{a.category_name || a.category || '—'}</td>
                          <td className="px-3 py-3 text-gray-600 dark:text-gray-400 whitespace-nowrap">{a.purchase_date || '—'}</td>
                          <td className="px-3 py-3 text-gray-800 dark:text-gray-200" dir="ltr">{fmt(a.purchase_price)}</td>
                          <td className="px-3 py-3 font-medium text-gray-800 dark:text-gray-200" dir="ltr">{fmt(a.current_value)}</td>
                          <td className="px-3 py-3">
                            <Badge color={statusMap[a.status]?.c || 'gray'}>
                              {t(statusMap[a.status]?.l || a.status)}
                            </Badge>
                          </td>
                          <td className="px-3 py-3 text-gray-600 dark:text-gray-400 max-w-[140px] truncate">{a.location || '—'}</td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => setDetailAsset(a)}
                                className="p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 text-accent-500"
                                title={t('view')}
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(a)}
                                className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"
                                title={t('delete')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700 mt-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('showing')} {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} {t('of')} {totalCount}
                  </p>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => fetchAssets(currentPage - 1)}
                      disabled={currentPage <= 1}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-500 dark:text-gray-400"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                    <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      onClick={() => fetchAssets(currentPage + 1)}
                      disabled={currentPage >= totalPages}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-500 dark:text-gray-400"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Tab 2: Categories (read-only) ── */}
          {activeTab === 1 && (
            <div className="space-y-4">
              <div className="relative max-w-md">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  value={searchCategories}
                  onChange={(e) => setSearchCategories(e.target.value)}
                  className={`${inputCls} !pr-10`}
                  placeholder={t('assetSearchCategories')}
                />
              </div>

              {loadingCategories ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
                </div>
              ) : categories.length === 0 ? (
                <div className="text-center py-16 text-gray-400 dark:text-gray-500">
                  <PackageOpen className="w-14 h-14 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                  <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('assetNoCategories')}</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-400">
                        {[t('assetCategoryName'), t('assetUsefulLife'), t('assetDepreciationMethod'), t('assetSalvageRate')].map((h) => (
                          <th key={h} className="px-4 py-3 text-right font-medium whitespace-nowrap text-xs uppercase">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {categories.map((c) => (
                        <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">{c.name}</td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{c.useful_life} {t('assetYears')}</td>
                          <td className="px-4 py-3">
                            <Badge color="blue">{c.depreciation_method}</Badge>
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{c.salvage_rate}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── Tab 3: Maintenance (read-only) ── */}
          {activeTab === 2 && (
            <div className="space-y-4">
              <div className="relative max-w-md">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  value={searchMaintenance}
                  onChange={(e) => setSearchMaintenance(e.target.value)}
                  className={`${inputCls} !pr-10`}
                  placeholder={t('assetSearchMaintenance')}
                />
              </div>

              {loadingMaintenances ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
                </div>
              ) : maintenances.length === 0 ? (
                <div className="text-center py-16 text-gray-400 dark:text-gray-500">
                  <PackageOpen className="w-14 h-14 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                  <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('assetNoMaintenance')}</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-400">
                        {[t('assetName'), t('assetMaintenanceType'), t('description'), t('assetMaintenanceCost'), t('date'), t('assetMaintenanceNextDate'), t('status')].map((h) => (
                          <th key={h} className="px-4 py-3 text-right font-medium whitespace-nowrap text-xs uppercase">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {maintenances.map((m) => (
                        <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">{m.asset_name || m.asset || '—'}</td>
                          <td className="px-4 py-3">
                            <Badge color="violet">{m.type}</Badge>
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400 max-w-[220px] truncate">{m.description || '—'}</td>
                          <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200" dir="ltr">{fmt(m.cost)}</td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400 whitespace-nowrap">{m.date || '—'}</td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400 whitespace-nowrap">{m.next_date || '—'}</td>
                          <td className="px-4 py-3">
                            <Badge color={mStatusMap[m.status]?.c || 'gray'}>
                              {t(mStatusMap[m.status]?.l || m.status)}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Create Asset Modal ── */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={closeModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('assetNewAsset')}</h3>
              <button onClick={closeModal} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {/* Asset name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('assetName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={assetForm.name}
                  onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-xl focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${
                    formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                  }`}
                  placeholder={t('assetName')}
                />
                {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
              </div>

              {/* Category & Location */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('assetCategory')}</label>
                  <select
                    value={assetForm.category}
                    onChange={(e) => setAssetForm({ ...assetForm, category: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-xl focus:ring-2 focus:ring-accent-500"
                  >
                    <option value="">—</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('assetLocation')}</label>
                  <input
                    type="text"
                    value={assetForm.location}
                    onChange={(e) => setAssetForm({ ...assetForm, location: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-xl focus:ring-2 focus:ring-accent-500"
                    placeholder={t('assetLocation')}
                  />
                </div>
              </div>

              {/* Purchase date & price */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('assetPurchaseDate')} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={assetForm.purchase_date}
                    onChange={(e) => setAssetForm({ ...assetForm, purchase_date: e.target.value })}
                    className={`w-full px-3 py-2.5 border rounded-xl focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${
                      formErrors.purchase_date ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                    }`}
                  />
                  {formErrors.purchase_date && <p className="text-red-500 text-xs mt-1">{formErrors.purchase_date}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('assetPurchasePrice')} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={assetForm.purchase_price}
                    onChange={(e) => setAssetForm({ ...assetForm, purchase_price: e.target.value })}
                    dir="ltr"
                    className={`w-full px-3 py-2.5 border rounded-xl focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-left ${
                      formErrors.purchase_price ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                    }`}
                    placeholder="0.00"
                  />
                  {formErrors.purchase_price && <p className="text-red-500 text-xs mt-1">{formErrors.purchase_price}</p>}
                </div>
              </div>

              {/* Modal footer */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-riadah-500 hover:bg-riadah-600 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  {formLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}</>
                  ) : (
                    <><Plus className="w-4 h-4" /> {t('add')}</>
                  )}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Asset Detail Modal ── */}
      {detailAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDetailAsset(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('assetDetails')}</h3>
              <button onClick={() => setDetailAsset(null)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {[
                  [t('assetNumber'), detailAsset.asset_number || '—'],
                  [t('assetName'), detailAsset.name],
                  [t('assetCategory'), detailAsset.category_name || detailAsset.category || '—'],
                  [t('assetLocation'), detailAsset.location || '—'],
                ].map(([label, value]) => (
                  <div key={label}>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                    <p className="font-medium text-gray-800 dark:text-white">{value}</p>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-riadah-50 dark:bg-riadah-900/20 rounded-xl p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t('assetPurchasePrice')}</p>
                  <p className="text-lg font-bold text-accent-500" dir="ltr">{fmt(detailAsset.purchase_price)}</p>
                </div>
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t('assetCurrentValue')}</p>
                  <p className="text-lg font-bold text-emerald-600" dir="ltr">{fmt(detailAsset.current_value)}</p>
                </div>
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t('assetDepreciation')}</p>
                  <p className="text-lg font-bold text-amber-600" dir="ltr">
                    {fmt((detailAsset.purchase_price || 0) - (detailAsset.current_value || 0))}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">{t('assetStatus')}:</span>{' '}
                  <Badge color={statusMap[detailAsset.status]?.c || 'gray'}>
                    {t(statusMap[detailAsset.status]?.l || detailAsset.status)}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ── */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <Trash2 className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirmDelete')}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                {t('confirmDeleteMessage')}{' '}
                <span className="font-semibold text-gray-900 dark:text-gray-100">"{deleteConfirm.name}"</span>?
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteLoading}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  {deleteLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</>
                  ) : (
                    <><Trash2 className="w-4 h-4" /> {t('delete')}</>
                  )}
                </button>
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
