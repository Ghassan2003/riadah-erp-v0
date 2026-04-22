/**
 * Create new sales order page.
 * Customer selection, product search, stock validation, order summary.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { customersAPI, productsAPI, ordersAPI } from '../api';
import {
  ArrowRight, Plus, Trash2, Search, Loader2, ShoppingCart,
  AlertTriangle, Package, User,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

export default function CreateOrderPage() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();

  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [customerSearch, setCustomerSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [loadingCustomers, setLoadingCustomers] = useState(true);
  const [loadingProducts, setLoadingProducts] = useState(true);

  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [orderItems, setOrderItems] = useState([]);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Fetch customers
  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const response = await customersAPI.list({ search: customerSearch || undefined, page_size: 50 });
        setCustomers(response.data.results || response.data);
      } catch {
        toast.error(t('errorLoadingCustomers') || 'فشل تحميل العملاء');
      } finally {
        setLoadingCustomers(false);
      }
    };
    const timer = setTimeout(fetchCustomers, 300);
    return () => clearTimeout(timer);
  }, [customerSearch]);

  // Fetch products
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await productsAPI.list({ search: productSearch || undefined, page_size: 100 });
        setProducts(response.data.results || response.data);
      } catch {
        toast.error(t('errorLoadingProducts') || 'فشل تحميل المنتجات');
      } finally {
        setLoadingProducts(false);
      }
    };
    const timer = setTimeout(fetchProducts, 300);
    return () => clearTimeout(timer);
  }, [productSearch]);

  // Add product to order
  const addProduct = (product) => {
    const existing = orderItems.find((item) => item.product_id === product.id);
    if (existing) {
      if (existing.quantity >= product.quantity) {
        toast.error(`${t('stockLimit')} "${product.name}" ${t('stockLimitAmount', { qty: product.quantity })}`);
        return;
      }
      setOrderItems(orderItems.map((item) =>
        item.product_id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      if (product.quantity <= 0) {
        toast.error(`${t('outOfStock')}: "${product.name}"`);
        return;
      }
      setOrderItems([...orderItems, {
        product_id: product.id,
        product_name: product.name,
        product_sku: product.sku,
        unit_price: product.unit_price,
        quantity: 1,
        available_stock: product.quantity,
      }]);
    }
  };

  // Update item quantity
  const updateQuantity = (productId, newQty) => {
    if (newQty < 1) return;
    const item = orderItems.find((i) => i.product_id === productId);
    if (item && newQty > item.available_stock) {
      toast.error(`${t('maxStock')}: ${item.available_stock}`);
      return;
    }
    setOrderItems(orderItems.map((item) =>
      item.product_id === productId ? { ...item, quantity: newQty } : item
    ));
  };

  // Remove item
  const removeItem = (productId) => {
    setOrderItems(orderItems.filter((item) => item.product_id !== productId));
  };

  // Calculate totals
  const subtotal = orderItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  const totalItems = orderItems.reduce((sum, item) => sum + item.quantity, 0);

  // Submit order
  const handleSubmit = async () => {
    if (!selectedCustomer) {
      toast.error(t('selectCustomerRequired') || 'يرجى اختيار عميل');
      return;
    }
    if (orderItems.length === 0) {
      toast.error(t('addProductRequired') || 'يرجى إضافة منتج واحد على الأقل');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        customer: selectedCustomer,
        notes,
        items: orderItems.map((item) => ({
          product: item.product_id,
          quantity: item.quantity,
        })),
      };
      const response = await ordersAPI.create(payload);
      toast.success(`${t('orderCreated')} ${response.data.order.order_number}`);
      navigate('/orders');
    } catch (error) {
      const msg = error.response?.data?.error ||
        error.response?.data?.items?.[0] ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        t('errorCreatingOrder');
      toast.error(typeof msg === 'string' ? msg : t('errorCreatingOrder'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/orders')} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          <ArrowRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('createOrder')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('createOrderDesc')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Customer + Products */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer selection */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <User className="w-5 h-5 text-accent-500 dark:text-accent-400" />
              {t('selectCustomer')} <span className="text-red-500">*</span>
            </h3>
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input type="text" value={customerSearch} onChange={(e) => setCustomerSearch(e.target.value)}
                placeholder={t('searchCustomer')}
                className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
            </div>
            {selectedCustomer && (
              <div className="mt-3 flex items-center justify-between bg-riadah-50 dark:bg-riadah-900/20 border border-riadah-200 dark:border-riadah-800 rounded-lg px-4 py-2">
                <span className="font-medium text-riadah-800 dark:text-accent-300">
                  {customers.find(c => c.id === selectedCustomer)?.name || t('customerSelected')}
                </span>
                <button onClick={() => setSelectedCustomer(null)} className="text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 text-xs">{t('change')}</button>
              </div>
            )}
            {!selectedCustomer && !loadingCustomers && (
              <div className="mt-2 max-h-40 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg">
                {customers.filter(c => c.is_active).map((customer) => (
                  <button key={customer.id} onClick={() => setSelectedCustomer(customer.id)}
                    className="w-full text-right px-4 py-2.5 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 border-b border-gray-100 dark:border-gray-700 last:border-0 transition-colors">
                    <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{customer.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{customer.email || customer.phone || '-'}</p>
                  </button>
                ))}
                {customers.length === 0 && <p className="text-center text-gray-400 dark:text-gray-500 py-3 text-sm">{t('noCustomers')}</p>}
              </div>
            )}
          </div>

          {/* Product search */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <Package className="w-5 h-5 text-green-500 dark:text-green-400" />
              {t('addItem')}
            </h3>
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input type="text" value={productSearch} onChange={(e) => setProductSearch(e.target.value)}
                placeholder={t('searchProduct')}
                className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div className="mt-2 max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg">
              {loadingProducts ? (
                <div className="flex items-center justify-center py-4"><Loader2 className="w-5 h-5 animate-spin text-gray-400 dark:text-gray-500" /></div>
              ) : products.filter(p => p.is_active).map((product) => {
                const inOrder = orderItems.find(i => i.product_id === product.id);
                return (
                  <div key={product.id}
                    className={`flex items-center justify-between px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 last:border-0 ${
                      product.quantity <= 0 ? 'opacity-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'
                    }`}>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">{product.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-3">
                        <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">{product.sku}</span>
                        <span>{Number(product.unit_price).toFixed(2)} {t('currency')}</span>
                        <span className={product.quantity <= 0 ? 'text-red-500 dark:text-red-400' : 'text-green-600 dark:text-green-400'}>
                          {t('stock')}: {product.quantity}
                        </span>
                      </p>
                    </div>
                    <button onClick={() => addProduct(product)}
                      disabled={product.quantity <= 0}
                      className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40">
                      <Plus className="w-3 h-3" />
                      {inOrder ? t('increase') : t('add')}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Order items */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-purple-500 dark:text-purple-400" />
              {t('orderItems')} ({orderItems.length})
            </h3>
            {orderItems.length === 0 ? (
              <p className="text-center text-gray-400 dark:text-gray-500 py-8 text-sm">{t('noItemsAdded')}</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-right py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('item')}</th>
                      <th className="text-right py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('price')}</th>
                      <th className="text-right py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('quantity')}</th>
                      <th className="text-right py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">{t('total')}</th>
                      <th className="text-right py-2 text-xs font-semibold text-gray-500 dark:text-gray-400"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {orderItems.map((item) => (
                      <tr key={item.product_id}>
                        <td className="py-3">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.product_name}</p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 font-mono">{item.product_sku}</p>
                        </td>
                        <td className="py-3 text-sm text-gray-600 dark:text-gray-300" dir="ltr">{Number(item.unit_price).toFixed(2)}</td>
                        <td className="py-3">
                          <div className="flex items-center gap-1">
                            <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                              disabled={item.quantity <= 1}
                              className="w-7 h-7 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 flex items-center justify-center text-sm">-</button>
                            <span className="w-10 text-center text-sm font-medium text-gray-900 dark:text-gray-100">{item.quantity}</span>
                            <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                              disabled={item.quantity >= item.available_stock}
                              className="w-7 h-7 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 flex items-center justify-center text-sm">+</button>
                          </div>
                          {item.quantity >= item.available_stock && (
                            <p className="text-xs text-orange-500 dark:text-orange-400 mt-0.5 flex items-center gap-0.5">
                              <AlertTriangle className="w-3 h-3" /> {t('maxStock')}
                            </p>
                          )}
                        </td>
                        <td className="py-3 text-sm font-semibold text-gray-900 dark:text-gray-100" dir="ltr">
                          {(item.quantity * item.unit_price).toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3">
                          <button onClick={() => removeItem(item.product_id)}
                            className="p-1.5 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">{t('notes')}</h3>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
              rows={3} className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 resize-none text-sm"
              placeholder={t('additionalNotes')}
            />
          </div>
        </div>

        {/* Right: Order summary */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 sticky top-24">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">{t('orderSummary')}</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t('customer')}:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {customers.find(c => c.id === selectedCustomer)?.name || t('notSelected')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t('productCount')}:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{orderItems.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t('totalUnits')}:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{totalItems}</span>
              </div>
              <hr className="my-3 border-gray-200 dark:border-gray-700" />
              <div className="flex justify-between text-base">
                <span className="font-semibold text-gray-800 dark:text-gray-200">{t('total')}:</span>
                <span className="font-bold text-accent-500 dark:text-accent-400" dir="ltr">
                  {subtotal.toLocaleString(locale === 'ar' ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2 })} {t('currency')}
                </span>
              </div>
            </div>
            <div className="mt-6 space-y-3">
              <button onClick={handleSubmit} disabled={submitting}
                className="w-full bg-riadah-500 dark:bg-riadah-700 hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
                {submitting ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('creating')}...</> : <><ShoppingCart className="w-4 h-4" /> {t('createOrder')}</>}
              </button>
              <button onClick={() => navigate('/orders')}
                className="w-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                {t('cancel')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
