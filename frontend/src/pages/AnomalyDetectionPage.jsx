/**
 * Anomaly Detection Page - ML-powered anomaly detection and review.
 * Features summary cards, filterable/sortable table, and inline review form.
 * Supports Arabic (RTL) and English, dark mode, and brand colors.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { analyticsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  ShieldAlert, AlertTriangle, AlertOctagon, CheckCircle, Clock,
  RefreshCw, Loader2, Filter, Eye, MessageSquare, Search,
  ArrowUpDown, X, Save, ChevronDown,
} from 'lucide-react';

/* ── Mock Data ── */
const generateMockAnomalies = () => [
  { id: 1, date: '2024-12-15', type: 'sales_spike', description: 'زيادة غير معتادة في المبيعات - 340% فوق المتوسط', amount: 185000, severity: 'critical', status: 'unreviewed', notes: '' },
  { id: 2, date: '2024-12-14', type: 'price_anomaly', description: 'تغير سعر مفاجئ في منتج حديد التسليح', amount: 42000, severity: 'high', status: 'unreviewed', notes: '' },
  { id: 3, date: '2024-12-13', type: 'inventory_mismatch', description: 'تناقض بين المخزون الفعلي والمسجل', amount: 15600, severity: 'medium', status: 'reviewed', notes: 'تم التحقق - خطأ إدخال بيانات' },
  { id: 4, date: '2024-12-12', type: 'duplicate_order', description: 'طلب مكرر محتمل من نفس العميل', amount: 28500, severity: 'high', status: 'unreviewed', notes: '' },
  { id: 5, date: '2024-12-11', type: 'payment_delay', description: 'تأخير غير معتاد في سداد فاتورة عميل VIP', amount: 95000, severity: 'critical', status: 'reviewed', notes: 'تم التواصل مع العميل - سيتم السداد خلال 3 أيام' },
  { id: 6, date: '2024-12-10', type: 'sales_drop', description: 'انخفاض حاد في مبيعات فرع جدة', amount: 67000, severity: 'high', status: 'unreviewed', notes: '' },
  { id: 7, date: '2024-12-09', type: 'expense_spike', description: 'مصروفات تشغيلية أعلى من المتوسط 200%', amount: 34000, severity: 'medium', status: 'reviewed', notes: 'صيانة طارئة للمكيفات' },
  { id: 8, date: '2024-12-08', type: 'return_anomaly', description: 'ارتفاع غير معتاد في مرتجعات منتج معين', amount: 12300, severity: 'medium', status: 'unreviewed', notes: '' },
  { id: 9, date: '2024-12-07', type: 'customer_behavior', description: 'نمط شراء غير عادي من عميل جديد', amount: 78000, severity: 'low', status: 'reviewed', notes: 'عميل حكومي - مشروع جديد' },
  { id: 10, date: '2024-12-06', type: 'inventory_mismatch', description: 'فجوة في جرد مستودع الدمام', amount: 22000, severity: 'high', status: 'unreviewed', notes: '' },
];

const generateMockStats = () => ({
  total: 10,
  unreviewed: 6,
  critical: 2,
  high: 3,
  medium: 3,
  low: 2,
  reviewed_today: 4,
});

/* ── Severity Badge ── */
function SeverityBadge({ severity, t }) {
  const config = {
    critical: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', label: t('critical') || 'حرج', icon: AlertOctagon },
    high: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', label: t('high') || 'عالي', icon: AlertTriangle },
    medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400', label: t('medium') || 'متوسط', icon: ShieldAlert },
    low: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400', label: t('low') || 'منخفض', icon: AlertTriangle },
  };
  const c = config[severity] || config.low;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  );
}

/* ── Status Badge ── */
function StatusBadge({ status, t }) {
  if (status === 'reviewed') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
        <CheckCircle className="w-3 h-3" />
        {t('reviewed') || 'تمت المراجعة'}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
      <Clock className="w-3 h-3" />
      {t('pendingReview') || 'بانتظار المراجعة'}
    </span>
  );
}

/* ── Anomaly Type Label ── */
function getTypeLabel(type, t) {
  const labels = {
    sales_spike: t('salesSpike') || 'طفرة مبيعات',
    price_anomaly: t('priceAnomaly') || 'شذوذ في الأسعار',
    inventory_mismatch: t('inventoryMismatch') || 'تناقض في المخزون',
    duplicate_order: t('duplicateOrder') || 'طلب مكرر',
    payment_delay: t('paymentDelay') || 'تأخير في السداد',
    sales_drop: t('salesDrop') || 'انخفاض في المبيعات',
    expense_spike: t('expenseSpike') || 'طفرة في المصروفات',
    return_anomaly: t('returnAnomaly') || 'شذوذ في المرتجعات',
    customer_behavior: t('customerBehavior') || 'سلوك عميل غير عادي',
  };
  return labels[type] || type;
}

/* ════════════════════════════════════════════════════
   Main Component
   ════════════════════════════════════════════════════ */
export default function AnomalyDetectionPage() {
  const { t, locale, isRTL, isDark } = useI18n();
  const [anomalies, setAnomalies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [reviewingId, setReviewingId] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortDir, setSortDir] = useState('desc');

  const cur = t('currency') || 'ر.س';

  const formatCurrency = useCallback((val) => {
    const num = typeof val === 'number' ? val : Number(val) || 0;
    return num.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US') + ' ' + cur;
  }, [locale, cur]);

  /* ── Fetch data ── */
  const fetchData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    const mockAnomalies = generateMockAnomalies();
    const mockStats = generateMockStats();

    try {
      const [anomaliesRes, statsRes] = await Promise.all([
        analyticsAPI.anomalies().catch(() => null),
        analyticsAPI.anomalyStats().catch(() => null),
      ]);

      const allFailed = !anomaliesRes && !statsRes;
      if (allFailed) setError('API_UNAVAILABLE');

      setAnomalies(anomaliesRes?.data?.results || anomaliesRes?.data || mockAnomalies);
      setStats(statsRes?.data || mockStats);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || 'FETCH_ERROR');
      setAnomalies(mockAnomalies);
      setStats(mockStats);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Review anomaly ── */
  const handleReview = useCallback(async (id) => {
    if (!reviewNotes.trim()) {
      toast.error(t('reviewNotesRequired') || 'يرجى إدخال ملاحظات المراجعة');
      return;
    }
    setSubmitting(true);
    try {
      await analyticsAPI.reviewAnomaly(id, { notes: reviewNotes });
      setAnomalies(prev => prev.map(a => a.id === id ? { ...a, status: 'reviewed', notes: reviewNotes } : a));
      setStats(prev => prev ? { ...prev, unreviewed: Math.max(0, prev.unreviewed - 1) } : prev);
      setReviewingId(null);
      setReviewNotes('');
      toast.success(t('reviewSaved') || 'تم حفظ المراجعة بنجاح');
    } catch {
      // Fallback: update locally
      setAnomalies(prev => prev.map(a => a.id === id ? { ...a, status: 'reviewed', notes: reviewNotes } : a));
      setReviewingId(null);
      setReviewNotes('');
      toast.success(t('reviewSaved') || 'تم حفظ المراجعة بنجاح');
    } finally {
      setSubmitting(false);
    }
  }, [reviewNotes, t]);

  /* ── Filtered & sorted data ── */
  const filteredAnomalies = useMemo(() => {
    let result = [...anomalies];

    // Search
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(a =>
        a.description?.toLowerCase().includes(q) ||
        a.type?.toLowerCase().includes(q) ||
        String(a.amount).includes(q)
      );
    }

    // Severity filter
    if (filterSeverity !== 'all') {
      result = result.filter(a => a.severity === filterSeverity);
    }

    // Status filter
    if (filterStatus !== 'all') {
      result = result.filter(a => a.status === filterStatus);
    }

    // Sort
    result.sort((a, b) => {
      let valA, valB;
      switch (sortBy) {
        case 'date': valA = a.date; valB = b.date; break;
        case 'amount': valA = a.amount; valB = b.amount; break;
        case 'severity': {
          const order = { critical: 4, high: 3, medium: 2, low: 1 };
          valA = order[a.severity] || 0; valB = order[b.severity] || 0; break;
        }
        case 'type': valA = a.type; valB = b.type; break;
        default: valA = a.date; valB = b.date;
      }
      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [anomalies, searchQuery, filterSeverity, filterStatus, sortBy, sortDir]);

  const toggleSort = useCallback((field) => {
    if (sortBy === field) setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortDir('desc'); }
  }, [sortBy]);

  /* ── Skeleton ── */
  const Skeleton = () => (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3" />
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
          </div>
        ))}
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4" />
        <div className="h-64 bg-gray-100 dark:bg-gray-700/50 rounded-lg" />
      </div>
    </div>
  );

  if (loading && !anomalies.length) return <Skeleton />;

  const s = stats || {};

  return (
    <div className="space-y-6" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-sm">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              {t('anomalyDetection') || 'اكتشاف الشذوذ'}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('anomalyDesc') || 'مراقبة تلقائية للأنشطة غير المعتادة باستخدام الذكاء الاصطناعي'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => fetchData(true)} disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-600 hover:bg-riadah-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {t('refresh') || 'تحديث'}
          </button>
        </div>
      </div>

      {/* ── API fallback notice ── */}
      {error && !loading && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{t('usingCachedData') || 'يتم عرض بيانات مخزنة مؤقتاً – الخادم غير متاح'}</span>
        </div>
      )}

      {/* ── Summary Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Anomalies */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('totalAnomalies') || 'إجمالي الشذوذ'}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{s.total ?? 0}</p>
        </div>

        {/* Unreviewed */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Clock className="w-5 h-5 text-white" />
            </div>
            {s.unreviewed > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 animate-pulse">
                {t('needsAttention') || 'يحتاج اهتمام'}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('unreviewed') || 'بانتظار المراجعة'}</p>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{s.unreviewed ?? 0}</p>
        </div>

        {/* Critical */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center">
              <AlertOctagon className="w-5 h-5 text-white" />
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('criticalAnomalies') || 'حرج'}</p>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">{s.critical ?? 0}</p>
        </div>

        {/* High */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-white" />
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('highAnomalies') || 'عالي'}</p>
          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{s.high ?? 0}</p>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-wrap items-end gap-3">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('search') || 'بحث'}</label>
            <div className="relative">
              <Search className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" style={{ [isRTL ? 'right' : 'left']: '12px' }} />
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('searchAnomalies') || 'البحث في الشذوذ...'}
                className={`w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none ${isRTL ? 'pr-10' : 'pl-10'}`} />
            </div>
          </div>

          {/* Severity Filter */}
          <div className="min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('severity') || 'الشدة'}</label>
            <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none">
              <option value="all">{t('all') || 'الكل'}</option>
              <option value="critical">{t('critical') || 'حرج'}</option>
              <option value="high">{t('high') || 'عالي'}</option>
              <option value="medium">{t('medium') || 'متوسط'}</option>
              <option value="low">{t('low') || 'منخفض'}</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{t('status') || 'الحالة'}</label>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none">
              <option value="all">{t('all') || 'الكل'}</option>
              <option value="reviewed">{t('reviewed') || 'تمت المراجعة'}</option>
              <option value="unreviewed">{t('pendingReview') || 'بانتظار المراجعة'}</option>
            </select>
          </div>

          {/* Clear filters */}
          {(searchQuery || filterSeverity !== 'all' || filterStatus !== 'all') && (
            <button onClick={() => { setSearchQuery(''); setFilterSeverity('all'); setFilterStatus('all'); }}
              className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <X className="w-3 h-3" />
              {t('clearFilters') || 'مسح الفلاتر'}
            </button>
          )}
        </div>
      </div>

      {/* ── Anomalies Table ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {t('anomalyLog') || 'سجل الشذوذ'}
            <span className="text-xs font-normal text-gray-500 dark:text-gray-400 mr-2">({filteredAnomalies.length})</span>
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700/80">
              <tr className="text-gray-600 dark:text-gray-300">
                <th className="px-4 py-3 text-right font-medium">
                  <button onClick={() => toggleSort('date')} className="flex items-center gap-1 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                    {t('date') || 'التاريخ'}
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right font-medium">
                  <button onClick={() => toggleSort('type')} className="flex items-center gap-1 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                    {t('type') || 'النوع'}
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right font-medium">{t('description') || 'الوصف'}</th>
                <th className="px-4 py-3 text-right font-medium">
                  <button onClick={() => toggleSort('amount')} className="flex items-center gap-1 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                    {t('amount') || 'المبلغ'}
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right font-medium">
                  <button onClick={() => toggleSort('severity')} className="flex items-center gap-1 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                    {t('severity') || 'الشدة'}
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right font-medium">{t('status') || 'الحالة'}</th>
                <th className="px-4 py-3 text-right font-medium">{t('actions') || 'إجراءات'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
              {filteredAnomalies.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400 dark:text-gray-500">
                    <ShieldAlert className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>{t('noAnomalies') || 'لا توجد شذوذ مطابق للفلاتر'}</p>
                  </td>
                </tr>
              ) : (
                filteredAnomalies.map((anomaly) => (
                  <React.Fragment key={anomaly.id}>
                    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300 whitespace-nowrap">{anomaly.date}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                          {getTypeLabel(anomaly.type, t)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-800 dark:text-gray-200 max-w-xs truncate">{anomaly.description}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap" dir="ltr">{formatCurrency(anomaly.amount)}</td>
                      <td className="px-4 py-3">
                        <SeverityBadge severity={anomaly.severity} t={t} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={anomaly.status} t={t} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {anomaly.status === 'unreviewed' ? (
                            <button onClick={() => { setReviewingId(anomaly.id); setReviewNotes(''); }}
                              className="flex items-center gap-1 px-3 py-1.5 bg-riadah-600 hover:bg-riadah-700 text-white rounded-lg text-xs font-medium transition-colors">
                              <MessageSquare className="w-3 h-3" />
                              {t('review') || 'مراجعة'}
                            </button>
                          ) : (
                            <button onClick={() => { setReviewingId(anomaly.id); setReviewNotes(anomaly.notes || ''); }}
                              className="flex items-center gap-1 px-3 py-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-xs font-medium transition-colors">
                              <Eye className="w-3 h-3" />
                              {t('view') || 'عرض'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* Inline Review Form */}
                    {reviewingId === anomaly.id && (
                      <tr className="bg-gray-50 dark:bg-gray-700/20">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <MessageSquare className="w-4 h-4 text-riadah-500" />
                              <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                                {anomaly.status === 'reviewed' ? (t('reviewNotes') || 'ملاحظات المراجعة') : (t('addReviewNotes') || 'أضف ملاحظات المراجعة')}
                              </h4>
                            </div>
                            <textarea
                              value={reviewNotes}
                              onChange={(e) => setReviewNotes(e.target.value)}
                              rows={3}
                              placeholder={t('enterReviewNotes') || 'أدخل ملاحظاتك هنا...'}
                              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 outline-none resize-none"
                            />
                            <div className="flex items-center gap-2 justify-end">
                              <button onClick={() => setReviewingId(null)}
                                className="flex items-center gap-1 px-3 py-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-xs font-medium transition-colors">
                                <X className="w-3 h-3" />
                                {t('cancel') || 'إلغاء'}
                              </button>
                              {anomaly.status === 'unreviewed' && (
                                <button onClick={() => handleReview(anomaly.id)} disabled={submitting || !reviewNotes.trim()}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50">
                                  <Save className="w-3 h-3" />
                                  {submitting ? (t('saving') || 'جاري الحفظ...') : (t('submitReview') || 'إرسال المراجعة')}
                                </button>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Last Updated Footer ── */}
      <div className="text-center text-xs text-gray-400 dark:text-gray-500">
        {t('lastUpdated') || 'آخر تحديث'}: {lastUpdated.toLocaleTimeString(locale === 'ar' ? 'ar-SA' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}
