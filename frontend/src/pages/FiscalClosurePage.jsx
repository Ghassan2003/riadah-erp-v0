/**
 * Fiscal Closure page - manages fiscal years and monthly periods.
 * Allows creating fiscal years, closing/reopening periods.
 * Supports dark mode and i18n (RTL Arabic/English).
 */

import { useState, useEffect, useCallback } from 'react';
import { fiscalClosureAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Plus, X, Calendar, ChevronDown, ChevronLeft, Lock, Unlock,
  AlertTriangle,
} from 'lucide-react';

export default function FiscalClosurePage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isAccountant = user?.role === 'admin' || user?.role === 'accountant';

  const PERIOD_STATUS_COLORS = {
    open: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    closing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    closed: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
  };

  const PERIOD_STATUS_LABELS = {
    open: 'مفتوح',
    closing: 'قيد الإقفال',
    closed: 'مقفل',
  };

  const FY_STATUS_COLORS = {
    open: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    closed: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
    partially_closed: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  };

  const FY_STATUS_LABELS = {
    open: 'مفتوح',
    closed: 'مقفل',
    partially_closed: 'مقفل جزئياً',
  };

  const MONTH_NAMES = [
    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
  ];

  /* ── state ── */
  const [fiscalYears, setFiscalYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedYears, setExpandedYears] = useState(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const [form, setForm] = useState({
    year: new Date().getFullYear(),
    start_date: '',
    end_date: '',
  });

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchFiscalYears = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fiscalClosureAPI.list();
      setFiscalYears(res.data.results || res.data);
    } catch {
      toast.error('خطأ في تحميل السنوات المالية');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiscalYears();
  }, [fetchFiscalYears]);

  // ──────────────────────── Helpers ────────────────────────

  const toggleExpand = (id) => {
    setExpandedYears((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ──────────────────────── Create Fiscal Year ────────────────────────

  const openCreate = () => {
    const year = new Date().getFullYear();
    setForm({
      year,
      start_date: `${year}-01-01`,
      end_date: `${year}-12-31`,
    });
    setShowCreateModal(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await fiscalClosureAPI.create(form);
      toast.success('تم إنشاء السنة المالية بنجاح');
      setShowCreateModal(false);
      fetchFiscalYears();
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.year?.[0] || 'خطأ في إنشاء السنة المالية';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // ──────────────────────── Close / Reopen Period ────────────────────────

  const handleClosePeriod = async () => {
    if (!confirmAction?.periodId) return;
    try {
      await fiscalClosureAPI.closePeriod(confirmAction.periodId);
      toast.success('تم إقفال الفترة بنجاح');
      fetchFiscalYears();
    } catch {
      toast.error('خطأ في إقفال الفترة');
    } finally {
      setConfirmAction(null);
    }
  };

  const handleReopenPeriod = async () => {
    if (!confirmAction?.periodId) return;
    try {
      await fiscalClosureAPI.reopenPeriod(confirmAction.periodId);
      toast.success('تم إعادة فتح الفترة بنجاح');
      fetchFiscalYears();
    } catch {
      toast.error('خطأ في إعادة فتح الفترة');
    } finally {
      setConfirmAction(null);
    }
  };

  const handleConfirm = () => {
    if (confirmAction?.type === 'close') {
      handleClosePeriod();
    } else if (confirmAction?.type === 'reopen') {
      handleReopenPeriod();
    }
  };

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            الإقفال المالي
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            إدارة السنوات المالية والفترات الشهرية
          </p>
        </div>
        {isAccountant && (
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5" />
            إنشاء سنة مالية
          </button>
        )}
      </div>

      {/* ── Fiscal Years ── */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-12 text-center text-gray-400 dark:text-gray-500 shadow-sm border border-gray-100 dark:border-gray-700">
            جاري التحميل...
          </div>
        ) : fiscalYears.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-12 text-center shadow-sm border border-gray-100 dark:border-gray-700">
            <Calendar className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">لا توجد سنوات مالية</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">أنشئ سنة مالية جديدة للبدء</p>
          </div>
        ) : (
          fiscalYears.map((fy) => {
            const periodCount = fy.periods?.length || 12;
            const closedCount = fy.periods?.filter((p) => p.status === 'closed').length || 0;
            const isExpanded = expandedYears.has(fy.id);

            return (
              <div
                key={fy.id}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden"
              >
                {/* Fiscal Year Header */}
                <button
                  onClick={() => toggleExpand(fy.id)}
                  className="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-riadah-50 dark:bg-riadah-900/30 rounded-xl flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-riadah-600 dark:text-riadah-400" />
                    </div>
                    <div className="text-right">
                      <h3 className="font-bold text-gray-900 dark:text-gray-100 text-lg">
                        السنة المالية {fy.year}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {fy.start_date} — {fy.end_date}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-left">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          FY_STATUS_COLORS[fy.status] || FY_STATUS_COLORS.open
                        }`}
                      >
                        {FY_STATUS_LABELS[fy.status] || fy.status}
                      </span>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {closedCount} من {periodCount} فترة مقفلة
                      </p>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronLeft className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </button>

                {/* Expanded Periods */}
                {isExpanded && (
                  <div className="border-t dark:border-gray-700">
                    {/* Progress Bar */}
                    <div className="px-5 py-3 bg-gray-50 dark:bg-gray-800/70">
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
                        <span>تقدم الإقفال</span>
                        <span>{periodCount > 0 ? Math.round((closedCount / periodCount) * 100) : 0}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${periodCount > 0 ? (closedCount / periodCount) * 100 : 0}%` }}
                        />
                      </div>
                    </div>

                    {/* Periods Grid */}
                    <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                      {(fy.periods || Array.from({ length: 12 }, (_, i) => ({
                        month_number: i + 1,
                        status: i < closedCount ? 'closed' : 'open',
                      }))).map((period, idx) => (
                        <div
                          key={period.id || idx}
                          className={`rounded-xl p-4 border transition-colors ${
                            period.status === 'closed'
                              ? 'bg-gray-50 dark:bg-gray-700/30 border-gray-200 dark:border-gray-600'
                              : period.status === 'closing'
                              ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800'
                              : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                              {MONTH_NAMES[period.month_number - 1] || `شهر ${period.month_number}`}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                PERIOD_STATUS_COLORS[period.status] || PERIOD_STATUS_COLORS.open
                              }`}
                            >
                              {PERIOD_STATUS_LABELS[period.status] || period.status}
                            </span>
                          </div>

                          {period.status === 'open' && isAccountant && (
                            <button
                              onClick={() =>
                                setConfirmAction({
                                  type: 'close',
                                  periodId: period.id,
                                  label: MONTH_NAMES[period.month_number - 1] || `شهر ${period.month_number}`,
                                })
                              }
                              className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors text-sm font-medium"
                            >
                              <Lock className="w-3.5 h-3.5" />
                              إقفال الفترة
                            </button>
                          )}

                          {period.status === 'closed' && isAccountant && (
                            <button
                              onClick={() =>
                                setConfirmAction({
                                  type: 'reopen',
                                  periodId: period.id,
                                  label: MONTH_NAMES[period.month_number - 1] || `شهر ${period.month_number}`,
                                })
                              }
                              className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors text-sm font-medium"
                            >
                              <Unlock className="w-3.5 h-3.5" />
                              إعادة فتح
                            </button>
                          )}

                          {period.status === 'closing' && (
                            <div className="text-xs text-yellow-600 dark:text-yellow-400 text-center">
                              جاري الإقفال...
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Create Fiscal Year Modal
         ═══════════════════════════════════════════════════════════ */}
      {showCreateModal && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                إنشاء سنة مالية جديدة
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  السنة المالية *
                </label>
                <input
                  type="number"
                  value={form.year}
                  onChange={(e) => setForm({ ...form, year: parseInt(e.target.value) || '' })}
                  placeholder="مثال: 2025"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    تاريخ البداية *
                  </label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    تاريخ النهاية *
                  </label>
                  <input
                    type="date"
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? 'جاري الحفظ...' : 'إنشاء'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Confirm Dialog (Close / Reopen Period)
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
              <div
                className={`mx-auto w-14 h-14 rounded-full flex items-center justify-center mb-4 ${
                  confirmAction.type === 'close'
                    ? 'bg-red-100 dark:bg-red-900/30'
                    : 'bg-green-100 dark:bg-green-900/30'
                }`}
              >
                <AlertTriangle
                  className={`w-7 h-7 ${
                    confirmAction.type === 'close'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-green-600 dark:text-green-400'
                  }`}
                />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {confirmAction.type === 'close' ? 'تأكيد إقفال الفترة' : 'تأكيد إعادة فتح الفترة'}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {confirmAction.type === 'close'
                    ? 'هل أنت متأكد من إقفال فترة'
                    : 'هل أنت متأكد من إعادة فتح فترة'}{' '}
                  <span className="font-medium text-gray-700 dark:text-gray-300">{confirmAction.label}</span>؟
                </p>
                {confirmAction.type === 'close' && (
                  <p className="text-xs text-red-500 dark:text-red-400 mt-2">
                    لن يمكن تسجيل قيود جديدة في هذه الفترة بعد الإقفال
                  </p>
                )}
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setConfirmAction(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
                <button
                  onClick={handleConfirm}
                  className={`flex-1 px-4 py-2.5 text-white rounded-lg transition-colors font-medium ${
                    confirmAction.type === 'close'
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {confirmAction.type === 'close' ? 'إقفال' : 'إعادة فتح'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
