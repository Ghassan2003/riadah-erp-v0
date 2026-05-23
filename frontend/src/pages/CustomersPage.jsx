/**
 * Customers management page.
 * CRUD operations for customers with search functionality.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { customersAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import {
  Users, Plus, Search, Edit3, Trash2, X, Save,
  Loader2, Phone, Mail, MapPin, Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

const emptyForm = { name: '', email: '', phone: '', address: '' };

export default function CustomersPage() {
  const { isSales } = useAuth();
  const { t, locale } = useI18n();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState({});
  const [formLoading, setFormLoading] = useState(false);

  // Delete state
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Export state
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.customers();
      downloadBlob(new Blob([response.data]), 'customers.xlsx');
      toast.success(t('dataExported'));
    } catch (error) {
      toast.error(t('exportError'));
    } finally {
      setExporting(false);
    }
  };

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { search: searchTerm || undefined };
      const response = await customersAPI.list(params);
      const data = response.data;
      setCustomers(data.results || (Array.isArray(data) ? data : []));
    } catch {
      toast.error(t('failedLoadCustomers'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => { fetchCustomers(); }, [fetchCustomers]);

  const openCreateModal = () => {
    setEditingCustomer(null);
    setFormData(emptyForm);
    setFormErrors({});
    setShowModal(true);
  };

  const openEditModal = (customer) => {
    setEditingCustomer(customer);
    setFormData({
      name: customer.name,
      email: customer.email || '',
      phone: customer.phone || '',
      address: customer.address || '',
    });
    setFormErrors({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingCustomer(null);
    setFormData(emptyForm);
    setFormErrors({});
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.name.trim()) errors.name = t('customerNameRequired');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setFormLoading(true);
    try {
      if (editingCustomer) {
        await customersAPI.update(editingCustomer.id, formData);
        toast.success(t('customerUpdated'));
      } else {
        await customersAPI.create(formData);
        toast.success(t('customerCreated'));
      }
      closeModal();
      fetchCustomers();
    } catch (error) {
      const data = error.response?.data;
      if (data) {
        const fieldErrors = {};
        Object.keys(data).forEach((key) => {
          if (key !== 'message' && key !== 'error') {
            fieldErrors[key] = Array.isArray(data[key]) ? data[key][0] : data[key];
          }
        });
        if (Object.keys(fieldErrors).length > 0) setFormErrors(fieldErrors);
        else toast.error(data.message || data.detail || t('operationFailed'));
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
      await customersAPI.softDelete(deleteConfirm.id);
      toast.success(t('customerDeleted'));
      setDeleteConfirm(null);
      fetchCustomers();
    } catch (error) {
      toast.error(t('failedDeleteCustomer'));
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageCustomers')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('viewManageCustomers')}</p>
        </div>
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
          {isSales && (
            <button onClick={openCreateModal} className="flex items-center gap-2 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm">
              <Plus className="w-4 h-4" />
              {t('addNewCustomer')}
            </button>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
        <input
          type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={t('searchCustomers')}
          className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400"
        />
      </div>

      {/* Customers table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : customers.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <Users className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('noCustomers')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('customer')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('contact')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('address')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('orders')}</th>
                  {isSales && <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('actions')}</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{customer.name}</p>
                      {customer.email && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5" dir="ltr">
                          <Mail className="w-3 h-3" /> {customer.email}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {customer.phone && (
                        <p className="text-sm text-gray-600 dark:text-gray-300 flex items-center gap-1" dir="ltr">
                          <Phone className="w-3.5 h-3.5" /> {customer.phone}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-gray-600 dark:text-gray-300 max-w-[200px] truncate">
                        {customer.address || '-'}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-riadah-50 dark:bg-riadah-900/30 text-riadah-700 dark:text-accent-300">
                        {customer.orders_count} {t('orders')}
                      </span>
                    </td>
                    {isSales && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button onClick={() => openEditModal(customer)} className="p-1.5 text-accent-500 dark:text-accent-400 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 rounded-lg transition-colors" title={t('edit')}>
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button onClick={() => setDeleteConfirm(customer)} className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title={t('delete')}>
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={closeModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingCustomer ? t('editCustomer') : t('addNewCustomer')}
              </h3>
              <button onClick={closeModal} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><X className="w-5 h-5 text-gray-500 dark:text-gray-400" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('customerName')} <span className="text-red-500">*</span>
                </label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 ${formErrors.name ? 'border-red-400 bg-red-50 dark:bg-red-900/20' : 'border-gray-300 dark:border-gray-600'} dark:bg-gray-700 dark:text-white dark:placeholder-gray-400`}
                  placeholder={t('customerNamePlaceholder')}
                />
                {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('email')}</label>
                <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400" dir="ltr"
                  placeholder="email@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('phone')}</label>
                <input type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400" dir="ltr"
                  placeholder="05XXXXXXXX"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('address')}</label>
                <textarea value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows={2} className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
                  placeholder={t('fullAddress')}
                />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button type="submit" disabled={formLoading}
                  className="flex-1 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
                  {formLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('saving')}...</> : <><Save className="w-4 h-4" /> {editingCustomer ? t('update') : t('add')}</>}
                </button>
                <button type="button" onClick={closeModal} className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">{t('cancel')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <Trash2 className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirmDelete')}</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">{t('confirmDeleteCustomer')} "<span className="font-semibold text-gray-900 dark:text-gray-100">{deleteConfirm.name}</span>"?</p>
            <div className="flex items-center gap-3">
              <button onClick={handleDelete} disabled={deleteLoading}
                className="flex-1 bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
                {deleteLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</> : t('delete')}
              </button>
              <button onClick={() => setDeleteConfirm(null)} className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">{t('cancel')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
