/**
 * Sales order detail page.
 * Shows full order info with items and status change actions.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ordersAPI } from '../api';
import {
  ArrowRight, Loader2, User, Package, ShoppingCart,
  CalendarDays, FileText, CheckCircle, XCircle,
  Truck, PackageCheck,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import AttachmentManager from '../components/AttachmentManager';

export default function OrderDetailPage() {
  const { t, locale } = useI18n();
  const { id } = useParams();
  const navigate = useNavigate();
  const { isSales } = useAuth();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const STATUS_CONFIG = {
    draft:      { label: t('draft'),       color: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600' },
    confirmed:  { label: t('confirmed'),    color: 'bg-riadah-100 text-riadah-700 border-riadah-200 dark:bg-riadah-900/30 dark:text-accent-300 dark:border-riadah-800' },
    shipped:    { label: t('shipped'),      color: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-800' },
    delivered:  { label: t('delivered'),    color: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800' },
    cancelled:  { label: t('cancelled'),    color: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800' },
  };

  const STATUS_TRANSITIONS = {
    draft:     ['confirmed', 'cancelled'],
    confirmed: ['shipped', 'cancelled'],
    shipped:   ['delivered'],
    delivered: [],
    cancelled: [],
  };

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        const response = await ordersAPI.get(id);
        setOrder(response.data);
      } catch {
        toast.error(t('orderNotFound'));
        navigate('/orders');
      } finally {
        setLoading(false);
      }
    };
    fetchOrder();
  }, [id, navigate]);

  const handleChangeStatus = async (newStatus) => {
    setActionLoading(true);
    try {
      const response = await ordersAPI.changeStatus(id, newStatus);
      setOrder(response.data.order);
      toast.success(`${t('statusChanged')} "${STATUS_CONFIG[newStatus].label}"`);
    } catch (error) {
      const msg = error.response?.data?.error || t('statusChangeFailed');
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><Loader2 className="w-8 h-8 animate-spin text-accent-500" /></div>;
  }

  if (!order) return null;

  const statusCfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.draft;
  const transitions = STATUS_TRANSITIONS[order.status] || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/orders')} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          <ArrowRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{order.order_number}</h1>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${statusCfg.color}`}>
              {statusCfg.label}
            </span>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('orderDetails')}</p>
        </div>
      </div>

      {/* Order info cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
            <User className="w-4 h-4" />
            <span className="text-sm">{t('customer')}</span>
          </div>
          <p className="font-semibold text-gray-900 dark:text-gray-100">{order.customer_name}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
            <CalendarDays className="w-4 h-4" />
            <span className="text-sm">{t('orderDate')}</span>
          </div>
          <p className="font-semibold text-gray-900 dark:text-gray-100">{order.order_date}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
            <ShoppingCart className="w-4 h-4" />
            <span className="text-sm">{t('createdBy')}</span>
          </div>
          <p className="font-semibold text-gray-900 dark:text-gray-100">{order.created_by_name || '-'}</p>
        </div>
      </div>

      {/* Status actions */}
      {isSales && transitions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">{t('changeStatus')}</h3>
          <div className="flex items-center gap-2 flex-wrap">
            {transitions.map((newStatus) => (
              <button key={newStatus} onClick={() => handleChangeStatus(newStatus)} disabled={actionLoading}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  newStatus === 'cancelled'
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800'
                    : 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/40 border border-green-200 dark:border-green-800'
                }`}>
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {STATUS_CONFIG[newStatus].label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Order items table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <Package className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            {t('orderItems')} ({order.items?.length || 0})
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('item')}</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">SKU</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('quantity')}</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('unitPrice')}</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{t('total')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {(order.items || []).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900 dark:text-gray-100">{item.product_name}</td>
                  <td className="px-5 py-3"><span className="font-mono text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded">{item.product_sku}</span></td>
                  <td className="px-5 py-3 text-sm text-gray-700 dark:text-gray-300">{item.quantity}</td>
                  <td className="px-5 py-3 text-sm text-gray-700 dark:text-gray-300" dir="ltr">{Number(item.unit_price).toFixed(2)} {t('currency')}</td>
                  <td className="px-5 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">{Number(item.subtotal).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 })} {t('currency')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Total */}
        <div className="px-5 py-4 bg-gray-50 dark:bg-gray-800/70 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <span className="text-lg font-semibold text-gray-800 dark:text-gray-200">{t('grandTotal')}:</span>
          <span className="text-xl font-bold text-accent-500 dark:text-accent-400" dir="ltr">
            {Number(order.total_amount).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 })} {t('currency')}
          </span>
        </div>
      </div>

      {/* Notes */}
      {order.notes && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            {t('notes')}
          </h3>
          <p className="text-gray-600 dark:text-gray-300 text-sm">{order.notes}</p>
        </div>
      )}

      {/* Attachments */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <AttachmentManager
          contentType="sales.salesorder"
          objectId={id}
          category="order"
        />
      </div>
    </div>
  );
}
