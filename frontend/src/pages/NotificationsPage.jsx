/**
 * NotificationsPage - مركز الإشعارات
 * Full-featured notifications management page with filtering, bulk actions,
 * stats, admin tools, and expand/collapse details.
 */

import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { notificationsAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Bell, BellOff, Check, CheckCircle, AlertTriangle, XCircle,
  Info, ShoppingCart, ClipboardList, Calendar, Settings,
  DollarSign, Receipt, FileText, Package, TrendingDown, Wallet,
  Trash2, Filter, X, Send, BarChart3, Mail, RefreshCw,
  ChevronDown, ChevronUp, Clock, AlertCircle, Loader2,
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ConfirmDialog';
import Modal from '../components/Modal';
import StatCard from '../components/StatCard';

// ── Icon & color maps for notification types ──────────────────────────
const typeIcons = {
  info: Info, success: CheckCircle, warning: AlertTriangle, error: XCircle,
  order: ShoppingCart, task: ClipboardList, leave: Calendar,
  system: Settings, payment: DollarSign, invoice: Receipt,
  contract: FileText, inventory: Package, expense: TrendingDown, payroll: Wallet,
};

const typeColors = {
  info: { bg: 'bg-riadah-100 dark:bg-riadah-900/30', icon: 'text-accent-500 dark:text-accent-400', dot: 'bg-riadah-500' },
  success: { bg: 'bg-green-100 dark:bg-green-900/30', icon: 'text-green-600 dark:text-green-400', dot: 'bg-green-500' },
  warning: { bg: 'bg-amber-100 dark:bg-amber-900/30', icon: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-500' },
  error: { bg: 'bg-red-100 dark:bg-red-900/30', icon: 'text-red-600 dark:text-red-400', dot: 'bg-red-500' },
  order: { bg: 'bg-indigo-100 dark:bg-indigo-900/30', icon: 'text-indigo-600 dark:text-indigo-400', dot: 'bg-indigo-500' },
  task: { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: 'text-purple-600 dark:text-purple-400', dot: 'bg-purple-500' },
  leave: { bg: 'bg-teal-100 dark:bg-teal-900/30', icon: 'text-teal-600 dark:text-teal-400', dot: 'bg-teal-500' },
  system: { bg: 'bg-gray-100 dark:bg-gray-700/30', icon: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-500' },
  payment: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', icon: 'text-emerald-600 dark:text-emerald-400', dot: 'bg-emerald-500' },
  invoice: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', icon: 'text-cyan-600 dark:text-cyan-400', dot: 'bg-cyan-500' },
  contract: { bg: 'bg-violet-100 dark:bg-violet-900/30', icon: 'text-violet-600 dark:text-violet-400', dot: 'bg-violet-500' },
  inventory: { bg: 'bg-orange-100 dark:bg-orange-900/30', icon: 'text-orange-600 dark:text-orange-400', dot: 'bg-orange-500' },
  expense: { bg: 'bg-rose-100 dark:bg-rose-900/30', icon: 'text-rose-600 dark:text-rose-400', dot: 'bg-rose-500' },
  payroll: { bg: 'bg-sky-100 dark:bg-sky-900/30', icon: 'text-sky-600 dark:text-sky-400', dot: 'bg-sky-500' },
};

const priorityBadge = {
  low: { cls: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300', label: 'priorityLow' },
  normal: { cls: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400', label: 'priorityNormal' },
  high: { cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400', label: 'priorityHigh' },
  urgent: { cls: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', label: 'priorityUrgent' },
};

const typeOptions = [
  'all', 'info', 'success', 'warning', 'error', 'order', 'task', 'leave',
  'system', 'payment', 'invoice', 'contract', 'inventory', 'expense', 'payroll',
];

const sortOptions = [
  { value: 'newest', label: 'newestFirst' },
  { value: 'oldest', label: 'oldestFirst' },
  { value: 'priority_high', label: 'priorityHighFirst' },
  { value: 'priority_low', label: 'priorityLowFirst' },
];

// ── Helper: time ago ──────────────────────────────────────────────────
function timeAgo(dateStr, locale) {
  try {
    const now = new Date();
    const date = new Date(dateStr);
    const seconds = Math.floor((now - date) / 1000);
    if (seconds < 60) return locale === 'ar' ? 'الآن' : 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} ${locale === 'ar' ? 'دقيقة' : 'min'}`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} ${locale === 'ar' ? 'ساعة' : 'hr'}`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} ${locale === 'ar' ? 'يوم' : 'days'}`;
    return date.toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US');
  } catch {
    return dateStr || '';
  }
}

// ── Select component ──────────────────────────────────────────────────
function SelectInput({ value, onChange, options, label }) {
  const { t, locale } = useI18n();
  return (
    <div className="flex flex-col gap-1 min-w-0">
      {label && <label className="text-xs text-gray-500 dark:text-gray-400 font-medium">{label}</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
      >
        {options.map((opt) => (
          <option key={typeof opt === 'string' ? opt : opt.value} value={typeof opt === 'string' ? opt : opt.value}>
            {typeof opt === 'string' ? (opt === 'all' ? t('all') : opt) : t(opt.label)}
          </option>
        ))}
      </select>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────
export default function NotificationsPage() {
  const { t, locale, isRTL } = useI18n();
  const { isDark } = useTheme();
  const { isAdmin, hasPermission } = useAuth();

  // ── Data state ─────────────────────────────────────────────────────
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // ── Filter state ───────────────────────────────────────────────────
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortBy, setSortBy] = useState('newest');

  // ── UI state ───────────────────────────────────────────────────────
  const [expandedId, setExpandedId] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());

  // ── Modals ─────────────────────────────────────────────────────────
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(90);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // ── Admin form ─────────────────────────────────────────────────────
  const [adminForm, setAdminForm] = useState({
    recipient_type: 'all', // 'all' | 'user' | 'role'
    recipient_id: '',
    recipient_role: '',
    title: '',
    message: '',
    type: 'info',
    priority: 'normal',
    link: '',
  });

  // ── Fetch stats ────────────────────────────────────────────────────
  const fetchStats = useCallback(async () => {
    try {
      const res = await notificationsAPI.stats();
      setStats(res.data);
    } catch {
      setStats(null);
    }
  }, []);

  // ── Fetch notifications ────────────────────────────────────────────
  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (typeFilter && typeFilter !== 'all') params.type = typeFilter;
      if (statusFilter && statusFilter !== 'all') params.is_read = statusFilter === 'read';
      if (priorityFilter && priorityFilter !== 'all') params.priority = priorityFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (sortBy) params.sorting = sortBy;

      const res = await notificationsAPI.filtered(params);
      const data = res.data;
      const items = data.results || (Array.isArray(data) ? data : []);
      setNotifications(items);
      setTotalCount(data.count || items.length || 0);
    } catch {
      // Fallback to basic list
      try {
        const res = await notificationsAPI.list();
        const data = res.data;
        const items = data.results || (Array.isArray(data) ? data : []);
        let filtered = items;

        if (typeFilter !== 'all') filtered = filtered.filter((n) => n.notification_type === typeFilter);
        if (statusFilter === 'read') filtered = filtered.filter((n) => n.is_read);
        if (statusFilter === 'unread') filtered = filtered.filter((n) => !n.is_read);
        if (priorityFilter !== 'all') filtered = filtered.filter((n) => n.priority === priorityFilter);
        if (dateFrom) filtered = filtered.filter((n) => n.created_at >= dateFrom);
        if (dateTo) filtered = filtered.filter((n) => n.created_at <= dateTo + 'T23:59:59');

        if (sortBy === 'oldest') filtered.reverse();
        if (sortBy === 'priority_high') {
          const pOrder = { urgent: 0, high: 1, normal: 2, low: 3 };
          filtered.sort((a, b) => (pOrder[a.priority] ?? 4) - (pOrder[b.priority] ?? 4));
        }
        if (sortBy === 'priority_low') {
          const pOrder = { low: 0, normal: 1, high: 2, urgent: 3 };
          filtered.sort((a, b) => (pOrder[a.priority] ?? 4) - (pOrder[b.priority] ?? 4));
        }

        setNotifications(filtered);
        setTotalCount(filtered.length);
      } catch {
        setNotifications([]);
        setTotalCount(0);
      }
    }
    setLoading(false);
  }, [typeFilter, statusFilter, priorityFilter, dateFrom, dateTo, sortBy]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // ── Handlers ───────────────────────────────────────────────────────
  const clearFilters = () => {
    setTypeFilter('all');
    setStatusFilter('all');
    setPriorityFilter('all');
    setDateFrom('');
    setDateTo('');
    setSortBy('newest');
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      await fetchStats();
      toast.success(locale === 'ar' ? 'تم تحديد الكل كمقروء' : 'All marked as read');
    } catch {
      toast.error(locale === 'ar' ? 'فشل تحديث الإشعارات' : 'Failed to update notifications');
    }
  };

  const handleMarkRead = async (notif) => {
    if (notif.is_read) return;
    try {
      await notificationsAPI.markRead(notif.id);
      setNotifications((prev) => prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n)));
      await fetchStats();
    } catch { /* silent */ }
  };

  const handleDelete = async (id) => {
    setActionLoading(true);
    try {
      await notificationsAPI.delete(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setSelectedIds((prev) => { const s = new Set(prev); s.delete(id); return s; });
      await fetchStats();
      toast.success(t('notificationDeleted'));
    } catch {
      toast.error(locale === 'ar' ? 'فشل حذف الإشعار' : 'Failed to delete notification');
    }
    setActionLoading(false);
    setShowDeleteConfirm(false);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    setActionLoading(true);
    try {
      await notificationsAPI.bulkDelete(Array.from(selectedIds));
      setNotifications((prev) => prev.filter((n) => !selectedIds.has(n.id)));
      setSelectedIds(new Set());
      await fetchStats();
      toast.success(t('notificationsDeleted'));
    } catch {
      toast.error(locale === 'ar' ? 'فشل حذف الإشعارات' : 'Failed to delete notifications');
    }
    setActionLoading(false);
    setShowBulkDeleteConfirm(false);
  };

  const handleBulkMarkRead = async () => {
    if (selectedIds.size === 0) return;
    const unread = Array.from(selectedIds).filter(
      (id) => !notifications.find((n) => n.id === id)?.is_read
    );
    for (const id of unread) {
      try { await notificationsAPI.markRead(id); } catch { /* skip */ }
    }
    setNotifications((prev) => prev.map((n) => (selectedIds.has(n.id) ? { ...n, is_read: true } : n)));
    setSelectedIds(new Set());
    await fetchStats();
    toast.success(locale === 'ar' ? 'تم تحديد المحدد كمقروء' : 'Selected marked as read');
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return s;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === notifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(notifications.map((n) => n.id)));
    }
  };

  // ── Admin: Send notification ───────────────────────────────────────
  const handleAdminSend = async () => {
    if (!adminForm.title.trim() || !adminForm.message.trim()) {
      toast.error(locale === 'ar' ? 'العنوان والرسالة مطلوبان' : 'Title and message are required');
      return;
    }
    setActionLoading(true);
    try {
      const payload = {
        title: adminForm.title,
        message: adminForm.message,
        notification_type: adminForm.type,
        priority: adminForm.priority,
        link: adminForm.link || undefined,
      };
      if (adminForm.recipient_type === 'all') {
        payload.broadcast = true;
      } else if (adminForm.recipient_type === 'user' && adminForm.recipient_id) {
        payload.recipient_id = adminForm.recipient_id;
      } else if (adminForm.recipient_type === 'role' && adminForm.recipient_role) {
        payload.role = adminForm.recipient_role;
      }
      await notificationsAPI.adminCreate(payload);
      toast.success(t('notificationSent'));
      setShowSendModal(false);
      setAdminForm({
        recipient_type: 'all', recipient_id: '', recipient_role: '',
        title: '', message: '', type: 'info', priority: 'normal', link: '',
      });
      await fetchNotifications();
      await fetchStats();
    } catch {
      toast.error(locale === 'ar' ? 'فشل إرسال الإشعار' : 'Failed to send notification');
    }
    setActionLoading(false);
  };

  // ── Admin: Cleanup ─────────────────────────────────────────────────
  const handleCleanup = async () => {
    setActionLoading(true);
    try {
      await notificationsAPI.cleanup(cleanupDays);
      toast.success(locale === 'ar' ? 'تم تنظيف الإشعارات القديمة' : 'Old notifications cleaned up');
      setShowCleanupModal(false);
      await fetchNotifications();
      await fetchStats();
    } catch {
      toast.error(locale === 'ar' ? 'فشل تنظيف الإشعارات' : 'Failed to clean up notifications');
    }
    setActionLoading(false);
  };

  const hasFilters = typeFilter !== 'all' || statusFilter !== 'all' || priorityFilter !== 'all' || dateFrom || dateTo || sortBy !== 'newest';

  // ── Render ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Page Header ──────────────────────────────────────────── */}
      <PageHeader
        title={t('notificationsPage')}
        description={t('notificationsDesc')}
        icon={Bell}
        breadcrumbs={[{ label: t('notificationsPage') }]}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => { fetchNotifications(); fetchStats(); }}
              className="p-2.5 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={t('refresh')}
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            {isAdmin && (
              <>
                <button
                  onClick={() => setShowSendModal(true)}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-riadah-500 hover:bg-riadah-600 transition-colors shadow-sm"
                >
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">{t('sendNotification')}</span>
                </button>
                <button
                  onClick={() => setShowCleanupModal(true)}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span className="hidden sm:inline">{t('cleanupOld')}</span>
                </button>
              </>
            )}
          </div>
        }
      />

      {/* ── Stats Row ────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('totalNotifications')}
          value={stats?.total ?? notifications.length ?? 0}
          icon={Bell}
          color="blue"
        />
        <StatCard
          title={t('unread')}
          value={stats?.unread ?? notifications.filter((n) => !n.is_read).length ?? 0}
          icon={Mail}
          color="red"
        />
        <StatCard
          title={t('urgentNotifications')}
          value={stats?.urgent ?? notifications.filter((n) => n.priority === 'urgent').length ?? 0}
          icon={AlertTriangle}
          color="orange"
        />
        <StatCard
          title={t('notificationStats')}
          value={stats?.by_type ? Object.keys(stats.by_type).length : 0}
          icon={BarChart3}
          color="purple"
        />
      </div>

      {/* ── Filter Bar ───────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('filter')}</span>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-xs text-red-500 hover:text-red-600 transition-colors mr-auto"
            >
              <X className="w-3 h-3" />
              {locale === 'ar' ? 'مسح الفلاتر' : 'Clear filters'}
            </button>
          )}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <SelectInput
            value={typeFilter}
            onChange={setTypeFilter}
            options={typeOptions}
            label={t('filterByType')}
          />
          <SelectInput
            value={statusFilter}
            onChange={setStatusFilter}
            options={['all', 'unread', 'read']}
            label={t('filterByStatus')}
          />
          <SelectInput
            value={priorityFilter}
            onChange={setPriorityFilter}
            options={['all', 'low', 'normal', 'high', 'urgent']}
            label={t('filterByPriority')}
          />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400 font-medium">{t('from')}</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400 font-medium">{t('to')}</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
            />
          </div>
          <SelectInput
            value={sortBy}
            onChange={setSortBy}
            options={sortOptions}
            label={t('sort')}
          />
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-400">
            {totalCount} {t('results')}
          </span>
          <button
            onClick={handleMarkAllRead}
            className="flex items-center gap-1.5 text-xs text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 font-medium transition-colors"
          >
            <Check className="w-3.5 h-3.5" />
            {t('markAllRead')}
          </button>
        </div>
      </div>

      {/* ── Bulk Actions Bar ─────────────────────────────────────── */}
      {selectedIds.size > 0 && (
        <div className="bg-riadah-50 dark:bg-riadah-900/20 rounded-xl border border-riadah-200 dark:border-riadah-800 p-3 flex flex-wrap items-center gap-3 animate-fade-in">
          <span className="text-sm font-medium text-riadah-700 dark:text-accent-300">
            {selectedIds.size} {locale === 'ar' ? 'إشعار محدد' : 'selected'}
          </span>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowBulkDeleteConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              {t('deleteNotifications')}
            </button>
            <button
              onClick={handleBulkMarkRead}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-accent-500 dark:text-accent-400 bg-riadah-100 dark:bg-riadah-900/30 hover:bg-riadah-200 dark:hover:bg-riadah-900/50 transition-colors"
            >
              <Check className="w-3.5 h-3.5" />
              {t('markAsRead')}
            </button>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              {t('deselectAll')}
            </button>
          </div>
        </div>
      )}

      {/* ── Notifications List ───────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
        </div>
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={BellOff}
          title={t('noNotifications')}
          description={locale === 'ar' ? 'لا توجد إشعارات لعرضها' : 'No notifications to display'}
          action={
            hasFilters ? (
              <button
                onClick={clearFilters}
                className="px-4 py-2 rounded-xl text-sm font-medium text-white bg-riadah-500 hover:bg-riadah-600 transition-colors"
              >
                {locale === 'ar' ? 'مسح الفلاتر' : 'Clear Filters'}
              </button>
            ) : null
          }
        />
      ) : (
        <div className="space-y-2">
          {/* Select all header */}
          <div className="flex items-center gap-3 px-4 py-2 text-xs text-gray-400 dark:text-gray-500">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedIds.size === notifications.length && notifications.length > 0}
                onChange={toggleSelectAll}
                className="rounded border-gray-300 dark:border-gray-600 text-accent-500 focus:ring-accent-500"
              />
              <span>{t('selectNotifications')}</span>
            </label>
          </div>

          {notifications.map((notif) => {
            const TypeIcon = typeIcons[notif.notification_type] || typeIcons.info;
            const colors = typeColors[notif.notification_type] || typeColors.info;
            const pBadge = priorityBadge[notif.priority];
            const isExpanded = expandedId === notif.id;
            const isSelected = selectedIds.has(notif.id);

            return (
              <div
                key={notif.id}
                className={`
                  bg-white dark:bg-gray-800 rounded-xl border transition-all duration-200
                  ${isExpanded ? 'border-riadah-300 dark:border-riadah-700 shadow-md' : 'border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md'}
                  ${!notif.is_read ? 'border-r-4 border-r-blue-500 dark:border-r-blue-400' : ''}
                  ${isSelected ? 'ring-2 ring-accent-500/30' : ''}
                `}
              >
                {/* Card content */}
                <div
                  className="flex items-start gap-3 p-4 cursor-pointer"
                  onClick={() => {
                    setExpandedId(isExpanded ? null : notif.id);
                    handleMarkRead(notif);
                  }}
                >
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => { e.stopPropagation(); toggleSelect(notif.id); }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1 rounded border-gray-300 dark:border-gray-600 text-accent-500 focus:ring-accent-500 flex-shrink-0"
                  />

                  {/* Type icon */}
                  <div className={`w-10 h-10 rounded-xl ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                    <TypeIcon className={`w-5 h-5 ${colors.icon}`} />
                  </div>

                  {/* Message content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className={`text-sm font-semibold truncate ${!notif.is_read ? 'text-gray-900 dark:text-gray-100' : 'text-gray-600 dark:text-gray-400'}`}>
                        {notif.title || (locale === 'ar' ? 'إشعار' : 'Notification')}
                      </h3>
                      {!notif.is_read && (
                        <span className={`w-2 h-2 rounded-full ${colors.dot} flex-shrink-0`} />
                      )}
                      {pBadge && (
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${pBadge.cls}`}>
                          {t(pBadge.label)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {notif.message || ''}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Clock className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-400">
                        {timeAgo(notif.created_at, locale)}
                      </span>
                      {notif.sender_name && (
                        <span className="text-xs text-gray-400">
                          {isRTL ? '•' : '•'} {notif.sender_name}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(true); setDeleteTarget(notif); }}
                      className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      title={t('deleteNotification')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setExpandedId(isExpanded ? null : notif.id); }}
                      className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      {isExpanded
                        ? <ChevronUp className="w-4 h-4" />
                        : <ChevronDown className="w-4 h-4" />
                      }
                    </button>
                  </div>
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 animate-fade-in">
                    <div className="pt-3">
                      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                        {notif.message || ''}
                      </p>
                      {notif.link && (
                        <a
                          href={notif.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 mt-2 text-xs text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 transition-colors"
                        >
                          {locale === 'ar' ? 'فتح الرابط' : 'Open link'}
                          <span className="text-xs">↗</span>
                        </a>
                      )}
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {notif.created_at}
                        </span>
                        {notif.notification_type && (
                          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                            {notif.notification_type}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Confirm: Delete single ───────────────────────────────── */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={() => deleteTarget && handleDelete(deleteTarget.id)}
        title={t('deleteNotification')}
        message={locale === 'ar' ? 'هل أنت متأكد من حذف هذا الإشعار؟' : 'Are you sure you want to delete this notification?'}
        type="danger"
        loading={actionLoading}
      />

      {/* ── Confirm: Bulk delete ─────────────────────────────────── */}
      <ConfirmDialog
        isOpen={showBulkDeleteConfirm}
        onClose={() => setShowBulkDeleteConfirm(false)}
        onConfirm={handleBulkDelete}
        title={t('deleteNotifications')}
        message={t('confirmDeleteNotifications')}
        type="danger"
        loading={actionLoading}
      />

      {/* ── Modal: Send notification (Admin) ─────────────────────── */}
      <Modal
        isOpen={showSendModal}
        onClose={() => { if (!actionLoading) setShowSendModal(false); }}
        title={t('sendNotification')}
        size="lg"
        footer={
          <>
            <button
              onClick={() => setShowSendModal(false)}
              disabled={actionLoading}
              className="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
            >
              {t('cancelBtn')}
            </button>
            <button
              onClick={handleAdminSend}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white bg-riadah-500 hover:bg-riadah-600 transition-colors disabled:opacity-50"
            >
              {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {t('send')}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          {/* Recipient type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {locale === 'ar' ? 'المستلم' : 'Recipient'}
            </label>
            <div className="flex items-center gap-4">
              {[
                { val: 'all', lbl: t('sendToAll') },
                { val: 'user', lbl: t('sendToUser') },
                { val: 'role', lbl: t('sendToRole') },
              ].map((opt) => (
                <label key={opt.val} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="recipient_type"
                    value={opt.val}
                    checked={adminForm.recipient_type === opt.val}
                    onChange={(e) => setAdminForm({ ...adminForm, recipient_type: e.target.value })}
                    className="text-accent-500 focus:ring-accent-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{opt.lbl}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Recipient ID / Role */}
          {adminForm.recipient_type === 'user' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {locale === 'ar' ? 'معرف المستخدم' : 'User ID'}
              </label>
              <input
                type="number"
                value={adminForm.recipient_id}
                onChange={(e) => setAdminForm({ ...adminForm, recipient_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
                placeholder={locale === 'ar' ? 'أدخل معرف المستخدم' : 'Enter user ID'}
              />
            </div>
          )}
          {adminForm.recipient_type === 'role' && (
            <SelectInput
              value={adminForm.recipient_role}
              onChange={(v) => setAdminForm({ ...adminForm, recipient_role: v })}
              options={['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}
              label={locale === 'ar' ? 'الدور' : 'Role'}
            />
          )}

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('name')}
            </label>
            <input
              type="text"
              value={adminForm.title}
              onChange={(e) => setAdminForm({ ...adminForm, title: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
              placeholder={locale === 'ar' ? 'عنوان الإشعار' : 'Notification title'}
            />
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('description')}
            </label>
            <textarea
              value={adminForm.message}
              onChange={(e) => setAdminForm({ ...adminForm, message: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors resize-none"
              placeholder={locale === 'ar' ? 'نص الإشعار...' : 'Notification message...'}
            />
          </div>

          {/* Type & Priority row */}
          <div className="grid grid-cols-2 gap-4">
            <SelectInput
              value={adminForm.type}
              onChange={(v) => setAdminForm({ ...adminForm, type: v })}
              options={typeOptions.filter((o) => o !== 'all')}
              label={t('type')}
            />
            <SelectInput
              value={adminForm.priority}
              onChange={(v) => setAdminForm({ ...adminForm, priority: v })}
              options={['low', 'normal', 'high', 'urgent']}
              label={t('priority')}
            />
          </div>

          {/* Link (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {locale === 'ar' ? 'رابط (اختياري)' : 'Link (optional)'}
            </label>
            <input
              type="url"
              value={adminForm.link}
              onChange={(e) => setAdminForm({ ...adminForm, link: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-colors"
              placeholder={locale === 'ar' ? 'https://...' : 'https://...'}
              dir="ltr"
            />
          </div>
        </div>
      </Modal>

      {/* ── Confirm: Cleanup old ─────────────────────────────────── */}
      <ConfirmDialog
        isOpen={showCleanupModal}
        onClose={() => setShowCleanupModal(false)}
        onConfirm={handleCleanup}
        title={t('cleanupOld')}
        message={`${t('cleanupConfirm')} ${cleanupDays} ${t('days')}?`}
        type="warning"
        loading={actionLoading}
      />
    </div>
  );
}
