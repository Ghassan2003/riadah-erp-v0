/**
 * Invoicing system page – الفوترة (RTL Arabic ERP)
 * Tabs: Invoices, Payments, Payment Reminders
 */
import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { invoicingAPI } from '../api';
import {
  FileText, Plus, Search, Eye, Loader2, ChevronLeft, ChevronRight, X, Save,
  Trash2, RotateCcw, Send, CheckCircle, Copy, Ban, Download, CreditCard, Bell,
  AlertTriangle, DollarSign, Receipt, Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';
/* eslint-disable react/prop-types */

const ITYPE = {
  sales: ['فاتورة مبيعات', 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'],
  purchase: ['فاتورة مشتريات', 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300'],
  credit_note: ['إشعار دائن', 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'],
  debit_note: ['إشعار مدين', 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'],
};
const STS = {
  draft: ['مسودة', 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'],
  sent: ['مرسلة', 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'],
  accepted: ['مقبولة', 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'],
  cancelled: ['ملغاة', 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  overdue: ['متأخرة', 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
};
const PSTS = {
  paid: ['مدفوعة', 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'],
  unpaid: ['غير مدفوعة', 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'],
  partial: ['مدفوعة جزئياً', 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'],
};
const badge = (map, key) => { const [label, cls] = map[key] || [key, '']; return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>; };
const IP = 'text-right px-3 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap';

export default function InvoicingPage() {
  const [tab, setTab] = useState('invoices');
  const tabs = [
    { key: 'invoices', label: 'الفواتير', icon: FileText },
    { key: 'payments', label: 'المدفوعات', icon: CreditCard },
    { key: 'reminders', label: 'تذكيرات الدفع', icon: Bell },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الفوترة</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة الفواتير والمدفوعات وتذكيرات الدفع</p>
      </div>
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.key ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>
      {tab === 'invoices' && <InvoicesTab />}
      {tab === 'payments' && <PaymentsTab />}
      {tab === 'reminders' && <RemindersTab />}
    </div>
  );
}

/* ===== TAB 1 — INVOICES ===== */
function InvoicesTab() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tf, setTf] = useState('');
  const [sf, setSf] = useState('');
  const [pf, setPf] = useState('');
  const [df, setDf] = useState('');
  const [dt, setDt] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const ps = 20;
  const [exporting, setExporting] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [aLoading, setALoading] = useState(null);
  const [form, setForm] = useState({ invoice_type: 'sales', customer: '', items: [{ description: '', quantity: 1, unit_price: 0 }], discount: 0 });
  const [fLoading, setFLoading] = useState(false);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, search: search || undefined, invoice_type: tf || undefined, status: sf || undefined, payment_status: pf || undefined, date_from: df || undefined, date_to: dt || undefined };
      const [ir, sr] = await Promise.all([invoicingAPI.getInvoices(params), invoicingAPI.getStats()]);
      const d = ir.data;
      setInvoices(d.results || (Array.isArray(d) ? d : []));
      setTotal(d.count || d.length || 0);
      setStats(sr.data);
      setPage(p);
    } catch { toast.error('فشل تحميل الفواتير'); } finally { setLoading(false); }
  }, [search, tf, sf, pf, df, dt]);

  useEffect(() => { fetch(1); }, [fetch]);
  const resetF = () => { setSearch(''); setTf(''); setSf(''); setPf(''); setDf(''); setDt(''); setPage(1); };

  const handleExport = async () => {
    try { setExporting(true); const r = await invoicingAPI.export(); const u = URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = u; a.download = 'invoices.xlsx'; a.click(); a.remove(); toast.success('تم التصدير'); }
    catch { toast.error('فشل التصدير'); } finally { setExporting(false); }
  };

  const act = async (id, fn, msg) => { setALoading(id); try { await fn(); toast.success(msg); fetch(page); } catch (e) { toast.error(e.response?.data?.error || 'خطأ'); } finally { setALoading(null); } };
  const openDetail = async (inv) => { try { const r = await invoicingAPI.getInvoice(inv.id); setDetailData(r.data); setShowDetail(inv.id); } catch { toast.error('فشل تحميل التفاصيل'); } };

  const addItem = () => setForm({ ...form, items: [...form.items, { description: '', quantity: 1, unit_price: 0 }] });
  const rmItem = (i) => setForm({ ...form, items: form.items.filter((_, idx) => idx !== i) });
  const upItem = (i, k, v) => setForm({ ...form, items: form.items.map((it, idx) => idx === i ? { ...it, [k]: k === 'description' ? v : Number(v) || 0 } : it) });
  const sub = form.items.reduce((s, it) => s + it.quantity * it.unit_price, 0);
  const vat = (sub - form.discount) * 0.15;
  const grand = sub - form.discount + vat;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.customer.trim()) { toast.error('يرجى إدخال العميل'); return; }
    setFLoading(true);
    try {
      await invoicingAPI.createInvoice({ ...form, discount: Number(form.discount) || 0 });
      toast.success('تم إنشاء الفاتورة');
      setShowCreate(false);
      setForm({ invoice_type: 'sales', customer: '', items: [{ description: '', quantity: 1, unit_price: 0 }], discount: 0 });
      fetch(1);
    } catch (err) { toast.error(err.response?.data?.error || 'فشل الإنشاء'); } finally { setFLoading(false); }
  };

  const tp = Math.ceil(total / ps);
  const statCards = [
    ['إجمالي الفواتير', stats.total_invoices, FileText, 'from-riadah-400 to-riadah-500'],
    ['إجمالي المبالغ', fmt(stats.total_amount), DollarSign, 'from-emerald-500 to-emerald-600'],
    ['المبلغ المدفوع', fmt(stats.paid_amount), CheckCircle, 'from-green-500 to-green-600'],
    ['المبلغ غير المدفوع', fmt(stats.unpaid_amount), Clock, 'from-red-500 to-red-600'],
    ['فواتير متأخرة', stats.overdue_count, AlertTriangle, 'from-orange-500 to-orange-600'],
  ];
  const ths = ['رقم الفاتورة', 'النوع', 'العميل/المورد', 'تاريخ الإصدار', 'تاريخ الاستحقاق', 'المبلغ', 'الضريبة', 'حالة الدفع', 'الحالة', 'إجراءات'];

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {statCards.map(([label, value, Icon, gradient], i) => (
          <div key={i} className={`bg-gradient-to-br ${gradient} rounded-xl p-4 text-white shadow-lg`}>
            <div className="flex items-center justify-between mb-2"><Icon className="w-5 h-5 opacity-80" /><span className="text-xs opacity-80">{label}</span></div>
            <p className="text-xl font-bold">{value ?? '—'}</p>
          </div>
        ))}
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button onClick={resetF} className="text-sm text-gray-500 hover:text-accent-500 dark:text-gray-400 dark:hover:text-accent-400">مسح الفلاتر</button>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}تصدير Excel
          </button>
          <button onClick={() => setShowCreate(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium">
            <Plus className="w-4 h-4" />إنشاء فاتورة
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="بحث..." className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm focus:ring-2 focus:ring-accent-500" />
        </div>
        <select value={tf} onChange={(e) => { setTf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">كل الأنواع</option>{Object.entries(ITYPE).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={sf} onChange={(e) => { setSf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">كل الحالات</option>{Object.entries(STS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={pf} onChange={(e) => { setPf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
          <option value="">حالة الدفع</option>{Object.entries(PSTS).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <input type="date" value={df} onChange={(e) => { setDf(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
        <input type="date" value={dt} onChange={(e) => { setDt(e.target.value); setPage(1); }} className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
          : invoices.length === 0 ? <div className="text-center py-20 text-gray-400"><Receipt className="w-16 h-16 mx-auto mb-3 opacity-40" /><p className="font-medium">لا توجد فواتير</p></div>
          : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{ths.map((h) => <th key={h} className={IP}>{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{invoices.map((inv) => (
              <tr key={inv.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                <td className="px-3 py-2.5"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300 bg-riadah-50 dark:bg-riadah-900/30 px-2 py-0.5 rounded">{inv.invoice_number}</span></td>
                <td className="px-3 py-2.5">{badge(ITYPE, inv.invoice_type)}</td>
                <td className="px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100">{inv.customer_name || inv.supplier_name || '—'}</td>
                <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{inv.issue_date}</td>
                <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{inv.due_date}</td>
                <td className="px-3 py-2.5 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(inv.total_amount)}</td>
                <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300" dir="ltr">{fmt(inv.vat_amount)}</td>
                <td className="px-3 py-2.5">{badge(PSTS, inv.payment_status)}</td>
                <td className="px-3 py-2.5">{badge(STS, inv.status)}</td>
                <td className="px-3 py-2.5"><div className="flex items-center gap-1 flex-wrap">
                  <button onClick={() => openDetail(inv)} className="p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" title="عرض"><Eye className="w-4 h-4" /></button>
                  <button onClick={() => act(inv.id, () => invoicingAPI.sendInvoice(inv.id), 'تم الإرسال')} disabled={aLoading === inv.id} className="p-1.5 text-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20 rounded-lg" title="إرسال"><Send className="w-4 h-4" /></button>
                  <button onClick={() => act(inv.id, () => invoicingAPI.changeStatus(inv.id, { status: 'accepted' }), 'تم القبول')} disabled={aLoading === inv.id} className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg" title="قبول"><CheckCircle className="w-4 h-4" /></button>
                  <button onClick={() => act(inv.id, () => invoicingAPI.changeStatus(inv.id, { status: 'cancelled' }), 'تم الإلغاء')} disabled={aLoading === inv.id} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title="إلغاء"><Ban className="w-4 h-4" /></button>
                  <button onClick={() => act(inv.id, () => invoicingAPI.duplicateInvoice(inv.id), 'تم التكرار')} disabled={aLoading === inv.id} className="p-1.5 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg" title="تكرار"><Copy className="w-4 h-4" /></button>
                  {inv.is_deleted
                    ? <button onClick={() => act(inv.id, () => invoicingAPI.restoreInvoice(inv.id), 'تم الاستعادة')} disabled={aLoading === inv.id} className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg" title="استعادة"><RotateCcw className="w-4 h-4" /></button>
                    : <button onClick={() => act(inv.id, () => invoicingAPI.deleteInvoice(inv.id), 'تم الحذف')} disabled={aLoading === inv.id} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title="حذف"><Trash2 className="w-4 h-4" /></button>}
                </div></td>
              </tr>
            ))}</tbody></table></div>}

        {tp > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">{((page - 1) * ps) + 1} - {Math.min(page * ps, total)} من {total}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetch(page - 1)} disabled={page <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">{page} / {tp}</span>
              <button onClick={() => fetch(page + 1)} disabled={page >= tp} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && <Modal title="إنشاء فاتورة" onClose={() => setShowCreate(false)} wide><form onSubmit={handleCreate} className="p-5 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع الفاتورة</label>
            <select value={form.invoice_type} onChange={(e) => setForm({ ...form, invoice_type: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
              {Object.entries(ITYPE).map(([k, [v]]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">العميل / المورد <span className="text-red-500">*</span></label>
            <input value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" /></div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2"><label className="text-sm font-medium text-gray-700 dark:text-gray-300">البنود</label>
            <button type="button" onClick={addItem} className="text-accent-500 hover:text-accent-600 text-xs font-medium flex items-center gap-1"><Plus className="w-3 h-3" /> إضافة بند</button></div>
          <div className="space-y-2 max-h-60 overflow-y-auto">{form.items.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input value={item.description} onChange={(e) => upItem(idx, 'description', e.target.value)} placeholder="الوصف" className="flex-1 min-w-0 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              <input type="number" value={item.quantity} onChange={(e) => upItem(idx, 'quantity', e.target.value)} className="w-20 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" min="1" />
              <input type="number" value={item.unit_price} onChange={(e) => upItem(idx, 'unit_price', e.target.value)} className="w-28 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" min="0" step="0.01" dir="ltr" />
              <button type="button" onClick={() => rmItem(idx)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><X className="w-4 h-4" /></button>
            </div>))}</div>
        </div>
        <div className="grid grid-cols-3 gap-3 pt-2">
          <div><label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">المجموع الفرعي</label><p className="text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(sub)}</p></div>
          <div><label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">الخصم</label>
            <input type="number" value={form.discount} onChange={(e) => setForm({ ...form, discount: Number(e.target.value) || 0 })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" /></div>
          <div><label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">ضريبة 15%</label><p className="text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(vat)}</p></div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 flex justify-between items-center">
          <span className="font-medium text-gray-700 dark:text-gray-300">الإجمالي</span>
          <span className="text-lg font-bold text-gray-900 dark:text-gray-100" dir="ltr">{fmt(grand)}</span>
        </div>
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={fLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
            {fLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الإنشاء...</> : <><Save className="w-4 h-4" /> إنشاء الفاتورة</>}</button>
          <button type="button" onClick={() => setShowCreate(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
        </div>
      </form></Modal>}

      {/* Detail Modal */}
      {showDetail && detailData && <Modal title={`فاتورة ${detailData.invoice_number}`} onClose={() => setShowDetail(null)} wide><div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[['النوع', badge(ITYPE, detailData.invoice_type)], ['العميل', detailData.customer_name || '—'], ['تاريخ الإصدار', detailData.issue_date], ['تاريخ الاستحقاق', detailData.due_date], ['المبلغ الإجمالي', fmt(detailData.total_amount)], ['الضريبة', fmt(detailData.vat_amount)], ['حالة الدفع', badge(PSTS, detailData.payment_status)], ['الحالة', badge(STS, detailData.status)]].map(([label, value], i) => (
            <div key={i} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5"><p className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{label}</p><p className="text-sm font-medium text-gray-900 dark:text-gray-100">{value}</p></div>
          ))}
        </div>
        {detailData.items?.length > 0 && <div><h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">بنود الفاتورة</h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700"><table className="w-full text-sm"><thead><tr className="bg-gray-50 dark:bg-gray-800/70"><th className="text-right px-3 py-2 text-xs font-medium text-gray-500">الوصف</th><th className="text-right px-3 py-2 text-xs font-medium text-gray-500">الكمية</th><th className="text-right px-3 py-2 text-xs font-medium text-gray-500">السعر</th><th className="text-right px-3 py-2 text-xs font-medium text-gray-500">المجموع</th></tr></thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{detailData.items.map((it, i) => <tr key={i}><td className="px-3 py-2">{it.description}</td><td className="px-3 py-2" dir="ltr">{it.quantity}</td><td className="px-3 py-2" dir="ltr">{fmt(it.unit_price)}</td><td className="px-3 py-2 font-medium" dir="ltr">{fmt(it.quantity * it.unit_price)}</td></tr>)}</tbody></table></div></div>}
        {detailData.payments?.length > 0 && <div><h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">المدفوعات</h4>
          <div className="space-y-1">{detailData.payments.map((p, i) => <div key={i} className="flex justify-between items-center bg-green-50 dark:bg-green-900/10 rounded-lg px-3 py-2 text-sm"><span className="text-gray-700 dark:text-gray-300">{p.payment_number} — {p.payment_method}</span><span className="font-semibold text-green-700 dark:text-green-400" dir="ltr">{fmt(p.amount)}</span></div>)}</div></div>}
        {detailData.reminders?.length > 0 && <div><h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">التذكيرات</h4>
          <div className="space-y-1">{detailData.reminders.map((r, i) => <div key={i} className="flex justify-between items-center bg-orange-50 dark:bg-orange-900/10 rounded-lg px-3 py-2 text-sm"><span className="text-gray-700 dark:text-gray-300">{r.reminder_type} — {r.sent_via}</span><span className="text-gray-500 text-xs">{r.sent_date}</span></div>)}</div></div>}
      </div></Modal>}
    </div>
  );
}

/* ===== TAB 2 — PAYMENTS ===== */
function PaymentsTab() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';
  const fmt = (v) => Number(v || 0).toLocaleString(nl, { minimumFractionDigits: 2 });
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [selInv, setSelInv] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [pf, setPf] = useState({ invoice: '', amount: '', payment_method: 'cash', reference: '' });
  const [pLoading, setPLoading] = useState(false);
  const [delConf, setDelConf] = useState(null);
  const [delLoading, setDelLoading] = useState(false);

  useEffect(() => { (async () => { setLoading(true); try { const r = await invoicingAPI.getInvoices({ page_size: 200 }); setInvoices(r.data.results || r.data); } catch { toast.error('فشل تحميل الفواتير'); } finally { setLoading(false); } })(); }, []);

  const loadPay = async (id) => { try { const r = await invoicingAPI.getPayments(id); setPayments(r.data.results || (Array.isArray(r.data) ? r.data : [])); } catch { toast.error('فشل تحميل المدفوعات'); } };
  const sel = (inv) => { setSelInv(inv); loadPay(inv.id); };

  const handleAdd = async (e) => {
    e.preventDefault(); if (!pf.invoice || !pf.amount) { toast.error('يرجى تعبئة الحقول'); return; }
    setPLoading(true);
    try { await invoicingAPI.createPayment(pf.invoice, { amount: Number(pf.amount), payment_method: pf.payment_method, reference: pf.reference }); toast.success('تم إضافة الدفعة'); setShowAdd(false); setPf({ invoice: '', amount: '', payment_method: 'cash', reference: '' }); if (selInv) loadPay(selInv.id); }
    catch (err) { toast.error(err.response?.data?.error || 'فشل'); } finally { setPLoading(false); }
  };

  const handleDel = async () => {
    if (!delConf) return; setDelLoading(true);
    try { await invoicingAPI.deletePayment(selInv.id, delConf.id); toast.success('تم الحذف'); setDelConf(null); loadPay(selInv.id); } catch { toast.error('فشل'); } finally { setDelLoading(false); }
  };

  const methods = { cash: 'نقدي', bank_transfer: 'تحويل بنكي', card: 'بطاقة', check: 'شيك' };
  const payThs = ['رقم الدفعة', 'رقم الفاتورة', 'المبلغ', 'طريقة الدفع', 'التاريخ', 'المرجع', 'إجراءات'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-500 dark:text-gray-400">اختر فاتورة لعرض المدفوعات</p>
        {selInv && <button onClick={() => setShowAdd(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" /> إضافة دفعة</button>}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden max-h-[500px]">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700"><div className="relative"><Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" /><input placeholder="بحث..." className="w-full pr-9 pl-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 dark:text-white text-sm" /></div></div>
          {loading ? <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-accent-500" /></div>
            : <div className="overflow-y-auto max-h-[420px]">{invoices.map((inv) => (
              <button key={inv.id} onClick={() => sel(inv)} className={`w-full text-right px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 transition-colors ${selInv?.id === inv.id ? 'bg-riadah-50 dark:bg-riadah-900/20 border-r-4 border-r-blue-600' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'}`}>
                <div className="flex justify-between items-center"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{inv.invoice_number}</span>{badge(PSTS, inv.payment_status)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{inv.customer_name || inv.supplier_name}</p>
              </button>))}</div>}
        </div>
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {!selInv ? <div className="flex items-center justify-center py-20 text-gray-400"><CreditCard className="w-12 h-12 opacity-40 ml-3" /><p>اختر فاتورة</p></div>
            : payments.length === 0 ? <div className="flex items-center justify-center py-20 text-gray-400"><p>لا توجد مدفوعات</p></div>
            : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{payThs.map((h) => <th key={h} className={IP}>{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{payments.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-emerald-700 dark:text-emerald-300">{p.payment_number}</td>
                  <td className="px-4 py-3 text-sm">{p.invoice_number}</td>
                  <td className="px-4 py-3 text-sm font-semibold" dir="ltr">{fmt(p.amount)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{methods[p.payment_method] || p.payment_method}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{p.payment_date}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{p.reference || '—'}</td>
                  <td className="px-4 py-3"><button onClick={() => setDelConf(p)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button></td>
                </tr>))}</tbody></table></div>}
        </div>
      </div>

      {/* Add Payment Modal */}
      {showAdd && <Modal title="إضافة دفعة" onClose={() => setShowAdd(false)}><form onSubmit={handleAdd} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الفاتورة</label>
          <select value={pf.invoice} onChange={(e) => setPf({ ...pf, invoice: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required>
            <option value="">اختر فاتورة...</option>{invoices.filter((i) => i.payment_status !== 'paid').map((i) => <option key={i.id} value={i.id}>{i.invoice_number} — {i.customer_name || i.supplier_name}</option>)}
          </select></div>
        <div className="grid grid-cols-2 gap-3">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المبلغ</label>
            <input type="number" value={pf.amount} onChange={(e) => setPf({ ...pf, amount: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" dir="ltr" min="0" step="0.01" required /></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">طريقة الدفع</label>
            <select value={pf.payment_method} onChange={(e) => setPf({ ...pf, payment_method: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
              {Object.entries(methods).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
        </div>
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المرجع</label>
          <input value={pf.reference} onChange={(e) => setPf({ ...pf, reference: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" placeholder="اختياري" /></div>
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={pLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
            {pLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الإضافة...</> : <><Save className="w-4 h-4" /> إضافة</>}</button>
          <button type="button" onClick={() => setShowAdd(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
        </div>
      </form></Modal>}

      {/* Delete Confirmation */}
      {delConf && <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setDelConf(null)} />
        <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6"><div className="text-center">
          <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600 dark:text-red-400" /></div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">تأكيد الحذف</h3>
          <p className="text-gray-600 dark:text-gray-300 mb-5">حذف الدفعة <span className="font-semibold">{delConf.payment_number}</span>؟</p>
          <div className="flex gap-3">
            <button onClick={handleDel} disabled={delLoading} className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
              {delLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحذف...</> : <><Trash2 className="w-4 h-4" /> حذف</>}</button>
            <button onClick={() => setDelConf(null)} className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
          </div>
        </div></div>
      </div>}
    </div>
  );
}

/* ===== TAB 3 — REMINDERS ===== */
function RemindersTab() {
  const [invoices, setInvoices] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [selInv, setSelInv] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [rf, setRf] = useState({ invoice: '', reminder_type: 'first', sent_via: 'email' });
  const [rLoading, setRLoading] = useState(false);

  useEffect(() => { (async () => { setLoading(true); try { const r = await invoicingAPI.getInvoices({ page_size: 200, payment_status: 'unpaid' }); setInvoices(r.data.results || r.data); } catch { toast.error('فشل'); } finally { setLoading(false); } })(); }, []);

  const loadRem = async (id) => { try { const r = await invoicingAPI.getReminders(id); setReminders(r.data.results || (Array.isArray(r.data) ? r.data : [])); } catch { toast.error('فشل'); } };
  const sel = (inv) => { setSelInv(inv); loadRem(inv.id); };

  const handleCreate = async (e) => {
    e.preventDefault(); if (!rf.invoice) { toast.error('اختر فاتورة'); return; }
    setRLoading(true);
    try { await invoicingAPI.createReminder(rf.invoice, { reminder_type: rf.reminder_type, sent_via: rf.sent_via }); toast.success('تم إرسال التذكير'); setShowAdd(false); setRf({ invoice: '', reminder_type: 'first', sent_via: 'email' }); if (selInv) loadRem(selInv.id); }
    catch (err) { toast.error(err.response?.data?.error || 'فشل'); } finally { setRLoading(false); }
  };

  const rTypes = { first: 'أول تذكير', second: 'تذكير ثاني', third: 'تذكير ثالث', final: 'تذكير أخير' };
  const sVia = { email: 'بريد إلكتروني', sms: 'رسالة نصية', whatsapp: 'واتساب' };
  const remThs = ['رقم الفاتورة', 'نوع التذكير', 'طريقة الإرسال', 'تاريخ الإرسال', 'الحالة'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-500 dark:text-gray-400">اختر فاتورة لعرض التذكيرات</p>
        {selInv && <button onClick={() => setShowAdd(true)} className="bg-riadah-500 hover:bg-riadah-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" /> إنشاء تذكير</button>}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden max-h-[500px]">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 font-medium text-sm text-gray-700 dark:text-gray-300">فواتير غير مدفوعة</div>
          {loading ? <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-accent-500" /></div>
            : <div className="overflow-y-auto max-h-[440px]">{invoices.map((inv) => (
              <button key={inv.id} onClick={() => sel(inv)} className={`w-full text-right px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 transition-colors ${selInv?.id === inv.id ? 'bg-riadah-50 dark:bg-riadah-900/20 border-r-4 border-r-blue-600' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'}`}>
                <div className="flex justify-between items-center"><span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{inv.invoice_number}</span><span className="text-xs text-gray-500" dir="ltr">{inv.due_date}</span></div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{inv.customer_name || inv.supplier_name}</p>
              </button>))}</div>}
        </div>
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {!selInv ? <div className="flex items-center justify-center py-20 text-gray-400"><Bell className="w-12 h-12 opacity-40 ml-3" /><p>اختر فاتورة</p></div>
            : reminders.length === 0 ? <div className="flex items-center justify-center py-20 text-gray-400"><p>لا توجد تذكيرات</p></div>
            : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">{remThs.map((h) => <th key={h} className={IP}>{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">{reminders.map((r, i) => (
                <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300">{r.invoice_number}</td>
                  <td className="px-4 py-3 text-sm">{rTypes[r.reminder_type] || r.reminder_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{sVia[r.sent_via] || r.sent_via}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{r.sent_date}</td>
                  <td className="px-4 py-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.status === 'sent' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'}`}>{r.status === 'sent' ? 'تم الإرسال' : 'قيد الانتظار'}</span></td>
                </tr>))}</tbody></table></div>}
        </div>
      </div>

      {/* Create Reminder Modal */}
      {showAdd && <Modal title="إنشاء تذكير دفع" onClose={() => setShowAdd(false)}><form onSubmit={handleCreate} className="p-5 space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الفاتورة</label>
          <select value={rf.invoice} onChange={(e) => setRf({ ...rf, invoice: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" required>
            <option value="">اختر فاتورة...</option>{invoices.map((i) => <option key={i.id} value={i.id}>{i.invoice_number} — {i.customer_name || i.supplier_name}</option>)}
          </select></div>
        <div className="grid grid-cols-2 gap-3">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع التذكير</label>
            <select value={rf.reminder_type} onChange={(e) => setRf({ ...rf, reminder_type: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
              {Object.entries(rTypes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">طريقة الإرسال</label>
            <select value={rf.sent_via} onChange={(e) => setRf({ ...rf, sent_via: e.target.value })} className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
              {Object.entries(sVia).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
        </div>
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={rLoading} className="flex-1 bg-riadah-500 hover:bg-riadah-600 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 text-sm">
            {rLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> جاري الإرسال...</> : <><Send className="w-4 h-4" /> إرسال التذكير</>}</button>
          <button type="button" onClick={() => setShowAdd(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">إلغاء</button>
        </div>
      </form></Modal>}
    </div>
  );
}

/* ===== SHARED MODAL ===== */
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
