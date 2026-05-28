/**
 * POS Management Page - إدارة نقاط البيع (الأسعار، الخصومات، البروموكود، الولاء، الطاولات)
 * Features: tabbed interface with tables + create modals for each section.
 */

import { useState, useEffect, useCallback } from 'react';
import { posAPI } from '../api';
import toast from 'react-hot-toast';
import {
  Settings, Plus, X, Edit3, Trash2, Search, Loader2, Save,
  AlertTriangle, Tag, Percent, Gift, Users, LayoutGrid, Check, XCircle,
} from 'lucide-react';

const Sp = () => (<svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>);
const ic = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none text-sm';

const TABS = [
  { id: 'prices', name: 'قوائم الأسعار', icon: Tag },
  { id: 'discounts', name: 'قواعد الخصم', icon: Percent },
  { id: 'promos', name: 'أكواد الخصم', icon: Gift },
  { id: 'loyalty', name: 'برامج الولاء', icon: Users },
  { id: 'tables', name: 'الطاولات', icon: LayoutGrid },
];

const DISCOUNT_TYPES = { percentage: 'نسبة مئوية', fixed_amount: 'مبلغ ثابت', bogo: 'اشترِ واحد واحصل على واحد' };
const PROMO_TYPES = { percentage: 'نسبة مئوية', fixed_amount: 'مبلغ ثابت' };
const TABLE_STATUS_CFG = {
  available: { label: 'متاحة', dot: 'bg-green-500' },
  occupied: { label: 'مشغولة', dot: 'bg-red-500' },
  reserved: { label: 'محجوزة', dot: 'bg-yellow-500' },
  cleaning: { label: 'تنظيف', dot: 'bg-blue-500' },
};

export default function POSManagementPage() {
  const [tab, setTab] = useState('prices');
  const [ld, setLd] = useState(false);
  const [sv, setSv] = useState(false);

  // Data for each tab
  const [priceLists, setPriceLists] = useState([]);
  const [discountRules, setDiscountRules] = useState([]);
  const [promoCodes, setPromoCodes] = useState([]);
  const [loyaltyPrograms, setLoyaltyPrograms] = useState([]);
  const [tables, setTables] = useState([]);

  // Modals
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Forms
  const [priceForm, setPriceForm] = useState({ name: '', is_default: false, valid_from: '', valid_until: '' });
  const [discountForm, setDiscountForm] = useState({ name: '', discount_type: 'percentage', discount_value: '', applies_to: 'all_products', min_purchase_amount: '', active: true });
  const [promoForm, setPromoForm] = useState({ code: '', discount_type: 'percentage', discount_value: '', max_uses: '', valid_from: '', valid_until: '' });
  const [loyaltyForm, setLoyaltyForm] = useState({ name: '', points_rate: 1, points_value: 0.01, min_redemption: 100 });
  const [tableForm, setTableForm] = useState({ table_number: '', capacity: 4, area: '', status: 'available' });

  // Fetch data for active tab
  useEffect(() => {
    const fetchData = async () => {
      setLd(true);
      try {
        if (tab === 'prices') setPriceLists((await posAPI.priceLists()).data.results || (await posAPI.priceLists()).data || []);
        if (tab === 'discounts') setDiscountRules((await posAPI.discountRules()).data.results || (await posAPI.discountRules()).data || []);
        if (tab === 'promos') setPromoCodes((await posAPI.promoCodes()).data.results || (await posAPI.promoCodes()).data || []);
        if (tab === 'loyalty') setLoyaltyPrograms((await posAPI.loyaltyPrograms()).data.results || (await posAPI.loyaltyPrograms()).data || []);
        if (tab === 'tables') setTables((await posAPI.tables()).data.results || (await posAPI.tables()).data || []);
      } catch { toast.error('خطأ في تحميل البيانات'); }
      finally { setLd(false); }
    };
    fetchData();
  }, [tab]);

  const getForm = () => {
    if (tab === 'prices') return [priceForm, setPriceForm];
    if (tab === 'discounts') return [discountForm, setDiscountForm];
    if (tab === 'promos') return [promoForm, setPromoForm];
    if (tab === 'loyalty') return [loyaltyForm, setLoyaltyForm];
    if (tab === 'tables') return [tableForm, setTableForm];
  };

  const getEmptyForm = () => {
    if (tab === 'prices') return { name: '', is_default: false, valid_from: '', valid_until: '' };
    if (tab === 'discounts') return { name: '', discount_type: 'percentage', discount_value: '', applies_to: 'all_products', min_purchase_amount: '', active: true };
    if (tab === 'promos') return { code: '', discount_type: 'percentage', discount_value: '', max_uses: '', valid_from: '', valid_until: '' };
    if (tab === 'loyalty') return { name: '', points_rate: 1, points_value: 0.01, min_redemption: 100 };
    if (tab === 'tables') return { table_number: '', capacity: 4, area: '', status: 'available' };
  };

  const getApiCreate = () => {
    if (tab === 'prices') return (data) => posAPI.createPriceList(data);
    if (tab === 'discounts') return (data) => posAPI.createDiscountRule(data);
    if (tab === 'promos') return (data) => posAPI.createPromoCode(data);
    if (tab === 'loyalty') return (data) => posAPI.createLoyaltyProgram(data);
    if (tab === 'tables') return (data) => posAPI.createTable(data);
  };

  const getApiUpdate = () => {
    if (tab === 'prices') return (id, data) => posAPI.updatePriceList(id, data);
    if (tab === 'discounts') return (id, data) => posAPI.updateDiscountRule(id, data);
    if (tab === 'promos') return (id, data) => posAPI.updatePromoCode(id, data);
    if (tab === 'loyalty') return (id, data) => posAPI.updateLoyaltyProgram(id, data);
    if (tab === 'tables') return (id, data) => posAPI.updateTable(id, data);
  };

  const getApiDelete = () => {
    if (tab === 'prices') return (id) => posAPI.deletePriceList(id);
    if (tab === 'discounts') return (id) => posAPI.deleteDiscountRule(id);
    if (tab === 'promos') return (id) => posAPI.deletePromoCode(id);
    if (tab === 'loyalty') return (id) => posAPI.deleteLoyaltyProgram(id);
    if (tab === 'tables') return () => {};
  };

  const [currentForm, setCurrentForm] = getForm();

  const openCreate = () => {
    setEditing(null);
    setCurrentForm(getEmptyForm());
    setShowModal(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    const empty = getEmptyForm();
    const filled = {};
    Object.keys(empty).forEach(k => { filled[k] = item[k] ?? empty[k]; });
    setCurrentForm(filled);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSv(true);
    try {
      const payload = { ...currentForm };
      if (payload.discount_value) payload.discount_value = +payload.discount_value;
      if (payload.max_uses) payload.max_uses = +payload.max_uses;
      if (payload.min_purchase_amount) payload.min_purchase_amount = +payload.min_purchase_amount;
      if (payload.points_rate) payload.points_rate = +payload.points_rate;
      if (payload.points_value) payload.points_value = +payload.points_value;
      if (payload.min_redemption) payload.min_redemption = +payload.min_redemption;
      if (payload.capacity) payload.capacity = +payload.capacity;
      if (payload.table_number) payload.table_number = +payload.table_number;
      if (editing) {
        await getApiUpdate()(editing.id, payload);
        toast.success('تم التحديث');
      } else {
        await getApiCreate()(payload);
        toast.success('تم الإنشاء');
      }
      setShowModal(false);
      // Refetch
      setLd(true);
      try {
        if (tab === 'prices') setPriceLists((await posAPI.priceLists()).data.results || []);
        if (tab === 'discounts') setDiscountRules((await posAPI.discountRules()).data.results || []);
        if (tab === 'promos') setPromoCodes((await posAPI.promoCodes()).data.results || []);
        if (tab === 'loyalty') setLoyaltyPrograms((await posAPI.loyaltyPrograms()).data.results || []);
        if (tab === 'tables') setTables((await posAPI.tables()).data.results || []);
      } catch (error) { console.error('Error:', error); }
      finally { setLd(false); }
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'خطأ');
    } finally { setSv(false); }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await getApiDelete()(deleteTarget.id);
      toast.success('تم الحذف');
      setDeleteTarget(null);
      setLd(true);
      try {
        if (tab === 'prices') setPriceLists((await posAPI.priceLists()).data.results || []);
        if (tab === 'discounts') setDiscountRules((await posAPI.discountRules()).data.results || []);
        if (tab === 'promos') setPromoCodes((await posAPI.promoCodes()).data.results || []);
        if (tab === 'loyalty') setLoyaltyPrograms((await posAPI.loyaltyPrograms()).data.results || []);
        if (tab === 'tables') setTables((await posAPI.tables()).data.results || []);
      } catch (error) { console.error('Error:', error); }
      finally { setLd(false); }
    } catch { toast.error('خطأ في الحذف'); }
  };

  const Modal = ({ title, children }) => showModal && (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
          <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"><X className="w-5 h-5" /></button>
        </div>
        {children}
      </div>
    </div>
  );

  const DeleteConfirm = () => deleteTarget && (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
        <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"><AlertTriangle className="w-7 h-7 text-red-600" /></div>
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">تأكيد الحذف</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">هذا الإجراء لا يمكن التراجع عنه</p>
        <div className="flex gap-3 mt-5">
          <button onClick={handleDelete} className="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors">حذف</button>
          <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button>
        </div>
      </div>
    </div>
  );

  const renderTable = () => {
    if (ld) return <div className="p-12 text-center text-gray-400 flex items-center justify-center gap-2"><Sp /> جاري التحميل...</div>;

    if (tab === 'prices') {
      return priceLists.length === 0 ? <div className="p-12 text-center text-gray-500">لا توجد قوائم أسعار</div> : (
        <table className="w-full text-sm"><thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700"><tr><th className="px-4 py-3 text-right">الاسم</th><th className="px-4 py-3 text-right">افتراضي</th><th className="px-4 py-3 text-right">صالح من</th><th className="px-4 py-3 text-right">صالح حتى</th><th className="px-4 py-3 text-right">إجراء</th></tr></thead>
        <tbody>{priceLists.map(p => (
          <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"><td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{p.name}</td><td className="px-4 py-3">{p.is_default ? <Check className="w-4 h-4 text-green-600" /> : <XCircle className="w-4 h-4 text-gray-400" />}</td><td className="px-4 py-3 text-gray-500 text-xs">{p.valid_from || '-'}</td><td className="px-4 py-3 text-gray-500 text-xs">{p.valid_until || '-'}</td><td className="px-4 py-3 flex gap-1"><button onClick={() => openEdit(p)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button><button onClick={() => setDeleteTarget(p)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button></td></tr>
        ))}</tbody></table>
      );
    }

    if (tab === 'discounts') {
      return discountRules.length === 0 ? <div className="p-12 text-center text-gray-500">لا توجد قواعد خصم</div> : (
        <table className="w-full text-sm"><thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700"><tr><th className="px-4 py-3 text-right">الاسم</th><th className="px-4 py-3 text-right">النوع</th><th className="px-4 py-3 text-right">القيمة</th><th className="px-4 py-3 text-right">تطبق على</th><th className="px-4 py-3 text-right">الحالة</th><th className="px-4 py-3 text-right">إجراء</th></tr></thead>
        <tbody>{discountRules.map(d => (
          <tr key={d.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"><td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{d.name}</td><td className="px-4 py-3 text-gray-600">{DISCOUNT_TYPES[d.discount_type] || d.discount_type}</td><td className="px-4 py-3 font-medium" dir="ltr">{d.discount_value}{d.discount_type === 'percentage' ? '%' : ''}</td><td className="px-4 py-3 text-gray-500 text-xs">{d.applies_to || '-'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs ${d.active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}>{d.active ? 'نشط' : 'غير نشط'}</span></td><td className="px-4 py-3 flex gap-1"><button onClick={() => openEdit(d)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button><button onClick={() => setDeleteTarget(d)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button></td></tr>
        ))}</tbody></table>
      );
    }

    if (tab === 'promos') {
      return promoCodes.length === 0 ? <div className="p-12 text-center text-gray-500">لا توجد أكواد خصم</div> : (
        <table className="w-full text-sm"><thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700"><tr><th className="px-4 py-3 text-right">الكود</th><th className="px-4 py-3 text-right">النوع</th><th className="px-4 py-3 text-right">القيمة</th><th className="px-4 py-3 text-right">الحد الأقصى</th><th className="px-4 py-3 text-right">الاستخدام</th><th className="px-4 py-3 text-right">إجراء</th></tr></thead>
        <tbody>{promoCodes.map(p => (
          <tr key={p.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"><td className="px-4 py-3 font-mono font-medium text-emerald-600 dark:text-emerald-400">{p.code}</td><td className="px-4 py-3 text-gray-600">{PROMO_TYPES[p.discount_type] || p.discount_type}</td><td className="px-4 py-3 font-medium" dir="ltr">{p.discount_value}{p.discount_type === 'percentage' ? '%' : ''}</td><td className="px-4 py-3" dir="ltr">{p.max_uses || '∞'}</td><td className="px-4 py-3" dir="ltr">{p.used_count || 0}/{p.max_uses || '∞'}</td><td className="px-4 py-3 flex gap-1"><button onClick={() => openEdit(p)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button><button onClick={() => setDeleteTarget(p)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button></td></tr>
        ))}</tbody></table>
      );
    }

    if (tab === 'loyalty') {
      return loyaltyPrograms.length === 0 ? <div className="p-12 text-center text-gray-500">لا توجد برامج ولاء</div> : (
        <table className="w-full text-sm"><thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700"><tr><th className="px-4 py-3 text-right">الاسم</th><th className="px-4 py-3 text-right">نقاط لكل ريال</th><th className="px-4 py-3 text-right">قيمة النقطة</th><th className="px-4 py-3 text-right">إجراء</th></tr></thead>
        <tbody>{loyaltyPrograms.map(l => (
          <tr key={l.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"><td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{l.name}</td><td className="px-4 py-3" dir="ltr">{l.points_rate}</td><td className="px-4 py-3" dir="ltr">{l.points_value}</td><td className="px-4 py-3 flex gap-1"><button onClick={() => openEdit(l)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button><button onClick={() => setDeleteTarget(l)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><Trash2 className="w-4 h-4" /></button></td></tr>
        ))}</tbody></table>
      );
    }

    if (tab === 'tables') {
      return tables.length === 0 ? <div className="p-12 text-center text-gray-500">لا توجد طاولات</div> : (
        <table className="w-full text-sm"><thead className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700"><tr><th className="px-4 py-3 text-right">الرقم</th><th className="px-4 py-3 text-right">السعة</th><th className="px-4 py-3 text-right">المنطقة</th><th className="px-4 py-3 text-right">الحالة</th><th className="px-4 py-3 text-right">إجراء</th></tr></thead>
        <tbody>{tables.map(t => (
          <tr key={t.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"><td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">#{t.table_number}</td><td className="px-4 py-3" dir="ltr">{t.capacity}</td><td className="px-4 py-3 text-gray-600">{t.area || '-'}</td><td className="px-4 py-3"><div className="flex items-center gap-2"><span className={`w-2.5 h-2.5 rounded-full ${TABLE_STATUS_CFG[t.status]?.dot || 'bg-gray-400'}`} /><span className="text-xs">{TABLE_STATUS_CFG[t.status]?.label || t.status}</span></div></td><td className="px-4 py-3"><button onClick={() => openEdit(t)} className="p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><Edit3 className="w-4 h-4" /></button></td></tr>
        ))}</tbody></table>
      );
    }
  };

  const renderModalForm = () => {
    if (tab === 'prices') {
      return (
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم القائمة *</label><input type="text" value={currentForm.name} onChange={e => setCurrentForm({ ...currentForm, name: e.target.value })} required className={ic} /></div>
          <div className="flex items-center gap-2"><input type="checkbox" checked={currentForm.is_default} onChange={e => setCurrentForm({ ...currentForm, is_default: e.target.checked })} className="rounded" /><label className="text-sm text-gray-700 dark:text-gray-300">قائمة افتراضية</label></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">صالح من</label><input type="date" value={currentForm.valid_from} onChange={e => setCurrentForm({ ...currentForm, valid_from: e.target.value })} className={ic} /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">صالح حتى</label><input type="date" value={currentForm.valid_until} onChange={e => setCurrentForm({ ...currentForm, valid_until: e.target.value })} className={ic} /></div>
          </div>
          <div className="flex gap-3 pt-2"><button type="submit" disabled={sv} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{sv ? <Sp /> : 'حفظ'}</button><button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button></div>
        </form>
      );
    }

    if (tab === 'discounts') {
      return (
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الاسم *</label><input type="text" value={currentForm.name} onChange={e => setCurrentForm({ ...currentForm, name: e.target.value })} required className={ic} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نوع الخصم</label><select value={currentForm.discount_type} onChange={e => setCurrentForm({ ...currentForm, discount_type: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>{Object.entries(DISCOUNT_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القيمة</label><input type="number" step="0.01" value={currentForm.discount_value} onChange={e => setCurrentForm({ ...currentForm, discount_value: e.target.value })} className={ic} dir="ltr" /></div>
          </div>
          <div className="flex items-center gap-2"><input type="checkbox" checked={currentForm.active} onChange={e => setCurrentForm({ ...currentForm, active: e.target.checked })} className="rounded" /><label className="text-sm text-gray-700 dark:text-gray-300">نشط</label></div>
          <div className="flex gap-3 pt-2"><button type="submit" disabled={sv} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{sv ? <Sp /> : 'حفظ'}</button><button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button></div>
        </form>
      );
    }

    if (tab === 'promos') {
      return (
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">كود الخصم *</label><input type="text" value={currentForm.code} onChange={e => setCurrentForm({ ...currentForm, code: e.target.value.toUpperCase() })} required className={ic} dir="ltr" placeholder="e.g. SUMMER2024" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع</label><select value={currentForm.discount_type} onChange={e => setCurrentForm({ ...currentForm, discount_type: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>{Object.entries(PROMO_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">القيمة</label><input type="number" step="0.01" value={currentForm.discount_value} onChange={e => setCurrentForm({ ...currentForm, discount_value: e.target.value })} className={ic} dir="ltr" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحد الأقصى للاستخدام</label><input type="number" min="0" value={currentForm.max_uses} onChange={e => setCurrentForm({ ...currentForm, max_uses: e.target.value })} className={ic} dir="ltr" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">صالح حتى</label><input type="date" value={currentForm.valid_until} onChange={e => setCurrentForm({ ...currentForm, valid_until: e.target.value })} className={ic} /></div>
          </div>
          <div className="flex gap-3 pt-2"><button type="submit" disabled={sv} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{sv ? <Sp /> : 'حفظ'}</button><button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button></div>
        </form>
      );
    }

    if (tab === 'loyalty') {
      return (
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم البرنامج *</label><input type="text" value={currentForm.name} onChange={e => setCurrentForm({ ...currentForm, name: e.target.value })} required className={ic} /></div>
          <div className="grid grid-cols-3 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">نقاط لكل 1 ريال</label><input type="number" step="0.1" value={currentForm.points_rate} onChange={e => setCurrentForm({ ...currentForm, points_rate: e.target.value })} className={ic} dir="ltr" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">قيمة النقطة (ريال)</label><input type="number" step="0.001" value={currentForm.points_value} onChange={e => setCurrentForm({ ...currentForm, points_value: e.target.value })} className={ic} dir="ltr" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">أقل استبدال</label><input type="number" min="0" value={currentForm.min_redemption} onChange={e => setCurrentForm({ ...currentForm, min_redemption: e.target.value })} className={ic} dir="ltr" /></div>
          </div>
          <div className="flex gap-3 pt-2"><button type="submit" disabled={sv} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{sv ? <Sp /> : 'حفظ'}</button><button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button></div>
        </form>
      );
    }

    if (tab === 'tables') {
      return (
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">رقم الطاولة *</label><input type="number" min="1" value={currentForm.table_number} onChange={e => setCurrentForm({ ...currentForm, table_number: e.target.value })} required className={ic} dir="ltr" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">السعة (أشخاص)</label><input type="number" min="1" value={currentForm.capacity} onChange={e => setCurrentForm({ ...currentForm, capacity: e.target.value })} className={ic} dir="ltr" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">المنطقة</label><input type="text" value={currentForm.area} onChange={e => setCurrentForm({ ...currentForm, area: e.target.value })} className={ic} placeholder="مثال: الداخل" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">الحالة</label><select value={currentForm.status} onChange={e => setCurrentForm({ ...currentForm, status: e.target.value })} className={`${ic} bg-white dark:bg-gray-700`}>{Object.entries(TABLE_STATUS_CFG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></div>
          </div>
          <div className="flex gap-3 pt-2"><button type="submit" disabled={sv} className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 font-medium">{sv ? <Sp /> : 'حفظ'}</button><button type="button" onClick={() => setShowModal(false)} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">إلغاء</button></div>
        </form>
      );
    }
  };

  const tabTitles = { prices: 'قائمة أسعار', discounts: 'قاعدة خصم', promos: 'كود خصم', loyalty: 'برنامج ولاء', tables: 'طاولة' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">إدارة نقاط البيع</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">الأسعار، الخصومات، البروموكود، الولاء، الطاولات</p>
          </div>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm shadow-sm">
          <Plus className="w-4 h-4" /> إضافة
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        {TABS.map(t => { const I = t.icon; return (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>
            <I className="w-4 h-4" />{t.name}
          </button>
        ); })}
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">{renderTable()}</div>
      </div>

      {/* Modal */}
      <Modal title={`${editing ? 'تعديل' : 'إنشاء'} ${tabTitles[tab]}`}>
        {renderModalForm()}
      </Modal>

      <DeleteConfirm />
    </div>
  );
}
