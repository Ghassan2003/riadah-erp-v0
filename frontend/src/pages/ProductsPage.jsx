/**
 * Products page - inventory management.
 * Features: product table, search, create/edit modal, soft delete, role-based UI.
 * Supports dark mode and i18n.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { productsAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import {
  Package, Plus, Search, Edit3, Trash2, RotateCcw,
  X, Save, Loader2, AlertTriangle, PackageSearch,
  ChevronLeft, ChevronRight, Filter, Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

// Empty form template
const emptyForm = {
  name: '',
  description: '',
  sku: '',
  quantity: 0,
  unit_price: '',
  reorder_level: 10,
};

export default function ProductsPage() {
  const { isWarehouse } = useAuth();
  const { t, locale } = useI18n();

  // Data state
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDeleted, setShowDeleted] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Export state
  const [exporting, setExporting] = useState(false);

  const numberLocale = locale === 'ar' ? 'ar-SA' : 'en-US';

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.products();
      downloadBlob(new Blob([response.data]), 'products.xlsx');
      toast.success(t('dataExported'));
    } catch (error) {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  // Fetch products from API
  const fetchProducts = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = {
        page,
        search: searchTerm || undefined,
        show_deleted: showDeleted || undefined,
      };
      const response = await productsAPI.list(params);
      const data = response.data;
      // Handle paginated response
      if (data.results) {
        setProducts(data.results);
        setTotalCount(data.count);
      } else {
        setProducts(Array.isArray(data) ? data : []);
        setTotalCount(data.length || 0);
      }
      // Update stats if present
      if (data.stats) {
        setStats(data.stats);
      }
      setCurrentPage(page);
    } catch (error) {
      toast.error(t('loadProductsFailed'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, showDeleted, t]);

  // Fetch stats separately (for sidebar cards)
  const fetchStats = async () => {
    try {
      const response = await productsAPI.getStats();
      setStats(response.data);
    } catch (error) {
      // Silent fail for stats
    }
  };

  useEffect(() => {
    fetchProducts(1);
    fetchStats();
  }, [fetchProducts]);

  // Search debounce
  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  // Form handling
  const openCreateModal = () => {
    setEditingProduct(null);
    setFormData(emptyForm);
    setFormErrors({});
    setShowModal(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      description: product.description || '',
      sku: product.sku,
      quantity: product.quantity,
      unit_price: product.unit_price,
      reorder_level: product.reorder_level,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingProduct(null);
    setFormData(emptyForm);
    setFormErrors({});
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.name.trim()) errors.name = t('productNameRequired');
    if (!formData.sku.trim()) errors.sku = t('skuRequired');
    if (formData.unit_price === '' || Number(formData.unit_price) <= 0)
      errors.unit_price = t('unitPriceMustBePositive');
    if (formData.quantity < 0) errors.quantity = t('quantityCannotBeNegative');
    if (formData.reorder_level < 0) errors.reorder_level = t('reorderLevelCannotBeNegative');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setFormLoading(true);
    try {
      const payload = {
        ...formData,
        unit_price: parseFloat(formData.unit_price),
        quantity: parseInt(formData.quantity, 10),
        reorder_level: parseInt(formData.reorder_level, 10),
      };

      if (editingProduct) {
        await productsAPI.update(editingProduct.id, payload);
        toast.success(t('productUpdatedSuccess'));
      } else {
        await productsAPI.create(payload);
        toast.success(t('productAddedSuccess'));
      }
      closeModal();
      fetchProducts(currentPage);
      fetchStats();
    } catch (error) {
      const data = error.response?.data;
      if (data) {
        // Handle field-specific errors from Django
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
        toast.error(t('operationFailedCheckData'));
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Delete handling (soft delete)
  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await productsAPI.softDelete(deleteConfirm.id);
      toast.success(t('productSoftDeleted'));
      setDeleteConfirm(null);
      fetchProducts(currentPage);
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.error || t('deleteProductFailed'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // Restore handling
  const handleRestore = async (product) => {
    try {
      await productsAPI.restore(product.id);
      toast.success(t('productRestored'));
      fetchProducts(currentPage);
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.error || t('restoreProductFailed'));
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageProducts')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageProductsDesc')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('exporting')}
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                {t('exportExcel')}
              </>
            )}
          </button>
          {isWarehouse && (
            <button
              onClick={openCreateModal}
              className="flex items-center gap-2 bg-riadah-500 hover:bg-riadah-600 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              {t('addNewProduct')}
            </button>
          )}
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalProducts')}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total_products}</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-riadah-50 dark:bg-riadah-900/20 flex items-center justify-center">
                <Package className="w-5 h-5 text-accent-500 dark:text-accent-400" />
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('lowStockProducts')}</p>
                <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{stats.low_stock_products}</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-orange-50 dark:bg-orange-900/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-orange-500 dark:text-orange-400" />
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('totalInventoryValue')}</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {Number(stats.total_inventory_value).toLocaleString(numberLocale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })} {t('sar')}
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-900/20 flex items-center justify-center">
                <PackageSearch className="w-5 h-5 text-green-500 dark:text-green-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder={t('searchByNameSku')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
          />
        </div>
        <label className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          <input
            type="checkbox"
            checked={showDeleted}
            onChange={(e) => {
              setShowDeleted(e.target.checked);
              setCurrentPage(1);
            }}
            className="rounded border-gray-300 dark:border-gray-600 text-accent-500 focus:ring-accent-500"
          />
          <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">{t('showDeleted')}</span>
        </label>
      </div>

      {/* Products table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <Package className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('noProducts')}</p>
            <p className="text-sm mt-1 text-gray-400 dark:text-gray-500">
              {searchTerm ? t('noSearchResults') : t('startAddingProducts')}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('product')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">SKU</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('quantity')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('unitPrice')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('totalValue')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('status')}</th>
                  {isWarehouse && (
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('actions')}</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {products.map((product) => (
                  <tr
                    key={product.id}
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${
                      !product.is_active ? 'bg-red-50/50 dark:bg-red-900/10 opacity-70' : ''
                    } ${product.is_low_stock && product.is_active ? 'bg-orange-50/30 dark:bg-orange-900/10' : ''}`}
                  >
                    {/* Product name */}
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100">{product.name}</p>
                        {product.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                            {product.description}
                          </p>
                        )}
                      </div>
                    </td>

                    {/* SKU */}
                    <td className="px-4 py-3">
                      <span className="font-mono text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
                        {product.sku}
                      </span>
                    </td>

                    {/* Quantity */}
                    <td className="px-4 py-3">
                      <span className={`font-semibold ${
                        product.is_low_stock && product.is_active ? 'text-orange-600 dark:text-orange-400' : 'text-gray-900 dark:text-gray-100'
                      }`}>
                        {product.quantity}
                      </span>
                      {product.is_low_stock && product.is_active && (
                        <span className="mr-1 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300">
                          {t('low')}
                        </span>
                      )}
                    </td>

                    {/* Unit price */}
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300" dir="ltr">
                      {Number(product.unit_price).toFixed(2)} {t('sar')}
                    </td>

                    {/* Total value */}
                    <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300" dir="ltr">
                      {Number(product.total_value).toLocaleString(numberLocale, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })} {t('sar')}
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        product.is_active
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                      }`}>
                        {product.is_active ? t('active') : t('deleted')}
                      </span>
                    </td>

                    {/* Actions */}
                    {isWarehouse && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {product.is_active ? (
                            <>
                              <button
                                onClick={() => openEditModal(product)}
                                className="p-1.5 text-accent-500 dark:text-accent-400 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 rounded-lg transition-colors"
                                title={t('edit')}
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(product)}
                                className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                title={t('delete')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleRestore(product)}
                              className="p-1.5 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                              title={t('restore')}
                            >
                              <RotateCcw className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    )}
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
                onClick={() => fetchProducts(currentPage - 1)}
                disabled={currentPage <= 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-500 dark:text-gray-400"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => fetchProducts(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-gray-500 dark:text-gray-400"
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
          <div className="fixed inset-0 bg-black/50" onClick={closeModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingProduct ? t('editProduct') : t('addNewProduct')}
              </h3>
              <button onClick={closeModal} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            {/* Modal body */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {/* Product name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('productName')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${
                    formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                  }`}
                  placeholder={t('productNamePlaceholder')}
                />
                {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('description')}</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none"
                  placeholder={t('descriptionPlaceholder')}
                />
              </div>

              {/* SKU */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('sku')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  dir="ltr"
                  className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-left ${
                    formErrors.sku ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                  }`}
                  placeholder={t('skuPlaceholder')}
                />
                {formErrors.sku && <p className="text-red-500 text-xs mt-1">{formErrors.sku}</p>}
              </div>

              <div className="grid grid-cols-3 gap-3">
                {/* Quantity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('quantity')}</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value, 10) || 0 })}
                    className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${
                      formErrors.quantity ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                    }`}
                    dir="ltr"
                  />
                  {formErrors.quantity && <p className="text-red-500 text-xs mt-1">{formErrors.quantity}</p>}
                </div>

                {/* Unit price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('unitPrice')} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.unit_price}
                    onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                    className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${
                      formErrors.unit_price ? 'border-red-400 bg-red-50 dark:bg-red-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white'
                    }`}
                    dir="ltr"
                    placeholder="0.00"
                  />
                  {formErrors.unit_price && <p className="text-red-500 text-xs mt-1">{formErrors.unit_price}</p>}
                </div>

                {/* Reorder level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('reorderLevel')}</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: parseInt(e.target.value, 10) || 0 })}
                    className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                    dir="ltr"
                  />
                </div>
              </div>

              {/* Modal footer */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-riadah-500 hover:bg-riadah-600 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {formLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</>
                  ) : (
                    <><Save className="w-4 h-4" /> {editingProduct ? t('updateProduct') : t('addProduct')}</>
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
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirmDelete')}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                {t('confirmDeleteMessage')}{' '}
                <span className="font-semibold text-gray-900 dark:text-gray-100">"{deleteConfirm.name}"</span>?
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                {t('softDeleteNote')}
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteLoading}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {deleteLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</>
                  ) : (
                    <><Trash2 className="w-4 h-4" /> {t('deleteProduct')}</>
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
