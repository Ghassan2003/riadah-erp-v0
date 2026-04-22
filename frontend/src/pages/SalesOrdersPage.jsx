/**
 * Sales Orders management page.
 * Lists orders with status filtering and actions.
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { ordersAPI, exportAPI } from '../api';
import { downloadBlob } from '../utils/export';
import {
  ShoppingCart, Plus, Search, Eye, Loader2, Filter,
  ChevronLeft, ChevronRight, CheckCircle, XCircle,
  Truck, Package, FileText, Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

const STATUS_TRANSITIONS = {
  draft:     ['confirmed', 'cancelled'],
  confirmed: ['shipped', 'cancelled'],
  shipped:   ['delivered'],
  delivered: [],
  cancelled: [],
};

export default function SalesOrdersPage() {
  const { isSales } = useAuth();
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;
  const [actionLoading, setActionLoading] = useState(null);

  // Export state
  const [exporting, setExporting] = useState(false);

  const STATUS_CONFIG = {
    draft:      { label: t('draft'),      color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',       icon: FileText },
    confirmed:  { label: t('confirmed'),  color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300',   icon: CheckCircle },
    shipped:    { label: t('shipped'),    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', icon: Truck },
    delivered:  { label: t('delivered'),  color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',   icon: Package },
    cancelled:  { label: t('cancelled'),  color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',         icon: XCircle },
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.orders();
      downloadBlob(new Blob([response.data]), 'orders.xlsx');
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
      const response = await ordersAPI.list(params);
      const data = response.data;
      setOrders(data.results || (Array.isArray(data) ? data : []));
      setTotalCount(data.count || data.length || 0);
      setCurrentPage(page);
    } catch {
      toast.error(t('failedLoadOrders'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter]);

  useEffect(() => { fetchOrders(1); }, [fetchOrders]);

  const handleChangeStatus = async (order, newStatus) => {
    setActionLoading(order.id);
    try {
      await ordersAPI.changeStatus(order.id, newStatus);
      toast.success(t('statusChanged'));
      fetchOrders(currentPage);
    } catch (error) {
      const msg = error.response?.data?.error || t('failedChangeStatus');
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);
  const numberLocale = locale === 'ar' ? 'ar-SA' : 'en-US';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageOrders')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('viewManageOrders')}</p>
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
            <button onClick={() => navigate('/orders/create')}
              className="flex items-center gap-2 bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 text-white font-medium px-4 py-2.5 rounded-lg transition-colors shadow-sm">
              <Plus className="w-4 h-4" />
              {t('createOrder')}
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input type="text" value={searchTerm} onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            placeholder={t('searchByNameSku')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400"
          />
        </div>
        <div className="relative">
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            className="appearance-none pr-9 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white">
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
          <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>
        ) : orders.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <ShoppingCart className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium text-gray-500 dark:text-gray-400">{t('noOrders')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('orderNumber')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('customer')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('status')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('date')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('total')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('items')}</th>
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
                        <span className="font-mono text-sm font-semibold text-riadah-700 dark:text-accent-300 bg-riadah-50 dark:bg-riadah-900/30 px-2 py-1 rounded">
                          {order.order_number}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{order.customer_name}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.color}`}>
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{order.order_date}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">
                        {Number(order.total_amount).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} {t('currency')}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-600 dark:text-gray-300">{order.items_count}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1 flex-wrap">
                          <button onClick={() => navigate(`/orders/${order.id}`)}
                            className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title={t('viewDetails')}>
                            <Eye className="w-4 h-4" />
                          </button>
                          {isSales && transitions.map((newStatus) => (
                            <button key={newStatus}
                              onClick={() => handleChangeStatus(order, newStatus)}
                              disabled={actionLoading === order.id}
                              className={`p-1.5 rounded-lg transition-colors text-xs font-medium px-2 ${
                                newStatus === 'cancelled'
                                  ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                                  : 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
                              }`}
                              title={STATUS_CONFIG[newStatus].label}
                            >
                              {actionLoading === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : STATUS_CONFIG[newStatus].label}
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
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('showing')} {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} {t('of')} {totalCount}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => fetchOrders(currentPage - 1)} disabled={currentPage <= 1} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
              <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/30 rounded-lg">{currentPage} / {totalPages}</span>
              <button onClick={() => fetchOrders(currentPage + 1)} disabled={currentPage >= totalPages} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
