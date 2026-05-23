/**
 * Currencies page - multi-currency management with converter widget.
 * Allows viewing currencies, updating exchange rates, and viewing rate history.
 * Supports dark mode and i18n (RTL Arabic/English).
 */

import { useState, useEffect, useCallback } from 'react';
import { multiCurrencyAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Search, Edit2, X, DollarSign, ArrowRightLeft, History,
  ChevronDown, ChevronLeft, RefreshCw, Star,
} from 'lucide-react';

export default function CurrenciesPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isAccountant = user?.role === 'admin' || user?.role === 'accountant';

  /* ── state ── */
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedCurrencies, setExpandedCurrencies] = useState(new Set());
  const [rateHistories, setRateHistories] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(null);

  /* ── converter ── */
  const [convertAmount, setConvertAmount] = useState('');
  const [convertFrom, setConvertFrom] = useState('');
  const [convertTo, setConvertTo] = useState('');
  const [convertResult, setConvertResult] = useState(null);
  const [converting, setConverting] = useState(false);

  /* ── update rate modal ── */
  const [showRateModal, setShowRateModal] = useState(false);
  const [editingCurrency, setEditingCurrency] = useState(null);
  const [newRate, setNewRate] = useState('');
  const [saving, setSaving] = useState(false);

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchCurrencies = useCallback(async () => {
    setLoading(true);
    try {
      const res = await multiCurrencyAPI.getCurrencies({ search });
      const data = res.data.results || res.data;
      setCurrencies(data);
      // Set default converter currencies
      if (data.length > 0 && !convertFrom) {
        setConvertFrom(data.find((c) => c.is_default)?.code || data[0]?.code || '');
        setConvertTo(data.length > 1 ? data[1]?.code : data[0]?.code || '');
      }
    } catch {
      toast.error('خطأ في تحميل العملات');
    } finally {
      setLoading(false);
    }
  }, [search, convertFrom]);

  useEffect(() => {
    fetchCurrencies();
  }, [fetchCurrencies]);

  // ──────────────────────── Converter ────────────────────────

  const handleConvert = async () => {
    if (!convertAmount || !convertFrom || !convertTo) return;
    setConverting(true);
    setConvertResult(null);
    try {
      const res = await multiCurrencyAPI.convert({
        amount: parseFloat(convertAmount),
        from_currency: convertFrom,
        to_currency: convertTo,
      });
      setConvertResult(res.data);
    } catch {
      toast.error('خطأ في تحويل العملة');
    } finally {
      setConverting(false);
    }
  };

  // ──────────────────────── Rate History ────────────────────────

  const toggleExpand = async (currency) => {
    const id = currency.id;
    if (expandedCurrencies.has(id)) {
      setExpandedCurrencies((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      return;
    }

    setExpandedCurrencies((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });

    if (!rateHistories[id]) {
      setLoadingHistory(id);
      try {
        const res = await multiCurrencyAPI.getRateHistory(id);
        setRateHistories((prev) => ({ ...prev, [id]: res.data.results || res.data }));
      } catch {
        toast.error('خطأ في تحميل سعر الصرف');
      } finally {
        setLoadingHistory(null);
      }
    }
  };

  // ──────────────────────── Update Rate ────────────────────────

  const openRateModal = (currency) => {
    setEditingCurrency(currency);
    setNewRate(String(currency.exchange_rate || ''));
    setShowRateModal(true);
  };

  const handleUpdateRate = async (e) => {
    e.preventDefault();
    if (!editingCurrency) return;
    setSaving(true);
    try {
      await multiCurrencyAPI.updateRate(editingCurrency.id, {
        exchange_rate: parseFloat(newRate),
      });
      toast.success('تم تحديث سعر الصرف بنجاح');
      setShowRateModal(false);
      fetchCurrencies();
    } catch {
      toast.error('خطأ في تحديث سعر الصرف');
    } finally {
      setSaving(false);
    }
  };

  // ──────────────────────── Helpers ────────────────────────

  const formatAmount = (val) =>
    Number(val || 0).toLocaleString('ar-SA', { minimumFractionDigits: 2, maximumFractionDigits: 4 });

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            العملات
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            إدارة العملات وأسعار الصرف
          </p>
        </div>
      </div>

      {/* ── Currency Converter Widget ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-accent-500" />
          محول العملات
        </h3>
        <div className="flex flex-col sm:flex-row items-end gap-3">
          <div className="flex-1 w-full">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">المبلغ</label>
            <input
              type="number"
              value={convertAmount}
              onChange={(e) => setConvertAmount(e.target.value)}
              placeholder="أدخل المبلغ"
              className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
              dir="ltr"
            />
          </div>
          <div className="w-full sm:w-36">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">من</label>
            <select
              value={convertFrom}
              onChange={(e) => setConvertFrom(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
            >
              {currencies.map((c) => (
                <option key={c.id} value={c.code}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleConvert}
            disabled={converting || !convertAmount}
            className="w-full sm:w-auto px-5 py-2.5 bg-accent-500 hover:bg-accent-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium flex items-center justify-center gap-2"
          >
            {converting ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <ArrowRightLeft className="w-4 h-4" />
            )}
            تحويل
          </button>
          <div className="w-full sm:w-36">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">إلى</label>
            <select
              value={convertTo}
              onChange={(e) => setConvertTo(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
            >
              {currencies.map((c) => (
                <option key={c.id} value={c.code}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {convertResult && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
            <p className="text-sm text-green-600 dark:text-green-400 font-medium">
              {formatAmount(convertAmount)} {convertFrom} = {formatAmount(convertResult.converted_amount)} {convertTo}
            </p>
            <p className="text-xs text-green-500 dark:text-green-500 mt-1">
              سعر الصرف: {formatAmount(convertResult.rate)}
            </p>
          </div>
        )}
      </div>

      {/* ── Search ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="البحث في العملات..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
          />
        </div>
      </div>

      {/* ── Currencies Table ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 dark:text-gray-500">جاري التحميل...</div>
        ) : currencies.length === 0 ? (
          <div className="p-12 text-center">
            <DollarSign className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">لا توجد عملات</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">الرمز</th>
                  <th className="px-4 py-3 text-right font-medium">الاسم</th>
                  <th className="px-4 py-3 text-right font-medium">الرمز المختصر</th>
                  <th className="px-4 py-3 text-right font-medium">سعر الصرف</th>
                  <th className="px-4 py-3 text-right font-medium">الافتراضية</th>
                  {isAccountant && (
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  )}
                  <th className="px-4 py-3 text-right font-medium w-10"></th>
                </tr>
              </thead>
              <tbody>
                {currencies.map((currency) => {
                  const isExpanded = expandedCurrencies.has(currency.id);
                  return (
                    <>
                      <tr
                        key={currency.id}
                        className={`border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors`}
                      >
                        <td className="px-4 py-3 font-mono font-bold text-gray-900 dark:text-gray-100">
                          {currency.code}
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                          {currency.name}
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                          {currency.symbol || '—'}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                          {formatAmount(currency.exchange_rate)}
                        </td>
                        <td className="px-4 py-3">
                          {currency.is_default && (
                            <span className="flex items-center gap-1 px-2.5 py-1 bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400 rounded-full text-xs font-medium">
                              <Star className="w-3 h-3" />
                              افتراضية
                            </span>
                          )}
                        </td>
                        {isAccountant && (
                          <td className="px-4 py-3">
                            <button
                              onClick={() => openRateModal(currency)}
                              className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors"
                              title="تحديث سعر الصرف"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          </td>
                        )}
                        <td className="px-4 py-3">
                          <button
                            onClick={() => toggleExpand(currency)}
                            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
                          >
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronLeft className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                      {/* Rate History Row */}
                      {isExpanded && (
                        <tr key={`${currency.id}-history`}>
                          <td colSpan={isAccountant ? 7 : 6} className="px-4 py-0">
                            <div className="bg-gray-50 dark:bg-gray-700/20 p-4">
                              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                <History className="w-4 h-4" />
                                سجل أسعار الصرف - {currency.code}
                              </h4>
                              {loadingHistory === currency.id ? (
                                <div className="text-center text-gray-400 dark:text-gray-500 py-4 text-sm">
                                  جاري التحميل...
                                </div>
                              ) : rateHistories[currency.id]?.length > 0 ? (
                                <div className="overflow-x-auto">
                                  <table className="w-full text-xs">
                                    <thead>
                                      <tr className="text-gray-500 dark:text-gray-400 border-b dark:border-gray-600">
                                        <th className="px-3 py-2 text-right">التاريخ</th>
                                        <th className="px-3 py-2 text-right">سعر الصرف</th>
                                        <th className="px-3 py-2 text-right">ملاحظات</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {rateHistories[currency.id].map((h, idx) => (
                                        <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
                                          <td className="px-3 py-2 text-gray-600 dark:text-gray-400">
                                            {h.date || h.created_at}
                                          </td>
                                          <td className="px-3 py-2 font-mono font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                                            {formatAmount(h.rate || h.exchange_rate)}
                                          </td>
                                          <td className="px-3 py-2 text-gray-500 dark:text-gray-400">
                                            {h.note || '—'}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <p className="text-sm text-gray-400 dark:text-gray-500 py-2">
                                  لا يوجد سجل لأسعار الصرف
                                </p>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Update Exchange Rate Modal
         ═══════════════════════════════════════════════════════════ */}
      {showRateModal && editingCurrency && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowRateModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                تحديث سعر الصرف
              </h3>
              <button
                onClick={() => setShowRateModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleUpdateRate} className="p-5 space-y-4">
              <div className="text-center mb-2">
                <span className="inline-block px-4 py-2 bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-riadah-400 rounded-xl font-bold text-lg" dir="ltr">
                  {editingCurrency.code}
                </span>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  {editingCurrency.name}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  سعر الصرف الجديد *
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={newRate}
                  onChange={(e) => setNewRate(e.target.value)}
                  placeholder="أدخل سعر الصرف"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  dir="ltr"
                  autoFocus
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? 'جاري الحفظ...' : 'تحديث'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRateModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
