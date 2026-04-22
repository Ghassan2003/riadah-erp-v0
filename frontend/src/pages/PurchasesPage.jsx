/**
 * Purchases page - suppliers and purchase orders management.
 * Two tabs: Suppliers and Purchase Orders.
 * Supports dark mode and i18n.
 */

import { useState, useEffect, useCallback } from 'react';
import { suppliersAPI, purchaseOrdersAPI, productsAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import { useI18n } from '../i18n/I18nContext';
import {
  Truck, Plus, Search, Edit3, Trash2, RotateCcw,
  X, Save, Loader2, AlertTriangle, Filter,
  ChevronLeft, ChevronRight, Package, ShoppingCart,
  Eye, Users, Building2, Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

/* eslint-disable react/prop-types */

export default function PurchasesPage() {
  const { t, locale } = useI18n();

  const STATUS_CONFIG = {
    draft:       { label: t('draft'),      color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
    pending:     { label: t('pending'),     color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
    approved:    { label: t('approved'),    color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300' },
    received:    { label: t('received'),    color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
    cancelled:   { label: t('cancelled'),   color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' },
  };

  const STATUS_TRANSITIONS = {
    draft:     ['pending', 'cancelled'],
    pending:   ['approved', 'cancelled'],
    approved:  ['received', 'cancelled'],
    received:  [],
    cancelled: [],
  };

  const emptySupplierForm = {
    name: '',
    email: '',
    phone: '',
    address: '',
    balance: 0,
  };

  const emptyOrderForm = {
    supplier: '',
    notes: '',
    items: [],
  };

  const numLocale = locale === 'ar' ? 'ar-SA' : 'en-US';

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('managePurchases')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('managePurchasesDesc')}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('suppliers')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'suppliers'
              ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <Users className="w-4 h-4" />
          {t('suppliers')}
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'orders'
              ? 'bg-riadah-500 dark:bg-riadah-700 text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <ShoppingCart className="w-4 h-4" />
          {t('purchaseOrders')}
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'suppliers' ? <SuppliersTab STATUS_CONFIG={STATUS_CONFIG} numLocale={numLocale} /> : <PurchaseOrdersTab STATUS_CONFIG={STATUS_CONFIG} STATUS_TRANSITIONS={STATUS_TRANSITIONS} numLocale={numLocale} />}
    </div>
  );
}

/* ============================================================
   SUPPLIERS TAB
   ============================================================ */
function SuppliersTab({ STATUS_CONFIG, numLocale }) {
  const { t, locale } = useI18n();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDeleted, setShowDeleted] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', address: '', balance: 0 });
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Export state
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.suppliers();
      downloadBlob(new Blob([response.data]), 'suppliers.xlsx');
      toast.success(t('dataExported'));
    } catch (error) {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  const fetchSuppliers = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = {
        page,
        search: searchTerm || undefined,
        show_deleted: showDeleted || undefined,
      };
      const response = await suppliersAPI.list(params);
      const data = response.data;
      if (data.results) {
        setSuppliers(data.results);
        setTotalCount(data.count);
      } else {
        setSuppliers(Array.isArray(data) ? data : []);
        setTotalCount(data.length || 0);
      }
      setCurrentPage(page);
    } catch {
      toast.error(t('failedLoadingSuppliers'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, showDeleted, t]);

  useEffect(() => { fetchSuppliers(1); }, [fetchSuppliers]);

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const openCreateModal = () => {
    setEditingSupplier(null);
    setFormData({ name: '', email: '', phone: '', address: '', balance: 0 });
    setFormErrors({});
    setShowModal(true);
  };

  const openEditModal = (supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      email: supplier.email || '',
      phone: supplier.phone || '',
      address: supplier.address || '',
      balance: supplier.balance || 0,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingSupplier(null);
    setFormData({ name: '', email: '', phone: '', address: '', balance: 0 });
    setFormErrors({});
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.name.trim()) errors.name = t('supplierNameRequired');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setFormLoading(true);
    try {
      const payload = { ...formData };
      if (editingSupplier) {
        await suppliersAPI.update(editingSupplier.id, payload);
        toast.success(t('supplierUpdated'));
      } else {
        await suppliersAPI.create(payload);
        toast.success(t('supplierCreated'));
      }
      closeModal();
      fetchSuppliers(currentPage);
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
          toast.error(data.message || data.error || t('operationFailed'));
        }
      } else {
        toast.error(t('operationFailed'));
      }
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await suppliersAPI.softDelete(deleteConfirm.id);
      toast.success(t('supplierDeletedSoft'));
      setDeleteConfirm(null);
      fetchSuppliers(currentPage);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedDeletingSupplier'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleRestore = async (supplier) => {
    try {
      await suppliersAPI.restore(supplier.id);
      toast.success(t('supplierRestored'));
      fetchSuppliers(currentPage);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedRestoringSupplier'));
    }
  };

  const formatAmount = (val) => Number(val || 0).toLocaleString(numLocale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-4">
      {/* Header + button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-gray-500 dark:text-gray-400">{t('manageSuppliersDesc')}</p>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 dark:bg-green-700 hover:bg-green-700 dark:hover:bg-green-800 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('exporting')}...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                {t('exportExcel')}
              </>
            )}
          </button>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            {t('addNewPurchase')}
          </button>
        </div>
      </div>

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder={t('searchPurchases')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
          />
        </div>
        <label className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          <input
            type="checkbox"
            checked={showDeleted}
            onChange={(e) => { setShowDeleted(e.target.checked); setCurrentPage(1); }}
            className="rounded border-gray-300 text-accent-500 focus:ring-accent-500"
          />
          <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">{t('showDeleted')}</span>
        </label>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : suppliers.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium">{t('noPurchases')}</p>
            <p className="text-sm mt-1">{searchTerm ? t('noResults') : t('addFirstItem')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('name')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('supplierEmail')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('supplierPhone')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('total')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('status')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {suppliers.map((supplier) => (
                  <tr
                    key={supplier.id}
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${!supplier.is_active ? 'bg-red-50/50 dark:bg-red-900/10 opacity-70' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100">{supplier.name}</p>
                        {supplier.address && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">{supplier.address}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{supplier.email || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{supplier.phone || '-'}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                      {formatAmount(supplier.balance)} {t('currency')}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        supplier.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {supplier.is_active ? t('active') : t('deleted')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {supplier.is_active ? (
                          <>
                            <button
                              onClick={() => openEditModal(supplier)}
                              className="p-1.5 text-accent-500 hover:bg-riadah-50 dark:text-accent-400 dark:hover:bg-riadah-900/20 rounded-lg transition-colors"
                              title={t('edit')}
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(supplier)}
                              className="p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              title={t('delete')}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleRestore(supplier)}
                            className="p-1.5 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                            title={t('restore')}
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
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
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('showing')} {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} {t('of')} {totalCount}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => fetchSuppliers(currentPage - 1)}
                disabled={currentPage <= 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => fetchSuppliers(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={closeModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingSupplier ? t('editSupplier') : t('addSupplier')}
              </h3>
              <button onClick={closeModal} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('supplierName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 ${
                    formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/20' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder={t('supplierNamePlaceholder')}
                />
                {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('supplierEmail')}</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    placeholder="email@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('supplierPhone')}</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    placeholder="+9665xxxxxxxx"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('address')}</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
                  placeholder={t('addressPlaceholder')}
                />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {formLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</>
                  ) : (
                    <><Save className="w-4 h-4" /> {editingSupplier ? t('updateSupplier') : t('addSupplier')}</>
                  )}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirm')}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                {t('confirmDeleteSupplier')} <span className="font-semibold text-gray-900 dark:text-gray-100"> "{deleteConfirm.name}"</span>?
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                {t('softDeleteNote')}
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteLoading}
                  className="flex-1 bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {deleteLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</>
                  ) : (
                    <><Trash2 className="w-4 h-4" /> {t('deleteSupplier')}</>
                  )}
                </button>
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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

/* ============================================================
   PURCHASE ORDERS TAB
   ============================================================ */
function PurchaseOrdersTab({ STATUS_CONFIG, STATUS_TRANSITIONS, numLocale }) {
  const { t } = useI18n();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;
  const [actionLoading, setActionLoading] = useState(null);

  // Create order modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierSearch, setSupplierSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [orderItems, setOrderItems] = useState([]);
  const [orderNotes, setOrderNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Export state
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.purchaseOrders();
      downloadBlob(new Blob([response.data]), 'purchase-orders.xlsx');
      toast.success(t('dataExported'));
    } catch (error) {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  const fetchOrders = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = {
        page,
        search: searchTerm || undefined,
        status: statusFilter || undefined,
      };
      const response = await purchaseOrdersAPI.list(params);
      const data = response.data;
      setOrders(data.results || (Array.isArray(data) ? data : []));
      setTotalCount(data.count || data.length || 0);
      setCurrentPage(page);
    } catch {
      toast.error(t('failedLoadingOrders'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter, t]);

  useEffect(() => { fetchOrders(1); }, [fetchOrders]);

  // Fetch suppliers for dropdown
  useEffect(() => {
    const fetchSuppliersList = async () => {
      try {
        const response = await suppliersAPI.list({ page_size: 100 });
        setSuppliers(response.data.results || response.data);
      } catch { /* silent */ }
    };
    fetchSuppliersList();
  }, []);

  // Fetch products for modal
  useEffect(() => {
    const fetchProductsList = async () => {
      try {
        const response = await productsAPI.list({ page_size: 200 });
        setProducts(response.data.results || response.data);
      } catch { /* silent */ }
    };
    if (showCreateModal) fetchProductsList();
  }, [showCreateModal]);

  const filteredSuppliers = suppliers.filter((s) =>
    s.is_active && (s.name.includes(supplierSearch) || (s.email || '').includes(supplierSearch))
  );

  const filteredProducts = products.filter((p) =>
    p.is_active && (p.name.includes(productSearch) || (p.sku || '').includes(productSearch))
  );

  const handleChangeStatus = async (order, newStatus) => {
    setActionLoading(order.id);
    try {
      await purchaseOrdersAPI.changeStatus(order.id, newStatus);
      toast.success(`${t('statusChangedTo')} "${STATUS_CONFIG[newStatus].label}"`);
      fetchOrders(currentPage);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedChangingStatus'));
    } finally {
      setActionLoading(null);
    }
  };

  const addProductToOrder = (product) => {
    const existing = orderItems.find((item) => item.product_id === product.id);
    if (existing) {
      setOrderItems(orderItems.map((item) =>
        item.product_id === product.id ? { ...item, quantity: item.quantity + 1 } : item
      ));
    } else {
      setOrderItems([...orderItems, {
        product_id: product.id,
        product_name: product.name,
        product_sku: product.sku,
        unit_price: product.unit_price,
        quantity: 1,
      }]);
    }
  };

  const updateItemQuantity = (productId, newQty) => {
    if (newQty < 1) return;
    setOrderItems(orderItems.map((item) =>
      item.product_id === productId ? { ...item, quantity: newQty } : item
    ));
  };

  const removeItem = (productId) => {
    setOrderItems(orderItems.filter((item) => item.product_id !== productId));
  };

  const subtotal = orderItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);

  const handleSubmitOrder = async () => {
    if (!selectedSupplier) {
      toast.error(t('selectSupplierRequired'));
      return;
    }
    if (orderItems.length === 0) {
      toast.error(t('addAtLeastOneProduct'));
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        supplier: selectedSupplier,
        notes: orderNotes,
        items: orderItems.map((item) => ({
          product: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
      };
      await purchaseOrdersAPI.create(payload);
      toast.success(t('purchaseCreated'));
      setShowCreateModal(false);
      resetOrderForm();
      fetchOrders(1);
    } catch (error) {
      const msg = error.response?.data?.error || error.response?.data?.detail || t('failedCreatingOrder');
      toast.error(typeof msg === 'string' ? msg : t('failedCreatingOrder'));
    } finally {
      setSubmitting(false);
    }
  };

  const resetOrderForm = () => {
    setSelectedSupplier(null);
    setOrderItems([]);
    setOrderNotes('');
    setSupplierSearch('');
    setProductSearch('');
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-4">
      {/* Header + button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-gray-500 dark:text-gray-400">{t('manageOrdersDesc')}</p>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 dark:bg-green-700 hover:bg-green-700 dark:hover:bg-green-800 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('exporting')}...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                {t('exportExcel')}
              </>
            )}
          </button>
          <button
            onClick={() => { setShowCreateModal(true); resetOrderForm(); }}
            className="flex items-center gap-2 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            {t('addNewPurchase')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            placeholder={t('searchPurchases')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
          />
        </div>
        <div className="relative">
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            className="appearance-none pr-9 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
          >
            <option value="">{t('allStatuses')}</option>
            {Object.entries(STATUS_CONFIG).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Orders table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <Truck className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium">{t('noPurchases')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('purchaseOrderNumber')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('supplierName')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('status')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('date')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('total')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {orders.map((order) => {
                  const statusCfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.draft;
                  const transitions = STATUS_TRANSITIONS[order.status] || [];
                  return (
                    <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 px-2 py-1 rounded">
                          {order.order_number}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{order.supplier_name}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.color}`}>
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{order.order_date}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">
                        {Number(order.total_amount || 0).toLocaleString(numLocale, { minimumFractionDigits: 2 })} {t('currency')}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1 flex-wrap">
                          <button
                            className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            title={t('view')}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {transitions.map((newStatus) => (
                            <button
                              key={newStatus}
                              onClick={() => handleChangeStatus(order, newStatus)}
                              disabled={actionLoading === order.id}
                              className={`p-1.5 rounded-lg transition-colors text-xs font-medium px-2 ${
                                newStatus === 'cancelled'
                                  ? 'text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20'
                                  : 'text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20'
                              }`}
                              title={STATUS_CONFIG[newStatus].label}
                            >
                              {actionLoading === order.id
                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                : STATUS_CONFIG[newStatus].label}
                            </button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('showing')} {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} {t('of')} {totalCount}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => fetchOrders(currentPage - 1)}
                disabled={currentPage <= 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => fetchOrders(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => { setShowCreateModal(false); resetOrderForm(); }} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('addNewPurchase')}</h3>
              <button onClick={() => { setShowCreateModal(false); resetOrderForm(); }} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            <div className="p-5 space-y-5">
              {/* Supplier selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('supplierName')} <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <input
                    type="text"
                    value={supplierSearch}
                    onChange={(e) => setSupplierSearch(e.target.value)}
                    placeholder={t('searchSupplier')}
                    className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
                {selectedSupplier && (
                  <div className="mt-2 flex items-center justify-between bg-riadah-50 dark:bg-riadah-900/20 border border-riadah-200 dark:border-riadah-800 rounded-lg px-4 py-2">
                    <span className="font-medium text-riadah-800 dark:text-accent-300">
                      {suppliers.find(s => s.id === selectedSupplier)?.name || t('supplierSelected')}
                    </span>
                    <button onClick={() => setSelectedSupplier(null)} className="text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 text-xs">{t('change')}</button>
                  </div>
                )}
                {!selectedSupplier && (
                  <div className="mt-2 max-h-32 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                    {filteredSuppliers.map((supplier) => (
                      <button
                        key={supplier.id}
                        onClick={() => setSelectedSupplier(supplier.id)}
                        className="w-full text-right px-4 py-2 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 border-b border-gray-100 dark:border-gray-700 last:border-0 transition-colors"
                      >
                        <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{supplier.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{supplier.email || supplier.phone || '-'}</p>
                      </button>
                    ))}
                    {filteredSuppliers.length === 0 && <p className="text-center text-gray-400 dark:text-gray-500 py-3 text-sm">{t('noPurchases')}</p>}
                  </div>
                )}
              </div>

              {/* Product search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('addProducts')}</label>
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <input
                    type="text"
                    value={productSearch}
                    onChange={(e) => setProductSearch(e.target.value)}
                    placeholder={t('searchProduct')}
                    className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                <div className="mt-2 max-h-40 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                  {filteredProducts.map((product) => {
                    const inOrder = orderItems.find(i => i.product_id === product.id);
                    return (
                      <div key={product.id} className="flex items-center justify-between px-4 py-2 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{product.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">{product.sku}</span>
                            {' '}{Number(product.unit_price).toFixed(2)} {t('currency')}
                          </p>
                        </div>
                        <button
                          onClick={() => addProductToOrder(product)}
                          className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30"
                        >
                          <Plus className="w-3 h-3" />
                          {inOrder ? t('increase') : t('add')}
                        </button>
                      </div>
                    );
                  })}
                  {filteredProducts.length === 0 && <p className="text-center text-gray-400 dark:text-gray-500 py-3 text-sm">{t('noProducts')}</p>}
                </div>
              </div>

              {/* Order items */}
              {orderItems.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('orderItems')} ({orderItems.length})
                  </label>
                  <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 dark:bg-gray-800/70">
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('product')}</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('price')}</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('quantity')}</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('total')}</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {orderItems.map((item) => (
                          <tr key={item.product_id}>
                            <td className="px-3 py-2 font-medium text-gray-900 dark:text-gray-100">{item.product_name}</td>
                            <td className="px-3 py-2 text-gray-600 dark:text-gray-300" dir="ltr">{Number(item.unit_price).toFixed(2)}</td>
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => updateItemQuantity(item.product_id, item.quantity - 1)}
                                  disabled={item.quantity <= 1}
                                  className="w-6 h-6 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 flex items-center justify-center text-xs"
                                >-</button>
                                <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                                <button
                                  onClick={() => updateItemQuantity(item.product_id, item.quantity + 1)}
                                  className="w-6 h-6 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-center text-xs"
                                >+</button>
                              </div>
                            </td>
                            <td className="px-3 py-2 font-semibold text-gray-900 dark:text-gray-100" dir="ltr">
                              {(item.quantity * item.unit_price).toLocaleString(numLocale, { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-3 py-2">
                              <button onClick={() => removeItem(item.product_id)} className="p-1 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <span className="text-base font-bold text-accent-500 dark:text-accent-400">
                      {t('total')}: <span dir="ltr">{subtotal.toLocaleString(numLocale, { minimumFractionDigits: 2 })}</span> {t('currency')}
                    </span>
                  </div>
                </div>
              )}

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('notes')}</label>
                <textarea
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none text-sm"
                  placeholder={t('additionalNotes')}
                />
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleSubmitOrder}
                  disabled={submitting}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {submitting ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('creating')}...</>
                  ) : (
                    <><ShoppingCart className="w-4 h-4" /> {t('addNewPurchase')}</>
                  )}
                </button>
                <button
                  onClick={() => { setShowCreateModal(false); resetOrderForm(); }}
                  className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
