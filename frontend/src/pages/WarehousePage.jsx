/**
 * Warehouse page - warehouse & inventory management.
 * Features: 3-tab layout (Warehouses, Stock, Transfers), stats cards,
 * search/filter, create warehouse modal.
 * Uses real API via warehouseAPI. Supports dark mode, RTL, i18n.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { warehouseAPI } from '../api';
import {
  Warehouse, Package, AlertTriangle, DollarSign, Plus, Search, Filter,
  ArrowLeftRight, Download, X, Loader2, MapPin, User,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Helpers ──────────────────────────────────────────────────────
const numberLocale = (locale) => (locale === 'ar' ? 'ar-SA' : 'en-US');

const formatCurrency = (value, locale) => {
  if (value == null) return '—';
  return Number(value).toLocaleString(numberLocale(locale), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

// Status badge mapping for stock items
const stockStatusMap = {
  good: { ar: 'جيد', en: 'Good', color: 'green' },
  low: { ar: 'منخفض', en: 'Low', color: 'red' },
  warning: { ar: 'تحذير', en: 'Warning', color: 'yellow' },
  out_of_stock: { ar: 'نفذ', en: 'Out', color: 'red' },
};

// Status badge mapping for transfers
const transferStatusMap = {
  pending: { ar: 'معلق', en: 'Pending', color: 'yellow' },
  approved: { ar: 'معتمد', en: 'Approved', color: 'blue' },
  received: { ar: 'مستلم', en: 'Received', color: 'green' },
  cancelled: { ar: 'ملغي', en: 'Cancelled', color: 'gray' },
  in_transit: { ar: 'قيد التحويل', en: 'In Transit', color: 'blue' },
};

// ─── Shared UI Components ─────────────────────────────────────────
const Badge = ({ children, color = 'blue' }) => {
  const colors = {
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    yellow: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    blue: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/40 dark:text-accent-300',
    gray: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300',
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${colors[color] || colors.blue}`}>
      {children}
    </span>
  );
};

const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-20">
    <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
  </div>
);

const EmptyState = ({ icon: Icon, message, subMessage }) => (
  <div className="text-center py-20 text-gray-400 dark:text-gray-500">
    <Icon className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
    <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{message}</p>
    {subMessage && <p className="text-sm mt-1 text-gray-400 dark:text-gray-500">{subMessage}</p>}
  </div>
);

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div
        className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
};

const inputClass =
  'w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition';
const selectClass = inputClass;
const btnPrimary =
  'inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-riadah-500 hover:bg-riadah-600 text-white shadow-sm transition-all duration-200 disabled:opacity-50';
const btnSecondary =
  'inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200';

// ─── Main Page ────────────────────────────────────────────────────
export default function WarehousePage() {
  const { isWarehouse } = useAuth();
  const { t, locale } = useI18n();

  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // Stats
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Tab data states
  const [warehouses, setWarehouses] = useState([]);
  const [warehousesLoading, setWarehousesLoading] = useState(true);

  const [stock, setStock] = useState([]);
  const [stockLoading, setStockLoading] = useState(false);

  const [transfers, setTransfers] = useState([]);
  const [transfersLoading, setTransfersLoading] = useState(false);

  // Search
  const [searchTerm, setSearchTerm] = useState('');

  // Create warehouse modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', code: '', location: '', manager: '' });
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // i18n helper with fallback
  const tx = (key, arFallback, enFallback) => {
    const val = t(key);
    // If translation is missing (returns the key itself), use fallback
    if (val === key) {
      return locale === 'ar' ? arFallback : enFallback;
    }
    return val;
  };

  // ─── Fetch functions ───
  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const response = await warehouseAPI.getStats();
      setStats(response.data);
    } catch {
      // silent fail
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const fetchWarehouses = useCallback(async () => {
    setWarehousesLoading(true);
    try {
      const params = searchTerm ? { search: searchTerm } : undefined;
      const response = await warehouseAPI.getWarehouses(params);
      const data = response.data;
      if (data.results) {
        setWarehouses(data.results);
      } else {
        setWarehouses(Array.isArray(data) ? data : []);
      }
    } catch {
      toast.error(tx('whLoadFailed', 'فشل تحميل البيانات', 'Failed to load data'));
    } finally {
      setWarehousesLoading(false);
    }
  }, [searchTerm, t, locale]);

  const fetchStock = useCallback(async () => {
    setStockLoading(true);
    try {
      const params = searchTerm ? { search: searchTerm } : undefined;
      const response = await warehouseAPI.listStock(params);
      const data = response.data;
      if (data.results) {
        setStock(data.results);
      } else {
        setStock(Array.isArray(data) ? data : []);
      }
    } catch {
      toast.error(tx('whLoadFailed', 'فشل تحميل البيانات', 'Failed to load data'));
    } finally {
      setStockLoading(false);
    }
  }, [searchTerm, t, locale]);

  const fetchTransfers = useCallback(async () => {
    setTransfersLoading(true);
    try {
      const params = searchTerm ? { search: searchTerm } : undefined;
      const response = await warehouseAPI.getTransfers(params);
      const data = response.data;
      if (data.results) {
        setTransfers(data.results);
      } else {
        setTransfers(Array.isArray(data) ? data : []);
      }
    } catch {
      toast.error(tx('whLoadFailed', 'فشل تحميل البيانات', 'Failed to load data'));
    } finally {
      setTransfersLoading(false);
    }
  }, [searchTerm, t, locale]);

  // Load stats + initial tab data on mount
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    if (activeTab === 0) fetchWarehouses();
    else if (activeTab === 1) fetchStock();
    else if (activeTab === 2) fetchTransfers();
  }, [activeTab, fetchWarehouses, fetchStock, fetchTransfers]);

  // ─── Create warehouse ───
  const handleCreateWarehouse = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!formData.name.trim()) errors.name = locale === 'ar' ? 'اسم المستودع مطلوب' : 'Warehouse name is required';
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setFormLoading(true);
    try {
      await warehouseAPI.createWarehouse({
        name: formData.name.trim(),
        code: formData.code.trim() || undefined,
        location: formData.location.trim() || undefined,
        manager: formData.manager.trim() || undefined,
      });
      toast.success(tx('whWarehouseCreated', 'تم إنشاء المستودع بنجاح', 'Warehouse created successfully'));
      setShowCreateModal(false);
      setFormData({ name: '', code: '', location: '', manager: '' });
      setFormErrors({});
      fetchWarehouses();
      fetchStats();
    } catch (error) {
      const data = error.response?.data;
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
          toast.error(data.message || data.error || tx('whLoadFailed', 'حدث خطأ', 'An error occurred'));
        }
      } else {
        toast.error(tx('whLoadFailed', 'حدث خطأ', 'An error occurred'));
      }
    } finally {
      setFormLoading(false);
    }
  };

  // ─── Tab definitions ───
  const tabs = [
    {
      label: tx('whTabWarehouses', 'المستودعات', 'Warehouses'),
      icon: Warehouse,
    },
    {
      label: tx('whTabStock', 'أرصدة المخزون', 'Stock'),
      icon: Package,
    },
    {
      label: tx('whTabTransfers', 'التحويلات', 'Transfers'),
      icon: ArrowLeftRight,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {tx('whManageWarehouses', 'إدارة المستودعات', 'Warehouse Management')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {tx('whManageWarehousesDesc', 'إدارة المستودعات والمخزون والتحويلات والجرد', 'Manage warehouses, stock, and transfers')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isWarehouse && (
            <button
              onClick={() => {
                setFormData({ name: '', code: '', location: '', manager: '' });
                setFormErrors({});
                setShowCreateModal(true);
              }}
              className={btnPrimary}
            >
              <Plus className="w-4 h-4" />
              {tx('whNewWarehouse', 'مستودع جديد', 'New Warehouse')}
            </button>
          )}
        </div>
      </div>

      {/* Stats cards */}
      {statsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-gray-200 dark:bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={Warehouse}
            label={tx('whTotalWarehouses', 'إجمالي المستودعات', 'Total Warehouses')}
            value={stats.total_warehouses ?? stats.total_warehouses || '—'}
            color="from-riadah-500 to-riadah-600"
          />
          <StatCard
            icon={Package}
            label={tx('whTotalProducts', 'إجمالي المنتجات', 'Total Products')}
            value={stats.total_products ?? stats.total_products || '—'}
            color="from-emerald-500 to-emerald-600"
          />
          <StatCard
            icon={AlertTriangle}
            label={tx('whLowStock', 'مخزون منخفض', 'Low Stock')}
            value={stats.low_stock_count ?? stats.low_stock_products ?? stats.low_stock ?? '—'}
            color="from-amber-500 to-amber-600"
          />
          <StatCard
            icon={DollarSign}
            label={tx('whTotalStockValue', 'قيمة المخزون', 'Stock Value')}
            value={
              stats.total_stock_value != null
                ? `${formatCurrency(stats.total_stock_value / 1000, locale)}K`
                : '—'
            }
            color="from-violet-500 to-violet-600"
          />
        </div>
      ) : null}

      {/* Tabs container */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {/* Tab navigation */}
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
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-4 md:p-6">
          {activeTab === 0 && (
            <WarehousesTab
              warehouses={warehouses}
              loading={warehousesLoading}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              locale={locale}
              tx={tx}
            />
          )}
          {activeTab === 1 && (
            <StockTab
              stock={stock}
              loading={stockLoading}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              locale={locale}
              tx={tx}
            />
          )}
          {activeTab === 2 && (
            <TransfersTab
              transfers={transfers}
              loading={transfersLoading}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              locale={locale}
              tx={tx}
            />
          )}
        </div>
      </div>

      {/* Create Warehouse Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={tx('whNewWarehouse', 'إنشاء مستودع جديد', 'Create New Warehouse')}
      >
        <form onSubmit={handleCreateWarehouse} className="space-y-4">
          {/* Warehouse name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {tx('whWarehouseName', 'اسم المستودع', 'Warehouse Name')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`${inputClass} ${formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : ''}`}
              placeholder={locale === 'ar' ? 'أدخل اسم المستودع' : 'Enter warehouse name'}
            />
            {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
          </div>

          {/* Code + Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {tx('whWarehouseCode', 'الرمز', 'Code')}
              </label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className={`${inputClass} ${formErrors.code ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : ''}`}
                placeholder="WH-001"
                dir="ltr"
              />
              {formErrors.code && <p className="text-red-500 text-xs mt-1">{formErrors.code}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {tx('whWarehouseLocation', 'الموقع', 'Location')}
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className={`${inputClass} ${formErrors.location ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : ''}`}
                placeholder={locale === 'ar' ? 'المدينة' : 'City'}
              />
              {formErrors.location && <p className="text-red-500 text-xs mt-1">{formErrors.location}</p>}
            </div>
          </div>

          {/* Manager */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {tx('whWarehouseManager', 'المسؤول', 'Manager')}
            </label>
            <input
              type="text"
              value={formData.manager}
              onChange={(e) => setFormData({ ...formData, manager: e.target.value })}
              className={`${inputClass} ${formErrors.manager ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : ''}`}
              placeholder={locale === 'ar' ? 'اسم المسؤول' : 'Manager name'}
            />
            {formErrors.manager && <p className="text-red-500 text-xs mt-1">{formErrors.manager}</p>}
          </div>

          {/* Form footer */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={formLoading}
              className="flex-1 bg-riadah-500 hover:bg-riadah-600 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {formLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              {tx('create', 'إنشاء', 'Create')}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className={btnSecondary}
            >
              {tx('cancel', 'إلغاء', 'Cancel')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

// ─── Stat Card ─────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl p-4 md:p-5 bg-gradient-to-br ${color} text-white shadow-lg`}
    >
      <div className="absolute top-0 left-0 w-24 h-24 bg-white/10 rounded-full -translate-x-8 -translate-y-8" />
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-white/20">
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs opacity-80">{label}</p>
          <p className="text-xl font-bold mt-0.5">{value}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Warehouses Tab ───────────────────────────────────────────────
function WarehousesTab({ warehouses, loading, searchTerm, setSearchTerm, locale, tx }) {
  // Client-side filtering as additional safety (API may also filter)
  const filtered = warehouses.filter(
    (w) =>
      !searchTerm ||
      (w.name && w.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (w.code && w.code.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (w.location && w.location.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) return <LoadingSpinner />;

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={Warehouse}
        message={tx('whNoWarehouses', 'لا توجد مستودعات', 'No warehouses found')}
        subMessage={
          searchTerm
            ? locale === 'ar'
              ? 'لا توجد نتائج لبحثك'
              : 'No results for your search'
            : locale === 'ar'
              ? 'ابدأ بإضافة مستودع جديد'
              : 'Start by adding a new warehouse'
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
            placeholder={tx('whSearchWarehouses', 'بحث في المستودعات...', 'Search warehouses...')}
          />
        </div>
      </div>

      {/* Warehouse cards grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((w) => (
          <div
            key={w.id}
            className="bg-gradient-to-br from-gray-50 to-white dark:from-gray-800/50 dark:to-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-bold text-gray-800 dark:text-white">{w.name}</h3>
                {w.code && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-mono">{w.code}</p>
                )}
              </div>
              {w.location && (
                <span className="text-xs bg-riadah-100 dark:bg-riadah-900/40 text-accent-500 dark:text-accent-300 px-2 py-1 rounded-full flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {w.location}
                </span>
              )}
            </div>

            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              {w.manager && (
                <p className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span className="text-gray-800 dark:text-gray-200">{w.manager}</span>
                </p>
              )}
              {w.products_count != null && (
                <p className="flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  <span className="text-gray-800 dark:text-gray-200">{w.products_count}</span>
                  <span>{tx('whProductsCount', 'منتج', 'product(s)')}</span>
                </p>
              )}
            </div>

            {/* Capacity bar */}
            {w.utilized_capacity != null && (
              <div className="mt-3">
                <div className="flex justify-between text-xs mb-1">
                  <span>{tx('whUsedCapacity', 'السعة المستخدمة', 'Used Capacity')}</span>
                  <span
                    className={
                      w.utilized_capacity > 85
                        ? 'text-red-500 font-bold'
                        : 'text-gray-600 dark:text-gray-400'
                    }
                  >
                    {w.utilized_capacity}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      w.utilized_capacity > 85
                        ? 'bg-red-500'
                        : w.utilized_capacity > 60
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                    }`}
                    style={{ width: `${w.utilized_capacity}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Stock Tab ─────────────────────────────────────────────────────
function StockTab({ stock, loading, searchTerm, setSearchTerm, locale, tx }) {
  // Client-side filtering as additional safety
  const filtered = stock.filter(
    (s) =>
      !searchTerm ||
      (s.product_name && s.product_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.warehouse && s.warehouse.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.product && s.product.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) return <LoadingSpinner />;

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={Package}
        message={tx('whNoStock', 'لا توجد أرصدة', 'No stock items found')}
        subMessage={
          searchTerm
            ? locale === 'ar'
              ? 'لا توجد نتائج لبحثك'
              : 'No results for your search'
            : null
        }
      />
    );
  }

  const headers = [
    tx('whStockProduct', 'المنتج', 'Product'),
    tx('whStockWarehouse', 'المستودع', 'Warehouse'),
    tx('whStockQuantity', 'الكمية', 'Quantity'),
    tx('whStockReserved', 'محجوز', 'Reserved'),
    tx('whStockAvailable', 'متاح', 'Available'),
    tx('whStockMinLevel', 'الحد الأدنى', 'Min Level'),
    tx('status', 'الحالة', 'Status'),
  ];

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
            placeholder={tx('whSearchStock', 'بحث في المنتجات...', 'Search products...')}
          />
        </div>
      </div>

      {/* Stock table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
              {headers.map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {filtered.map((s) => {
              const productName = s.product_name || s.product || '—';
              const warehouseName = s.warehouse_name || s.warehouse || '—';
              const statusInfo = stockStatusMap[s.status] || stockStatusMap.good;
              const statusLabel =
                s.status_display || statusInfo[locale] || statusInfo.en;

              return (
                <tr
                  key={s.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">
                    {productName}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {warehouseName}
                  </td>
                  <td className="px-4 py-3 text-gray-800 dark:text-gray-200">
                    {s.quantity ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-amber-600 dark:text-amber-400">
                    {s.reserved ?? 0}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">
                    {s.available ?? s.quantity ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {s.min_stock ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <Badge color={statusInfo.color}>{statusLabel}</Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Transfers Tab ─────────────────────────────────────────────────
function TransfersTab({ transfers, loading, searchTerm, setSearchTerm, locale, tx }) {
  const [statusFilter, setStatusFilter] = useState('all');

  // Client-side filtering
  const filtered = transfers.filter(
    (tr) =>
      (statusFilter === 'all' || tr.status === statusFilter) &&
      (!searchTerm ||
        (tr.transfer_number && tr.transfer_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (tr.from_warehouse_name || tr.from_warehouse || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (tr.to_warehouse_name || tr.to_warehouse || '').toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) return <LoadingSpinner />;

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={ArrowLeftRight}
        message={tx('whNoTransfers', 'لا توجد تحويلات', 'No transfers found')}
        subMessage={
          searchTerm
            ? locale === 'ar'
              ? 'لا توجد نتائج لبحثك'
              : 'No results for your search'
            : null
        }
      />
    );
  }

  const headers = [
    tx('whTransferNumber', 'رقم التحويل', 'Transfer #'),
    tx('whTransferFrom', 'من', 'From'),
    tx('whTransferTo', 'إلى', 'To'),
    tx('status', 'الحالة', 'Status'),
    tx('whTransferItems', 'عدد الأصناف', 'Items'),
    tx('date', 'التاريخ', 'Date'),
  ];

  return (
    <div className="space-y-4">
      {/* Search + status filter */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
            placeholder={tx('whSearchTransfers', 'بحث في التحويلات...', 'Search transfers...')}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={selectClass}
        >
          <option value="all">{tx('whAllStatuses', 'جميع الحالات', 'All Statuses')}</option>
          {Object.entries(transferStatusMap).map(([key, val]) => (
            <option key={key} value={key}>
              {val[locale] || val.en}
            </option>
          ))}
        </select>
      </div>

      {/* Transfers table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
              {headers.map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {filtered.map((tr) => {
              const fromName = tr.from_warehouse_name || tr.from_warehouse || '—';
              const toName = tr.to_warehouse_name || tr.to_warehouse || '—';
              const statusInfo = transferStatusMap[tr.status] || transferStatusMap.pending;
              const statusLabel =
                tr.status_display || statusInfo[locale] || statusInfo.en;
              const dateVal = tr.created_at || tr.date || tr.transfer_date || '—';

              return (
                <tr
                  key={tr.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-gray-800 dark:text-white font-mono">
                    {tr.transfer_number || '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{fromName}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{toName}</td>
                  <td className="px-4 py-3">
                    <Badge color={statusInfo.color}>{statusLabel}</Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-800 dark:text-gray-200">
                    {tr.items_count ?? tr.total_items ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {typeof dateVal === 'string' ? dateVal.split('T')[0] : dateVal}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
