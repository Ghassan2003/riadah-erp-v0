/**
 * Branches page - manages company branches for multi-currency/branch setup.
 * Allows viewing, creating, and editing branches.
 * Supports dark mode and i18n (RTL Arabic/English).
 */

import { useState, useEffect, useCallback } from 'react';
import { multiCurrencyAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Search, Plus, Edit2, X, Building2, Star, MapPin, User,
} from 'lucide-react';

export default function BranchesPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  /* ── state ── */
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [saving, setSaving] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const [form, setForm] = useState({
    code: '',
    name: '',
    name_en: '',
    city: '',
    manager_name: '',
    currency: '',
    is_hq: false,
    address: '',
    phone: '',
  });

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchBranches = useCallback(async () => {
    setLoading(true);
    try {
      const res = await multiCurrencyAPI.getBranches({ search });
      setBranches(res.data.results || res.data);
    } catch {
      toast.error('خطأ في تحميل الفروع');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchBranches();
  }, [fetchBranches]);

  // ──────────────────────── Create / Edit ────────────────────────

  const openCreate = () => {
    setEditingBranch(null);
    setForm({
      code: '', name: '', name_en: '', city: '', manager_name: '',
      currency: '', is_hq: false, address: '', phone: '',
    });
    setShowModal(true);
  };

  const openEdit = (branch) => {
    setEditingBranch(branch);
    setForm({
      code: branch.code || '',
      name: branch.name || '',
      name_en: branch.name_en || '',
      city: branch.city || '',
      manager_name: branch.manager_name || '',
      currency: branch.currency || '',
      is_hq: branch.is_hq || false,
      address: branch.address || '',
      phone: branch.phone || '',
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingBranch) {
        await multiCurrencyAPI.updateBranch(editingBranch.id, form);
        toast.success('تم تحديث الفرع بنجاح');
      } else {
        await multiCurrencyAPI.createBranch(form);
        toast.success('تم إنشاء الفرع بنجاح');
      }
      setShowModal(false);
      fetchBranches();
    } catch (err) {
      const msg =
        err.response?.data?.code?.[0] ||
        err.response?.data?.error ||
        'خطأ في حفظ الفرع';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // ──────────────────────── Delete ────────────────────────

  const handleDelete = async () => {
    if (!confirmAction?.id) return;
    try {
      await multiCurrencyAPI.deleteBranch(confirmAction.id);
      toast.success('تم حذف الفرع بنجاح');
      fetchBranches();
    } catch {
      toast.error('خطأ في حذف الفرع');
    } finally {
      setConfirmAction(null);
    }
  };

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            الفروع
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            إدارة فروع الشركة والعملات
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5" />
            إضافة فرع
          </button>
        )}
      </div>

      {/* ── Search ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="البحث في الفروع..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
          />
        </div>
      </div>

      {/* ── Branches Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full bg-white dark:bg-gray-800 rounded-xl p-12 text-center text-gray-400 dark:text-gray-500 shadow-sm border border-gray-100 dark:border-gray-700">
            جاري التحميل...
          </div>
        ) : branches.length === 0 ? (
          <div className="col-span-full bg-white dark:bg-gray-800 rounded-xl p-12 text-center shadow-sm border border-gray-100 dark:border-gray-700">
            <Building2 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">لا توجد فروع</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">أضف فرع جديد للبدء</p>
          </div>
        ) : (
          branches.map((branch) => (
            <div
              key={branch.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
            >
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 bg-riadah-50 dark:bg-riadah-900/30 rounded-xl flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-riadah-600 dark:text-riadah-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 dark:text-gray-100">
                      {branch.name}
                    </h3>
                    <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                      {branch.code}
                    </span>
                  </div>
                </div>
                {branch.is_hq && (
                  <span className="flex items-center gap-1 px-2.5 py-1 bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400 rounded-full text-xs font-medium">
                    <Star className="w-3 h-3" />
                    المقر الرئيسي
                  </span>
                )}
              </div>

              {/* Card Details */}
              <div className="space-y-2 text-sm">
                {branch.city && (
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span>{branch.city}</span>
                  </div>
                )}
                {branch.manager_name && (
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <User className="w-4 h-4 text-gray-400" />
                    <span>{branch.manager_name}</span>
                  </div>
                )}
                {branch.currency && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">العملة:</span>
                    <span className="px-2 py-0.5 bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-riadah-400 rounded text-xs font-medium">
                      {branch.currency}
                    </span>
                  </div>
                )}
              </div>

              {/* Card Actions */}
              {isAdmin && (
                <div className="flex items-center gap-1 mt-4 pt-4 border-t dark:border-gray-700">
                  <button
                    onClick={() => openEdit(branch)}
                    className="flex items-center gap-1.5 text-sm text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 px-2 py-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    تعديل
                  </button>
                  {!branch.is_hq && (
                    <button
                      onClick={() => setConfirmAction({ id: branch.id, name: branch.name })}
                      className="flex items-center gap-1.5 text-sm text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 px-2 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors mr-auto"
                    >
                      حذف
                    </button>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Create / Edit Branch Modal
         ═══════════════════════════════════════════════════════════ */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingBranch ? 'تعديل الفرع' : 'إضافة فرع جديد'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    رمز الفرع *
                  </label>
                  <input
                    type="text"
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value })}
                    placeholder="مثال: BR-001"
                    disabled={!!editingBranch}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none disabled:bg-gray-50 dark:disabled:bg-gray-700 disabled:text-gray-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    العملة *
                  </label>
                  <input
                    type="text"
                    value={form.currency}
                    onChange={(e) => setForm({ ...form, currency: e.target.value })}
                    placeholder="مثال: SAR, USD"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  اسم الفرع (عربي) *
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="اسم الفرع بالعربية"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  اسم الفرع (إنجليزي)
                </label>
                <input
                  type="text"
                  value={form.name_en}
                  onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                  placeholder="Branch name in English"
                  dir="ltr"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    المدينة
                  </label>
                  <input
                    type="text"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    placeholder="المدينة"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    المدير المسؤول
                  </label>
                  <input
                    type="text"
                    value={form.manager_name}
                    onChange={(e) => setForm({ ...form, manager_name: e.target.value })}
                    placeholder="اسم المدير"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  العنوان
                </label>
                <textarea
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  placeholder="عنوان الفرع"
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_hq"
                  checked={form.is_hq}
                  onChange={(e) => setForm({ ...form, is_hq: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-riadah-600 focus:ring-riadah-500"
                />
                <label htmlFor="is_hq" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  مقر رئيسي
                </label>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? 'جاري الحفظ...' : editingBranch ? 'حفظ التعديلات' : 'إنشاء'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
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
          Delete Confirmation Dialog
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
              <div className="mx-auto w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
                <Building2 className="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                تأكيد الحذف
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                هل أنت متأكد من حذف الفرع{' '}
                <span className="font-medium text-gray-700 dark:text-gray-300">{confirmAction.name}</span>؟
              </p>
              <p className="text-xs text-red-500 dark:text-red-400 mt-2">
                هذا الإجراء لا يمكن التراجع عنه
              </p>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setConfirmAction(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
                <button
                  onClick={handleDelete}
                  className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
                >
                  حذف
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
