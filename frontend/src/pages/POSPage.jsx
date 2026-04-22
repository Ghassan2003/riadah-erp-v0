/**
 * POS (Point of Sale) Page - نقطة البيع
 * Cashier interface with product grid, cart, payment, shift management, and reports.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { posAPI, productsAPI } from '../api';
import {
  ShoppingCart, Search, Plus, Minus, Trash2, CreditCard, Banknote,
  Clock, DollarSign, BarChart3, X, Loader2, Pause, CheckCircle,
  RotateCcw, Package, AlertTriangle, Receipt, CircleDot,
  Wifi, TrendingUp, Archive,
} from 'lucide-react';
import toast from 'react-hot-toast';

const VAT = 0.15;
const PAYMENTS = [
  { key: 'cash', label: 'نقدي', icon: Banknote },
  { key: 'card', label: 'بطاقة', icon: CreditCard },
  { key: 'online', label: 'إلكتروني', icon: Wifi },
  { key: 'mixed', label: 'مختلط', icon: CircleDot },
];
const getPayLabel = (k) => PAYMENTS.find((p) => p.key === k)?.label || k;

export default function POSPage() {
  const { t, locale } = useI18n();
  const fmt = (v) => Number(v || 0).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 });
  const ic = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none';

  const [tab, setTab] = useState('pos');
  const [stats, setStats] = useState(null);
  const [shift, setShift] = useState(null);

  // Modals
  const [showOpen, setShowOpen] = useState(false);
  const [showClose, setShowClose] = useState(false);
  const [openCash, setOpenCash] = useState('');
  const [closeCash, setCloseCash] = useState('');
  const [shiftLoading, setShiftLoading] = useState(false);

  // Products
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [cat, setCat] = useState('all');
  const [cats, setCats] = useState([]);
  const [pLoading, setPLoading] = useState(false);

  // Cart
  const [cart, setCart] = useState([]);
  const [discType, setDiscType] = useState('percent');
  const [discVal, setDiscVal] = useState('');
  const [payMethod, setPayMethod] = useState('cash');
  const [cashIn, setCashIn] = useState('');
  const [cardDig, setCardDig] = useState('');
  const [custName, setCustName] = useState('');
  const [saleLoading, setSaleLoading] = useState(false);

  // Receipt & void
  const [showReceipt, setShowReceipt] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [showVoid, setShowVoid] = useState(false);
  const [voidTarget, setVoidTarget] = useState(null);
  const [voidReason, setVoidReason] = useState('');
  const [voidLoading, setVoidLoading] = useState(false);

  // Holds
  const [holds, setHolds] = useState([]);
  const [showHolds, setShowHolds] = useState(false);

  // Reports
  const [rSales, setRSales] = useState([]);
  const [rShifts, setRShifts] = useState([]);
  const [rRefunds, setRRefunds] = useState([]);
  const [rLoading, setRLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const r = await posAPI.getStats();
      setStats(r.data);
      if (r.data.active_shift) setShift(r.data.active_shift);
    } catch { /* */ }
  }, []);

  const fetchProducts = useCallback(async () => {
    setPLoading(true);
    try {
      const r = await productsAPI.list({ page_size: 200, search: search || undefined });
      const d = r.data.results || (Array.isArray(r.data) ? r.data : []);
      setProducts(d);
      setCats([...new Set(d.map((p) => p.category).filter(Boolean))]);
    } catch { toast.error('فشل تحميل المنتجات'); }
    finally { setPLoading(false); }
  }, [search]);

  const fetchHolds = useCallback(async () => {
    try { const r = await posAPI.getHolds({ status: 'active' }); setHolds(r.data.results || r.data || []); } catch { /* */ }
  }, []);

  useEffect(() => { fetchStats(); fetchProducts(); fetchHolds(); }, [fetchStats, fetchProducts, fetchHolds]);

  const filtered = useMemo(() => cat === 'all' ? products : products.filter((p) => p.category === cat), [products, cat]);

  // Cart ops
  const addCart = (p) => {
    setCart((prev) => {
      const ex = prev.find((i) => i.pid === p.id);
      if (ex) {
        if (ex.qty >= p.quantity) { toast.error(`الكمية المتاحة ${p.quantity} فقط`); return prev; }
        return prev.map((i) => i.pid === p.id ? { ...i, qty: i.qty + 1 } : i);
      }
      return [...prev, { pid: p.id, name: p.name, sku: p.sku, price: p.unit_price, qty: 1, disc: 0, max: p.quantity }];
    });
  };
  const updQty = (pid, d) => setCart((prev) => prev.map((i) => {
    if (i.pid !== pid) return i;
    const nq = i.qty + d;
    if (nq <= 0) return i;
    if (nq > i.max) { toast.error('تجاوز الكمية المتاحة'); return i; }
    return { ...i, qty: nq };
  }));
  const rmCart = (pid) => setCart((p) => p.filter((i) => i.pid !== pid));
  const updDisc = (pid, v) => setCart((p) => p.map((i) => i.pid === pid ? { ...i, disc: Math.min(Math.max(Number(v) || 0, 0), 100) } : i));

  // Totals
  const subtotal = useMemo(() => cart.reduce((s, i) => s + i.price * i.qty * (1 - i.disc / 100), 0), [cart]);
  const discAmt = useMemo(() => {
    if (!discVal) return 0;
    return discType === 'percent' ? subtotal * Math.min(Number(discVal) || 0, 100) / 100 : Math.min(Number(discVal) || 0, subtotal);
  }, [subtotal, discType, discVal]);
  const afterDisc = subtotal - discAmt;
  const vatAmt = afterDisc * VAT;
  const total = afterDisc + vatAmt;
  const change = payMethod === 'cash' ? Math.max((Number(cashIn) || 0) - total, 0) : 0;

  // Shift ops
  const openShift = async () => {
    if (!openCash || Number(openCash) < 0) { toast.error('أدخل مبلغ الافتتاح'); return; }
    setShiftLoading(true);
    try { const r = await posAPI.openShift({ opening_cash: Number(openCash) }); setShift(r.data); setShowOpen(false); setOpenCash(''); toast.success('تم فتح الوردية'); fetchStats(); }
    catch { toast.error('فشل فتح الوردية'); } finally { setShiftLoading(false); }
  };
  const closeShift = async () => {
    setShiftLoading(true);
    try { await posAPI.closeShift(shift.id, { closing_cash: Number(closeCash) || 0 }); setShift(null); setShowClose(false); toast.success('تم إغلاق الوردية'); fetchStats(); }
    catch { toast.error('فشل الإغلاق'); } finally { setShiftLoading(false); }
  };

  // Sale
  const completeSale = async () => {
    if (!shift) { toast.error('افتح وردية أولاً'); return; }
    if (!cart.length) { toast.error('السلة فارغة'); return; }
    if (payMethod === 'cash' && Number(cashIn) < total) { toast.error('المبلغ المدفوع أقل من الإجمالي'); return; }
    if (payMethod === 'card' && cardDig.length < 4) { toast.error('أدخل آخر 4 أرقام البطاقة'); return; }
    setSaleLoading(true);
    try {
      const r = await posAPI.createSale({
        shift: shift.id,
        items: cart.map((i) => ({ product: i.pid, quantity: i.qty, discount: i.disc })),
        discount_type: discType, discount_value: Number(discVal) || 0,
        payment_method: payMethod,
        cash_received: payMethod === 'cash' ? Number(cashIn) : null,
        card_last_four: payMethod === 'card' ? cardDig.slice(-4) : null,
        customer_name: custName || null,
      });
      setReceipt(r.data); setShowReceipt(true);
      setCart([]); setDiscVal(''); setCashIn(''); setCardDig(''); setCustName('');
      toast.success('تم إتمام البيع'); fetchStats(); fetchProducts();
    } catch (e) { toast.error(e.response?.data?.error || 'فشل البيع'); } finally { setSaleLoading(false); }
  };
  const handleVoid = async () => {
    if (!voidReason.trim()) { toast.error('أدخل سبب الإلغاء'); return; }
    setVoidLoading(true);
    try { await posAPI.voidSale(voidTarget.id, { reason: voidReason }); setShowVoid(false); toast.success('تم الإلغاء'); fetchStats(); }
    catch { toast.error('فشل الإلغاء'); } finally { setVoidLoading(false); }
  };
  const holdOrder = async () => {
    if (!cart.length) return;
    try {
      await posAPI.createHold({ shift: shift?.id, items: cart.map((i) => ({ product: i.pid, quantity: i.qty, discount: i.disc })), discount_type: discType, discount_value: Number(discVal) || 0, customer_name: custName || null });
      setCart([]); setDiscVal(''); setCustName(''); toast.success('تم تعليق الطلب'); fetchHolds();
    } catch { toast.error('فشل التعليق'); }
  };
  const resumeHold = (h) => {
    setCart(h.items?.map((i) => ({ ...i, pid: i.product, max: 999 })) || []);
    setDiscType(h.discount_type || 'percent'); setDiscVal(h.discount_value || ''); setCustName(h.customer_name || '');
    toast.success('تم استئناف الطلب');
  };

  // Reports
  const fetchReports = useCallback(async () => {
    setRLoading(true);
    try {
      const [s, sh, r] = await Promise.all([posAPI.getSales({ page_size: 20 }), posAPI.getShifts({ page_size: 10 }), posAPI.getRefunds({ page_size: 10 })]);
      setRSales(s.data.results || s.data || []); setRShifts(sh.data.results || sh.data || []); setRRefunds(r.data.results || r.data || []);
    } catch { toast.error('فشل تحميل التقارير'); } finally { setRLoading(false); }
  }, []);
  useEffect(() => { if (tab === 'reports') fetchReports(); }, [tab, fetchReports]);

  const modalWrap = (show, close, content) => show && (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={close} />
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">{content}</div>
    </div>
  );

  return (
    <div className="space-y-4" style={{ minHeight: 'calc(100vh - 120px)' }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <ShoppingCart className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">نقطة البيع</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {shift ? <>وردية <span className="font-semibold text-emerald-600 dark:text-emerald-400">#{shift.shift_number || shift.id}</span> — مفتوحة</> : 'لا توجد وردية مفتوحة'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {stats && (
            <div className="hidden md:flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 ml-3">
              <span>مبيعات اليوم: <strong className="text-gray-900 dark:text-gray-100" dir="ltr">{fmt(stats.today_sales)} {t('sar')}</strong></span>
              {shift && <span>عمليات: <strong className="text-gray-900 dark:text-gray-100">{shift.transaction_count || 0}</strong></span>}
            </div>
          )}
          <button onClick={() => setShowOpen(true)} disabled={!!shift}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-amber-500 hover:bg-amber-600 text-white">
            <DollarSign className="w-4 h-4" /> فتح وردية
          </button>
          {shift && <button onClick={() => { setCloseCash(''); setShowClose(true); }}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 transition-colors">
            إغلاق الوردية
          </button>}
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            {[['pos', ShoppingCart, 'الكاشير'], ['reports', BarChart3, 'التقارير']].map(([k, Icon, lbl]) => (
              <button key={k} onClick={() => setTab(k)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${tab === k ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}`}>
                <Icon className="w-4 h-4" />{lbl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ─── POS TAB ────────────────────────────────────── */}
      {tab === 'pos' && (
        <div className="flex flex-col lg:flex-row gap-4" style={{ height: 'calc(100vh - 180px)' }}>
          {/* LEFT: Products 70% */}
          <div className="lg:w-[70%] flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-3 border-b border-gray-200 dark:border-gray-700 space-y-3">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="بحث بالاسم أو الكود أو الباركود..." autoFocus
                  className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400 text-sm focus:ring-2 focus:ring-emerald-500 outline-none" />
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setCat('all')} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${cat === 'all' ? 'bg-emerald-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>الكل</button>
                {cats.map((c) => (
                  <button key={c} onClick={() => setCat(c)} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${cat === c ? 'bg-emerald-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>{c}</button>
                ))}
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              {pLoading ? <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin text-emerald-500" /></div>
                : !filtered.length ? <div className="flex flex-col items-center justify-center h-full text-gray-400"><Package className="w-16 h-16 mb-3" /><p className="text-lg font-medium">لا توجد منتجات</p></div>
                : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {filtered.map((p) => (
                      <button key={p.id} onClick={() => p.quantity > 0 && addCart(p)} disabled={p.quantity <= 0}
                        className={`group text-right p-3 rounded-xl border transition-all duration-150 hover:shadow-md ${p.quantity <= 0 ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-50 cursor-not-allowed' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/10'}`}>
                        <div className="w-full h-14 rounded-lg bg-gray-100 dark:bg-gray-700 mb-2 flex items-center justify-center">
                          <Package className="w-6 h-6 text-gray-400 group-hover:text-emerald-500 transition-colors" />
                        </div>
                        <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{p.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-mono" dir="ltr">{p.sku}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400" dir="ltr">{Number(p.unit_price).toFixed(2)}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${p.quantity > 5 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : p.quantity > 0 ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'}`}>{p.quantity}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
            </div>
          </div>

          {/* RIGHT: Cart 30% */}
          <div className="lg:w-[30%] flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{shift ? `وردية #${shift.shift_number || shift.id}` : 'بدون وردية'}</span>
              <span className="flex items-center gap-1">رصيد: <strong className="text-gray-900 dark:text-gray-100" dir="ltr">{fmt(shift?.cash_balance || 0)}</strong></span>
            </div>
            <div className="px-3 pt-3"><input type="text" value={custName} onChange={(e) => setCustName(e.target.value)} placeholder="اسم العميل (اختياري)" className={`${ic} text-xs`} /></div>
            <div className="flex-1 overflow-y-auto px-3 py-2 min-h-0">
              {!cart.length ? <div className="flex flex-col items-center justify-center h-full text-gray-400"><ShoppingCart className="w-12 h-12 mb-2" /><p className="text-sm">السلة فارغة</p></div> : (
                <div className="space-y-2">
                  {cart.map((i) => (
                    <div key={i.pid} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5">
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{i.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400" dir="ltr">{fmt(i.price)} × {i.qty}</p>
                        </div>
                        <button onClick={() => rmCart(i.pid)} className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
                          <button onClick={() => updQty(i.pid, -1)} className="px-2 py-1 hover:bg-gray-200 dark:hover:bg-gray-600"><Minus className="w-3 h-3" /></button>
                          <span className="px-2.5 py-1 text-sm font-medium bg-white dark:bg-gray-700 min-w-[28px] text-center" dir="ltr">{i.qty}</span>
                          <button onClick={() => updQty(i.pid, 1)} className="px-2 py-1 hover:bg-gray-200 dark:hover:bg-gray-600"><Plus className="w-3 h-3" /></button>
                        </div>
                        <input type="number" min="0" max="100" value={i.disc || ''} onChange={(e) => updDisc(i.pid, e.target.value)} placeholder="خصم%"
                          className="w-16 px-1.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center" dir="ltr" />
                        <span className="text-xs font-bold text-gray-900 dark:text-gray-100 mr-auto" dir="ltr">{fmt(i.price * i.qty * (1 - i.disc / 100))}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {/* Totals */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-3 space-y-2 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-2">
                <select value={discType} onChange={(e) => setDiscType(e.target.value)} className="text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1.5">
                  <option value="percent">خصم %</option><option value="fixed">خصم ثابت</option>
                </select>
                <input type="number" min="0" value={discVal} onChange={(e) => setDiscVal(e.target.value)} placeholder="0" className="flex-1 px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" dir="ltr" />
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between text-gray-500 dark:text-gray-400"><span>المجموع الفرعي</span><span dir="ltr">{fmt(subtotal)}</span></div>
                {discAmt > 0 && <div className="flex justify-between text-red-500"><span>الخصم</span><span dir="ltr">-{fmt(discAmt)}</span></div>}
                <div className="flex justify-between text-gray-500 dark:text-gray-400"><span>ضريبة (15%)</span><span dir="ltr">{fmt(vatAmt)}</span></div>
                <div className="flex justify-between text-lg font-bold text-gray-900 dark:text-gray-100 pt-1 border-t border-gray-200 dark:border-gray-600"><span>الإجمالي</span><span dir="ltr">{fmt(total)}</span></div>
              </div>
              <div className="flex gap-1.5">
                {PAYMENTS.map((pm) => { const I = pm.icon; return (
                  <button key={pm.key} onClick={() => setPayMethod(pm.key)}
                    className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-lg text-xs font-medium transition-colors ${payMethod === pm.key ? 'bg-emerald-600 text-white' : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'}`}>
                    <I className="w-3.5 h-3.5" />{pm.label}
                  </button>
                ); })}
              </div>
              {payMethod === 'cash' && (
                <div className="flex items-center gap-2">
                  <input type="number" min="0" step="0.01" value={cashIn} onChange={(e) => setCashIn(e.target.value)} placeholder="المبلغ المدفوع" className={`flex-1 ${ic} text-sm`} dir="ltr" />
                  {cashIn && Number(cashIn) >= total && <div className="text-xs bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 px-2 py-1 rounded-lg whitespace-nowrap">الباقي: <strong dir="ltr">{fmt(change)}</strong></div>}
                </div>
              )}
              {payMethod === 'card' && <input type="text" maxLength={4} value={cardDig} onChange={(e) => setCardDig(e.target.value.replace(/\D/g, ''))} placeholder="آخر 4 أرقام" className={`${ic} text-sm text-center`} dir="ltr" />}
              <div className="space-y-2 pt-1">
                <button onClick={completeSale} disabled={saleLoading || !cart.length || !shift}
                  className="w-full py-3 rounded-xl text-white font-bold text-base transition-colors flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 shadow-lg shadow-emerald-200 dark:shadow-emerald-900/30">
                  {saleLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />} إتمام البيع
                </button>
                <div className="flex gap-2">
                  <button onClick={() => setShowHolds(true)} className="flex-1 py-2 rounded-lg text-sm font-medium border border-amber-300 dark:border-amber-700 text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors flex items-center justify-center gap-1.5">
                    <Pause className="w-4 h-4" /> تعليق
                  </button>
                  <button onClick={() => { setCart([]); setDiscVal(''); setCustName(''); }} className="flex-1 py-2 rounded-lg text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center justify-center gap-1.5">
                    <X className="w-4 h-4" /> إلغاء
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── REPORTS TAB ─────────────────────────────────── */}
      {tab === 'reports' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'مبيعات اليوم', value: stats?.today_sales || 0, icon: TrendingUp, c: 'emerald' },
              { label: 'عدد العمليات', value: stats?.today_transactions || 0, icon: Receipt, c: 'blue' },
              { label: 'المردودات', value: stats?.today_refunds || 0, icon: RotateCcw, c: 'red' },
              { label: 'صافي الأرباح', value: stats?.today_profit || 0, icon: DollarSign, c: 'amber' },
            ].map((cd) => { const I = cd.icon; return (
              <div key={cd.label} className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div><p className="text-xs text-gray-500 dark:text-gray-400">{cd.label}</p><p className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-1" dir="ltr">{fmt(cd.value)}</p></div>
                <div className={`w-10 h-10 rounded-lg bg-${cd.c}-100 dark:bg-${cd.c}-900/20 flex items-center justify-center`}><I className={`w-5 h-5 text-${cd.c}-600 dark:text-${cd.c}-400`} /></div>
              </div>
            ); })}
          </div>
          {rLoading ? <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-emerald-500" /></div> : (
            <>
              {/* Recent Sales */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2"><Receipt className="w-4 h-4 text-emerald-600" /><h3 className="font-bold text-gray-900 dark:text-gray-100">المبيعات الأخيرة</h3></div>
                <div className="overflow-x-auto max-h-72 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-800/70 sticky top-0 text-gray-500 dark:text-gray-400 text-xs">
                      <tr><th className="text-right px-4 py-2">#</th><th className="text-right px-4 py-2">التاريخ</th><th className="text-right px-4 py-2">الدفع</th><th className="text-right px-4 py-2">الإجمالي</th><th className="text-right px-4 py-2">الحالة</th><th className="text-right px-4 py-2">إجراء</th></tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {!rSales.length ? <tr><td colSpan={6} className="text-center py-8 text-gray-400">لا توجد مبيعات</td></tr>
                        : rSales.map((s) => (
                          <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                            <td className="px-4 py-2 font-mono text-emerald-600 dark:text-emerald-400" dir="ltr">{s.receipt_number || s.id}</td>
                            <td className="px-4 py-2 text-gray-600 dark:text-gray-300">{s.created_at}</td>
                            <td className="px-4 py-2"><span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">{getPayLabel(s.payment_method)}</span></td>
                            <td className="px-4 py-2 font-semibold" dir="ltr">{fmt(s.total_amount)}</td>
                            <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'voided' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'}`}>{s.status === 'voided' ? 'ملغاة' : 'مكتملة'}</span></td>
                            <td className="px-4 py-2">{s.status !== 'voided' && <button onClick={() => { setVoidTarget(s); setShowVoid(true); setVoidReason(''); }} className="text-xs text-red-600 dark:text-red-400 hover:underline">إلغاء</button>}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
              {/* Shifts & Refunds */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2"><Clock className="w-4 h-4 text-accent-500" /><h3 className="font-bold text-gray-900 dark:text-gray-100">سجل الورديات</h3></div>
                  <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-800/70 sticky top-0 text-gray-500 dark:text-gray-400 text-xs">
                        <tr><th className="text-right px-4 py-2">#</th><th className="text-right px-4 py-2">الافتتاح</th><th className="text-right px-4 py-2">المبيعات</th><th className="text-right px-4 py-2">الحالة</th></tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {rShifts.map((sh) => (
                          <tr key={sh.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                            <td className="px-4 py-2 font-mono" dir="ltr">{sh.shift_number || sh.id}</td>
                            <td className="px-4 py-2 text-gray-600 dark:text-gray-300">{sh.opened_at}</td>
                            <td className="px-4 py-2 font-semibold" dir="ltr">{fmt(sh.total_sales || 0)}</td>
                            <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded-full ${sh.status === 'open' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}>{sh.status === 'open' ? 'مفتوحة' : 'مغلقة'}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2"><RotateCcw className="w-4 h-4 text-red-600" /><h3 className="font-bold text-gray-900 dark:text-gray-100">المردودات</h3></div>
                  <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-800/70 sticky top-0 text-gray-500 dark:text-gray-400 text-xs">
                        <tr><th className="text-right px-4 py-2">#</th><th className="text-right px-4 py-2">التاريخ</th><th className="text-right px-4 py-2">المبلغ</th><th className="text-right px-4 py-2">السبب</th></tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {!rRefunds.length ? <tr><td colSpan={4} className="text-center py-8 text-gray-400">لا توجد مردودات</td></tr>
                          : rRefunds.map((r) => (
                            <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                              <td className="px-4 py-2 font-mono" dir="ltr">{r.id}</td>
                              <td className="px-4 py-2 text-gray-600 dark:text-gray-300">{r.created_at}</td>
                              <td className="px-4 py-2 font-semibold text-red-600" dir="ltr">{fmt(r.amount)}</td>
                              <td className="px-4 py-2 text-gray-500 dark:text-gray-400 text-xs max-w-[120px] truncate">{r.reason}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ─── MODALS ─────────────────────────────────────── */}
      {/* Open Shift */}
      {modalWrap(showOpen, () => setShowOpen(false), (
        <>
          <div className="text-center mb-4">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center"><DollarSign className="w-7 h-7 text-emerald-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">فتح وردية جديدة</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">أدخل مبلغ النقدية في الدرج</p>
          </div>
          <input type="number" min="0" step="0.01" value={openCash} onChange={(e) => setOpenCash(e.target.value)} placeholder="مبلغ الافتتاح" className={`${ic} text-center text-lg mb-4`} dir="ltr" autoFocus onKeyDown={(e) => e.key === 'Enter' && openShift()} />
          <div className="flex gap-3">
            <button onClick={openShift} disabled={shiftLoading} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50">
              {shiftLoading && <Loader2 className="w-4 h-4 animate-spin" />} فتح الوردية
            </button>
            <button onClick={() => setShowOpen(false)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
          </div>
        </>
      ))}

      {/* Close Shift */}
      {modalWrap(showClose, () => setShowClose(false), (
        <>
          <div className="text-center mb-4">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"><Receipt className="w-7 h-7 text-gray-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">إغلاق الوردية</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">أدخل المبلغ الفعلي في الدرج</p>
          </div>
          <input type="number" min="0" step="0.01" value={closeCash} onChange={(e) => setCloseCash(e.target.value)} placeholder="مبلغ الإغلاق" className={`${ic} text-center text-lg mb-4`} dir="ltr" autoFocus onKeyDown={(e) => e.key === 'Enter' && closeShift()} />
          <div className="flex gap-3">
            <button onClick={closeShift} disabled={shiftLoading} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50">
              {shiftLoading && <Loader2 className="w-4 h-4 animate-spin" />} إغلاق
            </button>
            <button onClick={() => setShowClose(false)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">تراجع</button>
          </div>
        </>
      ))}

      {/* Receipt */}
      {showReceipt && receipt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowReceipt(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2"><CheckCircle className="w-5 h-5 text-emerald-600" /> تم البيع بنجاح</h3>
              <button onClick={() => setShowReceipt(false)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><X className="w-5 h-5" /></button>
            </div>
            <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-4 bg-gray-50 dark:bg-gray-700/30">
              <div className="text-center mb-3"><p className="font-bold text-gray-900 dark:text-gray-100">إيصال بيع</p><p className="text-xs text-gray-500" dir="ltr">{receipt.receipt_number || `#${receipt.id}`}</p></div>
              <div className="divide-y divide-gray-200 dark:divide-gray-600">
                {(receipt.items || []).map((i, idx) => (
                  <div key={idx} className="py-2 flex justify-between text-sm"><span className="text-gray-700 dark:text-gray-300">{i.product_name} ×{i.quantity}</span><span className="font-medium" dir="ltr">{fmt(i.total)}</span></div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600 space-y-1">
                <div className="flex justify-between text-sm"><span className="text-gray-500">المجموع</span><span dir="ltr">{fmt(receipt.subtotal)}</span></div>
                {receipt.discount > 0 && <div className="flex justify-between text-sm text-red-500"><span>الخصم</span><span dir="ltr">-{fmt(receipt.discount)}</span></div>}
                <div className="flex justify-between text-sm"><span className="text-gray-500">الضريبة</span><span dir="ltr">{fmt(receipt.vat_amount)}</span></div>
                <div className="flex justify-between text-base font-bold pt-1 border-t border-gray-200 dark:border-gray-600"><span>الإجمالي</span><span dir="ltr">{fmt(receipt.total_amount)}</span></div>
                {receipt.change > 0 && <div className="flex justify-between text-sm text-emerald-600"><span>الباقي</span><span dir="ltr">{fmt(receipt.change)}</span></div>}
              </div>
              <p className="text-center text-xs text-gray-400 mt-3">شكراً لتعاملكم معنا</p>
            </div>
            <button onClick={() => setShowReceipt(false)} className="w-full mt-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors">تم</button>
          </div>
        </div>
      )}

      {/* Void */}
      {modalWrap(showVoid, () => setShowVoid(false), (
        <>
          <div className="text-center mb-4">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600" /></div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">إلغاء عملية البيع</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">هذا الإجراء لا يمكن التراجع عنه</p>
          </div>
          <textarea value={voidReason} onChange={(e) => setVoidReason(e.target.value)} placeholder="أدخل سبب الإلغاء..." rows={3} className={`${ic} mb-4`} autoFocus />
          <div className="flex gap-3">
            <button onClick={handleVoid} disabled={voidLoading} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50">
              {voidLoading && <Loader2 className="w-4 h-4 animate-spin" />} تأكيد الإلغاء
            </button>
            <button onClick={() => setShowVoid(false)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">تراجع</button>
          </div>
        </>
      ))}

      {/* Holds */}
      {showHolds && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowHolds(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-md max-h-[70vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2"><Pause className="w-4 h-4 text-amber-500" /> الطلبات المعلقة ({holds.length})</h3>
              <button onClick={() => setShowHolds(false)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {!holds.length ? <div className="text-center py-8 text-gray-400"><Archive className="w-12 h-12 mx-auto mb-2" /><p>لا توجد طلبات معلقة</p></div>
                : holds.map((h) => (
                  <div key={h.id} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3">
                    <div className="flex items-center justify-between mb-2"><span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{h.customer_name || 'بدون اسم'}</span><span className="text-xs text-gray-500 dark:text-gray-400">{h.items?.length || 0} منتج</span></div>
                    <div className="flex gap-2">
                      <button onClick={() => { resumeHold(h); setShowHolds(false); }} className="flex-1 py-1.5 text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors flex items-center justify-center gap-1"><RotateCcw className="w-3 h-3" /> استئناف</button>
                      <button onClick={async () => { try { await posAPI.deleteHold(h.id); fetchHolds(); toast.success('تم الحذف'); } catch { toast.error('فشل الحذف'); }}}
                        className="py-1.5 px-3 text-xs font-medium text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"><Trash2 className="w-3 h-3" /></button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
