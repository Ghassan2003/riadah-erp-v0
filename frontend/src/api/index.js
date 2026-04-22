/**
 * Axios API client with JWT token management.
 * Automatically attaches the access token to every request.
 */

import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, redirect to login
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);
        originalRequest.headers.Authorization = `Bearer ${access}`;

        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout the user
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  login2FA: (data) => api.post('/auth/login/2fa/', data),
  register: (userData) => api.post('/auth/register/', userData),
  refreshToken: (refresh) => api.post('/auth/refresh/', { refresh }),
};

// Profile API endpoints
export const profileAPI = {
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
};

// User management API (admin only)
export const usersAPI = {
  list: (params) => api.get('/auth/users/', { params }),
  get: (id) => api.get(`/auth/users/${id}/`),
  create: (data) => api.post('/auth/users/create/', data),
  toggleActive: (id) => api.patch(`/auth/users/${id}/toggle-active/`),
  reset2FA: (id) => api.post(`/auth/users/${id}/reset-2fa/`),
  forceChangePassword: (id) => api.post(`/auth/users/${id}/force-change-password/`),
  update: (id, data) => api.patch(`/auth/users/${id}/update/`, data),
};

// 2FA API
export const twoFactorAPI = {
  setup: (data) => api.post('/auth/2fa/setup/', data),
  verify: (code) => api.post('/auth/2fa/verify/', { code }),
  status: () => api.get('/auth/2fa/status/'),
  disable: (data) => api.post('/auth/2fa/disable/', data),
};

// Permissions API
export const permissionsAPI = {
  list: () => api.get('/auth/permissions/'),
  allRoles: () => api.get('/auth/permissions/roles/'),
  rolePermissions: (role) => api.get(`/auth/permissions/roles/${role}/`),
  updateRole: (role, permissionIds) => api.put(`/auth/permissions/roles/${role}/update/`, { role, permission_ids: permissionIds }),
  check: (code) => api.post('/auth/permissions/check/', { code }),
  myPermissions: () => api.get('/auth/permissions/my/'),
  seed: () => api.post('/auth/permissions/seed/'),

};

// Password Policy API
export const passwordPolicyAPI = {
  get: () => api.get('/auth/password-policy/'),
  update: (data) => api.put('/auth/password-policy/', data),
  info: () => api.get('/auth/password-policy/info/'),
};

// Forgot / Reset Password API
export const forgotPasswordAPI = {
  request: (email) => api.post('/auth/forgot-password/', { email }),
  reset: (data) => api.post('/auth/reset-password/', data),
};

// Inventory / Products API
export const productsAPI = {
  list: (params) => api.get('/inventory/products/', { params }),
  get: (id) => api.get(`/inventory/products/${id}/`),
  create: (data) => api.post('/inventory/products/', data),
  update: (id, data) => api.patch(`/inventory/products/${id}/`, data),
  softDelete: (id) => api.delete(`/inventory/products/${id}/soft-delete/`),
  restore: (id) => api.post(`/inventory/products/${id}/restore/`),
  getStats: () => api.get('/inventory/stats/'),
};

// Customers API
export const customersAPI = {
  list: (params) => api.get('/sales/customers/', { params }),
  get: (id) => api.get(`/sales/customers/${id}/`),
  create: (data) => api.post('/sales/customers/', data),
  update: (id, data) => api.patch(`/sales/customers/${id}/`, data),
  softDelete: (id) => api.delete(`/sales/customers/${id}/soft-delete/`),
};

// Sales Orders API
export const ordersAPI = {
  list: (params) => api.get('/sales/orders/', { params }),
  get: (id) => api.get(`/sales/orders/${id}/`),
  create: (data) => api.post('/sales/orders/create/', data),
  update: (id, data) => api.patch(`/sales/orders/${id}/update/`, data),
  delete: (id) => api.delete(`/sales/orders/${id}/delete/`),
  changeStatus: (id, status) => api.post(`/sales/orders/${id}/change-status/`, { status }),
  getStats: () => api.get('/sales/stats/'),
};

// Accounting API
export const accountsAPI = {
  list: (params) => api.get('/accounting/accounts/', { params }),
  get: (id) => api.get(`/accounting/accounts/${id}/`),
  create: (data) => api.post('/accounting/accounts/create/', data),
  update: (id, data) => api.patch(`/accounting/accounts/${id}/update/`, data),
  delete: (id) => api.delete(`/accounting/accounts/${id}/delete/`),
};

export const journalEntriesAPI = {
  list: (params) => api.get('/accounting/entries/', { params }),
  get: (id) => api.get(`/accounting/entries/${id}/`),
  create: (data) => api.post('/accounting/entries/create/', data),
  post: (id) => api.post(`/accounting/entries/${id}/post/`),
  reverse: (id) => api.post(`/accounting/entries/${id}/reverse/`),
  update: (id, data) => api.patch(`/accounting/entries/${id}/update/`, data),
};

export const reportsAPI = {
  incomeStatement: (params) => api.get('/accounting/reports/income-statement/', { params }),
  balanceSheet: () => api.get('/accounting/reports/balance-sheet/'),
};

export const accountingAPI = {
  getStats: () => api.get('/accounting/stats/'),
};

// HR API
export const departmentsAPI = {
  list: (params) => api.get('/hr/departments/', { params }),
  get: (id) => api.get(`/hr/departments/${id}/`),
  create: (data) => api.post('/hr/departments/', data),
  update: (id, data) => api.patch(`/hr/departments/${id}/`, data),
  delete: (id) => api.delete(`/hr/departments/${id}/delete/`),
  restore: (id) => api.post(`/hr/departments/${id}/restore/`),
};

export const employeesAPI = {
  list: (params) => api.get('/hr/employees/', { params }),
  get: (id) => api.get(`/hr/employees/${id}/`),
  create: (data) => api.post('/hr/employees/', data),
  update: (id, data) => api.patch(`/hr/employees/${id}/`, data),
  delete: (id) => api.delete(`/hr/employees/${id}/delete/`),
  restore: (id) => api.post(`/hr/employees/${id}/restore/`),
};

export const attendanceAPI = {
  list: (params) => api.get('/hr/attendance/', { params }),
  create: (data) => api.post('/hr/attendance/create/', data),
  get: (id) => api.get(`/hr/attendance/${id}/`),
  update: (id, data) => api.patch(`/hr/attendance/${id}/update/`, data),
  delete: (id) => api.delete(`/hr/attendance/${id}/delete/`),
};

export const leavesAPI = {
  list: (params) => api.get('/hr/leaves/', { params }),
  create: (data) => api.post('/hr/leaves/create/', data),
  approve: (id, data) => api.post(`/hr/leaves/${id}/approve/`, data),
  get: (id) => api.get(`/hr/leaves/${id}/`),
  delete: (id) => api.delete(`/hr/leaves/${id}/delete/`),
};

export const hrAPI = {
  getStats: () => api.get('/hr/stats/'),
};

// Purchases API
export const suppliersAPI = {
  list: (params) => api.get('/purchases/suppliers/', { params }),
  get: (id) => api.get(`/purchases/suppliers/${id}/`),
  create: (data) => api.post('/purchases/suppliers/', data),
  update: (id, data) => api.patch(`/purchases/suppliers/${id}/`, data),
  softDelete: (id) => api.delete(`/purchases/suppliers/${id}/soft-delete/`),
  restore: (id) => api.post(`/purchases/suppliers/${id}/restore/`),
};

export const purchaseOrdersAPI = {
  list: (params) => api.get('/purchases/orders/', { params }),
  get: (id) => api.get(`/purchases/orders/${id}/`),
  create: (data) => api.post('/purchases/orders/create/', data),
  update: (id, data) => api.patch(`/purchases/orders/${id}/update/`, data),
  delete: (id) => api.delete(`/purchases/orders/${id}/delete/`),
  changeStatus: (id, status) => api.post(`/purchases/orders/${id}/change-status/`, { status }),
  getStats: () => api.get('/purchases/stats/'),
};

// Documents API
export const documentsAPI = {
  list: (params) => api.get('/documents/', { params }),
  get: (id) => api.get(`/documents/${id}/`),
  upload: (formData) => api.post('/documents/upload/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/documents/${id}/delete/`),
  download: (id) => api.get(`/documents/${id}/download/`),
  categories: () => api.get('/documents/categories/'),
  update: (id, data) => api.patch(`/documents/${id}/update/`, data),
  deleteCategory: (id) => api.delete(`/documents/categories/${id}/delete/`),
};

// Projects API
export const projectsAPI = {
  list: (params) => api.get('/projects/', { params }),
  get: (id) => api.get(`/projects/${id}/`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.patch(`/projects/${id}/`, data),
  delete: (id) => api.delete(`/projects/${id}/delete/`),
  getStats: () => api.get('/projects/stats/'),
};

export const projectTasksAPI = {
  list: (params) => api.get('/projects/tasks/', { params }),
  get: (id) => api.get(`/projects/tasks/${id}/`),
  create: (data) => api.post('/projects/tasks/', data),
  update: (id, data) => api.patch(`/projects/tasks/${id}/`, data),
  delete: (id) => api.delete(`/projects/tasks/${id}/delete/`),
  comments: (taskId) => api.get(`/projects/tasks/${taskId}/comments/`),
  addComment: (taskId, data) => api.post(`/projects/tasks/${taskId}/comments/`, data),
  getComment: (id) => api.get(`/projects/comments/${id}/`),
  updateComment: (id, data) => api.patch(`/projects/comments/${id}/update/`, data),
  deleteComment: (id) => api.delete(`/projects/comments/${id}/delete/`),
};

export const projectExpensesAPI = {
  list: (params) => api.get('/projects/expenses/', { params }),
  create: (data) => api.post('/projects/expenses/', data),
  delete: (id) => api.delete(`/projects/expenses/${id}/delete/`),
  get: (id) => api.get(`/projects/expenses/${id}/`),
  update: (id, data) => api.patch(`/projects/expenses/${id}/update/`, data),
};

// Notifications API
export const notificationsAPI = {
  list: () => api.get('/notifications/'),
  unreadCount: () => api.get('/notifications/unread-count/'),
  markRead: (id) => api.post(`/notifications/${id}/read/`),
  markAllRead: () => api.post('/notifications/mark-all-read/'),
  // New advanced notification endpoints
  filtered: (params) => api.get('/notifications/filtered/', { params }),
  detail: (id) => api.get(`/notifications/${id}/detail/`),
  delete: (id) => api.delete(`/notifications/${id}/delete/`),
  bulkDelete: (ids) => api.post('/notifications/bulk-delete/', { ids }),
  stats: () => api.get('/notifications/stats/'),
  adminCreate: (data) => api.post('/notifications/admin/create/', data),
  cleanup: (days) => api.post('/notifications/admin/cleanup/', { days }),
};

// Dashboard API
export const dashboardAPI = {
  getStats: (params) => api.get('/dashboard/stats/', { params }),
  liveStats: () => api.get('/dashboard/live-stats/'),
};

// PDF Reports API - Enhanced
export const pdfAPI = {
  incomeStatement: (params) => api.get('/accounting/reports/income-statement/pdf/', { params, responseType: 'blob' }),
  balanceSheet: () => api.get('/accounting/reports/balance-sheet/pdf/', { responseType: 'blob' }),
  enhancedIncome: (params) => api.get('/reports/income-statement/enhanced/pdf/', { params, responseType: 'blob' }),
  enhancedBalance: (params) => api.get('/reports/balance-sheet/enhanced/pdf/', { params, responseType: 'blob' }),
  cashFlow: (params) => api.get('/reports/cash-flow/pdf/', { params, responseType: 'blob' }),
  moduleReport: (module, params) => api.get(`/reports/pdf/${module}/`, { params, responseType: 'blob' }),
};

// Financial Reports API - Enhanced
export const financialReportsAPI = {
  incomeStatement: (params) => api.get('/accounting/reports/income-statement/', { params }),
  balanceSheet: () => api.get('/accounting/reports/balance-sheet/'),
  cashFlow: (params) => api.get('/reports/cash-flow/', { params }),
};

// Audit Log API
export const auditLogAPI = {
  list: (params) => api.get('/audit-log/', { params }),
  stats: () => api.get('/audit-log/stats/'),
  clear: (days) => api.delete('/audit-log/clear/', { params: { days } }),
};

// Excel Export API
export const exportAPI = {
  users: () => api.get('/auth/users/export/', { responseType: 'blob' }),
  products: () => api.get('/inventory/products/export/', { responseType: 'blob' }),
  customers: () => api.get('/sales/customers/export/', { responseType: 'blob' }),
  orders: () => api.get('/sales/orders/export/', { responseType: 'blob' }),
  accounts: () => api.get('/accounting/accounts/export/', { responseType: 'blob' }),
  entries: () => api.get('/accounting/entries/export/', { responseType: 'blob' }),
  employees: () => api.get('/hr/employees/export/', { responseType: 'blob' }),
  attendance: (params) => api.get('/hr/attendance/export/', { params, responseType: 'blob' }),
  leaves: () => api.get('/hr/leaves/export/', { responseType: 'blob' }),
  suppliers: () => api.get('/purchases/suppliers/export/', { responseType: 'blob' }),
  purchaseOrders: () => api.get('/purchases/orders/export/', { responseType: 'blob' }),
  projects: () => api.get('/projects/export/', { responseType: 'blob' }),
  warehouses: () => api.get('/warehouse/warehouses/export/', { responseType: 'blob' }),
  transfers: () => api.get('/warehouse/transfers/export/', { responseType: 'blob' }),
  adjustments: () => api.get('/warehouse/adjustments/export/', { responseType: 'blob' }),
  assets: () => api.get('/assets/assets/export/', { responseType: 'blob' }),
  contracts: () => api.get('/contracts/contracts/export/', { responseType: 'blob' }),
  invoices: () => api.get('/invoicing/export/', { responseType: 'blob' }),
  payroll: () => api.get('/payroll/export/', { responseType: 'blob' }),
  pos: (params) => api.get('/pos/export/', { params, responseType: 'blob' }),
  payments: (params) => api.get('/payments/export/', { params, responseType: 'blob' }),
};

// System API
export const systemAPI = {
  info: () => api.get('/system/info/'),
};

// Advanced Analytics Reports API
export const analyticsAPI = {
  sales: (params) => api.get('/reports/sales-analytics/', { params }),
  inventory: (params) => api.get('/reports/inventory-analytics/', { params }),
  financial: (params) => api.get('/reports/financial-analytics/', { params }),
  hr: (params) => api.get('/reports/hr-analytics/', { params }),
};

// Maintenance API - Backup
export const backupAPI = {
  list: (params) => api.get('/maintenance/backups/', { params }),
  stats: () => api.get('/maintenance/backups/stats/'),
  create: (data) => api.post('/maintenance/backups/create/', data),
  download: (id) => api.get(`/maintenance/backups/${id}/download/`, { responseType: 'blob' }),
  restore: (id) => api.post(`/maintenance/backups/${id}/restore/`),
  delete: (id) => api.delete(`/maintenance/backups/${id}/delete/`),
};

// Maintenance API - Error Log
export const errorLogAPI = {
  list: (params) => api.get('/maintenance/errors/', { params }),
  stats: () => api.get('/maintenance/errors/stats/'),
  detail: (id) => api.get(`/maintenance/errors/${id}/`),
  resolve: (id, data) => api.post(`/maintenance/errors/${id}/resolve/`, data),
  batchResolve: (data) => api.post('/maintenance/errors/batch-resolve/', data),
  clear: (days) => api.delete('/maintenance/errors/clear/', { params: { days } }),
};

// Maintenance API - System Settings
export const settingsAPI = {
  get: () => api.get('/maintenance/settings/'),
  update: (data) => api.put('/maintenance/settings/', data),
  numberPreview: () => api.get('/maintenance/settings/number-preview/'),
};

// Maintenance API - Cron Jobs
export const cronJobAPI = {
  list: (params) => api.get('/maintenance/cron-jobs/', { params }),
  stats: () => api.get('/maintenance/cron-jobs/stats/'),
  create: (data) => api.post('/maintenance/cron-jobs/create/', data),
  detail: (id) => api.get(`/maintenance/cron-jobs/${id}/`),
  update: (id, data) => api.put(`/maintenance/cron-jobs/${id}/`, data),
  delete: (id) => api.delete(`/maintenance/cron-jobs/${id}/`),
  toggle: (id, data) => api.post(`/maintenance/cron-jobs/${id}/toggle/`, data),
  runNow: (id) => api.post(`/maintenance/cron-jobs/${id}/run-now/`),
};

// Videos / Instructions API
export const videosAPI = {
  list: (params) => api.get('/videos/videos/', { params }),
  get: (id) => api.get(`/videos/videos/${id}/`),
  create: (formData) => api.post('/videos/videos/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, formData) => api.patch(`/videos/videos/${id}/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/videos/videos/${id}/`),
  like: (id) => api.post(`/videos/videos/${id}/like/`),
  featured: () => api.get('/videos/videos/featured/'),
  stats: () => api.get('/videos/videos/stats/'),
  search: (query) => api.get('/videos/search/', { params: { q: query } }),
};

export const videoCategoriesAPI = {
  list: () => api.get('/videos/categories/'),
  get: (id) => api.get(`/videos/categories/${id}/`),
  create: (data) => api.post('/videos/categories/', data),
  update: (id, data) => api.patch(`/videos/categories/${id}/`, data),
  delete: (id) => api.delete(`/videos/categories/${id}/`),

};

export const videoProgressAPI = {
  list: () => api.get('/videos/progress/'),
  update: (data) => api.post('/videos/progress/', data),
  getVideo: (videoId) => api.get(`/videos/progress/${videoId}/`),
};

export const videoCommentsAPI = {
  list: (videoId) => api.get(`/videos/${videoId}/comments/`),
  create: (videoId, data) => api.post(`/videos/${videoId}/comments/`, data),
  delete: (commentId) => api.delete(`/videos/comments/${commentId}/delete/`),
  get: (commentId) => api.get(`/videos/comments/${commentId}/`),
  update: (commentId, data) => api.patch(`/videos/comments/${commentId}/update/`, data),
};

// POS (Point of Sale) API
export const posAPI = {
  getStats: () => api.get('/pos/stats/'),
  openShift: (data) => api.post('/pos/shifts/open/', data),
  closeShift: (id, data) => api.post(`/pos/shifts/${id}/close/`, data),
  getShifts: (params) => api.get('/pos/shifts/', { params }),
  getShift: (id) => api.get(`/pos/shifts/${id}/`),
  createSale: (data) => api.post('/pos/sales/create/', data),
  getSales: (params) => api.get('/pos/sales/', { params }),
  getSale: (id) => api.get(`/pos/sales/${id}/`),
  voidSale: (id, data) => api.post(`/pos/sales/${id}/void/`, data),
  getRefunds: (params) => api.get('/pos/refunds/', { params }),
  createRefund: (data) => api.post('/pos/refunds/create/', data),
  getHolds: (params) => api.get('/pos/holds/', { params }),
  createHold: (data) => api.post('/pos/holds/create/', data),
  deleteHold: (id) => api.delete(`/pos/holds/${id}/`),
  getDrawerTransactions: (params) => api.get('/pos/drawer/', { params }),
  createDrawerTransaction: (data) => api.post('/pos/drawer/create/', data),
  export: () => api.get('/pos/export/', { responseType: 'blob' }),
  getRefund: (id) => api.get(`/pos/refunds/${id}/`),
  getHold: (id) => api.get(`/pos/holds/${id}/`),
  getDrawerTransaction: (id) => api.get(`/pos/drawer/${id}/`),
};

// Invoicing API
export const invoicingAPI = {
  getStats: () => api.get('/invoicing/stats/'),
  getInvoices: (params) => api.get('/invoicing/', { params }),
  createInvoice: (data) => api.post('/invoicing/create/', data),
  getInvoice: (id) => api.get(`/invoicing/${id}/`),
  updateInvoice: (id, data) => api.patch(`/invoicing/${id}/update/`, data),
  deleteInvoice: (id) => api.delete(`/invoicing/${id}/delete/`),
  restoreInvoice: (id) => api.post(`/invoicing/${id}/restore/`),
  changeStatus: (id, data) => api.post(`/invoicing/${id}/change-status/`, data),
  sendInvoice: (id) => api.post(`/invoicing/${id}/send/`),
  duplicateInvoice: (id) => api.post(`/invoicing/${id}/duplicate/`),
  getPayments: (invoiceId) => api.get(`/invoicing/${invoiceId}/payments/`),
  createPayment: (invoiceId, data) => api.post(`/invoicing/${invoiceId}/payments/create/`, data),
  deletePayment: (invoiceId, paymentPk) => api.delete(`/invoicing/payments/${paymentPk}/delete/`),
  getReminders: (invoiceId) => api.get(`/invoicing/${invoiceId}/reminders/`),
  createReminder: (invoiceId, data) => api.post(`/invoicing/${invoiceId}/reminders/create/`, data),
  export: () => api.get('/invoicing/export/', { responseType: 'blob' }),
  getPayment: (invoiceId, paymentPk) => api.get(`/invoicing/payments/${paymentPk}/`),
  updatePayment: (invoiceId, paymentPk, data) => api.patch(`/invoicing/payments/${paymentPk}/update/`, data),
  getReminder: (invoiceId, reminderPk) => api.get(`/invoicing/reminders/${reminderPk}/`),
  updateReminder: (invoiceId, reminderPk, data) => api.patch(`/invoicing/reminders/${reminderPk}/update/`, data),
  deleteReminder: (invoiceId, reminderPk) => api.delete(`/invoicing/reminders/${reminderPk}/delete/`),
};

// Payroll API
export const payrollAPI = {
  getStats: () => api.get('/payroll/stats/'),
  getPeriods: (params) => api.get('/payroll/periods/', { params }),
  createPeriod: (data) => api.post('/payroll/periods/', data),
  updatePeriod: (id, data) => api.patch(`/payroll/periods/${id}/`, data),
  deletePeriod: (id) => api.delete(`/payroll/periods/${id}/delete/`),
  generatePayroll: (periodId) => api.post(`/payroll/periods/${periodId}/generate/`),
  closePeriod: (periodId) => api.post(`/payroll/periods/${periodId}/close/`),
  getRecords: (params) => api.get('/payroll/records/', { params }),
  updateRecord: (id, data) => api.patch(`/payroll/records/${id}/update/`, data),
  payRecord: (id) => api.post(`/payroll/records/${id}/pay/`),
  getAdvances: (params) => api.get('/payroll/advances/', { params }),
  createAdvance: (data) => api.post('/payroll/advances/', data),
  approveAdvance: (id, data) => api.post(`/payroll/advances/${id}/approve/`, data),
  getLoans: (params) => api.get('/payroll/loans/', { params }),
  createLoan: (data) => api.post('/payroll/loans/', data),
  approveLoan: (id, data) => api.post(`/payroll/loans/${id}/approve/`, data),
  listEndOfService: (params) => api.get('/payroll/end-of-service/', { params }),
  createEndOfService: (data) => api.post('/payroll/end-of-service/', data),
  export: () => api.get('/payroll/export/', { responseType: 'blob' }),
  getAdvance: (id) => api.get(`/payroll/advances/${id}/`),
  deleteAdvance: (id) => api.delete(`/payroll/advances/${id}/delete/`),
  getLoan: (id) => api.get(`/payroll/loans/${id}/`),
  deleteLoan: (id) => api.delete(`/payroll/loans/${id}/delete/`),
  getEndOfService: (id) => api.get(`/payroll/end-of-service/${id}/`),
  deleteEndOfService: (id) => api.delete(`/payroll/end-of-service/${id}/delete/`),
};

// Warehouse API
export const warehouseAPI = {
  getStats: () => api.get('/warehouse/stats/'),
  getWarehouses: (params) => api.get('/warehouse/warehouses/', { params }),
  createWarehouse: (data) => api.post('/warehouse/warehouses/', data),
  getWarehouse: (id) => api.get(`/warehouse/warehouses/${id}/`),
  updateWarehouse: (id, data) => api.patch(`/warehouse/warehouses/${id}/`, data),
  deleteWarehouse: (id) => api.delete(`/warehouse/warehouses/${id}/delete/`),
  restoreWarehouse: (id) => api.post(`/warehouse/warehouses/${id}/restore/`),
  completeCount: (id) => api.post(`/warehouse/counts/${id}/complete/`),
  listStock: (params) => api.get('/warehouse/stocks/', { params }),
  getTransfers: (params) => api.get('/warehouse/transfers/', { params }),
  createTransfer: (data) => api.post('/warehouse/transfers/create/', data),
  approveTransfer: (id) => api.post(`/warehouse/transfers/${id}/approve/`),
  receiveTransfer: (id, data) => api.post(`/warehouse/transfers/${id}/receive/`, data),
  getCounts: (params) => api.get('/warehouse/counts/', { params }),
  createCount: (data) => api.post('/warehouse/counts/create/', data),
  export: () => api.get('/warehouse/export/', { responseType: 'blob' }),
  createStock: (data) => api.post('/warehouse/stocks/create/', data),
  getStock: (id) => api.get(`/warehouse/stocks/${id}/`),
  updateStock: (id, data) => api.patch(`/warehouse/stocks/${id}/update/`, data),
  deleteStock: (id) => api.delete(`/warehouse/stocks/${id}/delete/`),
  getTransfer: (id) => api.get(`/warehouse/transfers/${id}/`),
  updateTransfer: (id, data) => api.patch(`/warehouse/transfers/${id}/update/`, data),
  cancelTransfer: (id) => api.post(`/warehouse/transfers/${id}/cancel/`),
  createAdjustment: (data) => api.post('/warehouse/adjustments/create/', data),
  getAdjustment: (id) => api.get(`/warehouse/adjustments/${id}/`),
  updateAdjustment: (id, data) => api.patch(`/warehouse/adjustments/${id}/update/`, data),
  deleteAdjustment: (id) => api.delete(`/warehouse/adjustments/${id}/delete/`),
  getCount: (id) => api.get(`/warehouse/counts/${id}/`),
  updateCount: (id, data) => api.patch(`/warehouse/counts/${id}/update/`, data),
  deleteCount: (id) => api.delete(`/warehouse/counts/${id}/delete/`),
};

// Fixed Assets API
export const assetsAPI = {
  getStats: () => api.get('/assets/stats/'),
  getAssets: (params) => api.get('/assets/assets/', { params }),
  createAsset: (data) => api.post('/assets/assets/', data),
  getAsset: (id) => api.get(`/assets/assets/${id}/`),
  updateAsset: (id, data) => api.patch(`/assets/assets/${id}/`, data),
  deleteAsset: (id) => api.delete(`/assets/assets/${id}/delete/`),
  restoreAsset: (id) => api.post(`/assets/assets/${id}/restore/`),
  transferAsset: (data) => api.post('/assets/transfers/create/', data),
  disposeAsset: (data) => api.post('/assets/disposals/create/', data),
  depreciateAll: () => api.post('/assets/depreciation/'),
  getCategories: (params) => api.get('/assets/categories/', { params }),
  createCategory: (data) => api.post('/assets/categories/', data),
  getMaintenances: (params) => api.get('/assets/maintenances/', { params }),
  createMaintenance: (data) => api.post('/assets/maintenances/create/', data),
  getDisposals: (params) => api.get('/assets/disposals/', { params }),
  export: () => api.get('/assets/export/', { responseType: 'blob' }),
  getTransfers: (params) => api.get('/assets/transfers/', { params }),
  getTransfer: (id) => api.get(`/assets/transfers/${id}/`),
  updateTransfer: (id, data) => api.patch(`/assets/transfers/${id}/update/`, data),
  deleteTransfer: (id) => api.delete(`/assets/transfers/${id}/delete/`),
  getMaintenance: (id) => api.get(`/assets/maintenances/${id}/`),
  updateMaintenance: (id, data) => api.patch(`/assets/maintenances/${id}/update/`, data),
  deleteMaintenance: (id) => api.delete(`/assets/maintenances/${id}/delete/`),
  getDisposal: (id) => api.get(`/assets/disposals/${id}/`),
  updateDisposal: (id, data) => api.patch(`/assets/disposals/${id}/update/`, data),
  deleteDisposal: (id) => api.delete(`/assets/disposals/${id}/delete/`),
};

// Contracts API
export const contractsAPI = {
  getStats: () => api.get('/contracts/stats/'),
  getContracts: (params) => api.get('/contracts/', { params }),
  createContract: (data) => api.post('/contracts/create/', data),
  getContract: (id) => api.get(`/contracts/${id}/`),
  updateContract: (id, data) => api.patch(`/contracts/${id}/`, data),
  deleteContract: (id) => api.delete(`/contracts/${id}/delete/`),
  restoreContract: (id) => api.post(`/contracts/${id}/restore/`),
  createMilestone: (data) => api.post('/contracts/milestones/create/', data),
  changeStatus: (id, data) => api.post(`/contracts/${id}/change-status/`, data),
  renewContract: (id, data) => api.post(`/contracts/${id}/renew/`, data),
  getMilestones: (params) => api.get('/contracts/milestones/', { params }),
  updateMilestone: (id, data) => api.patch(`/contracts/milestones/${id}/`, data),
  getContractPayments: (params) => api.get('/contracts/contract-payments/', { params }),
  createContractPayment: (data) => api.post('/contracts/contract-payments/create/', data),
  export: () => api.get('/contracts/export/', { responseType: 'blob' }),
  getMilestone: (id) => api.get(`/contracts/milestones/${id}/`),
  deleteMilestone: (id) => api.delete(`/contracts/milestones/${id}/delete/`),
  getContractPayment: (id) => api.get(`/contracts/contract-payments/${id}/`),
  updateContractPayment: (id, data) => api.patch(`/contracts/contract-payments/${id}/update/`, data),
  deleteContractPayment: (id) => api.delete(`/contracts/contract-payments/${id}/delete/`),
};

// Financial Payments API
export const paymentsAPI = {
  getStats: () => api.get('/payments/stats/'),
  getTransactions: (params) => api.get('/payments/transactions/', { params }),
  createTransaction: (data) => api.post('/payments/transactions/create/', data),
  deleteTransaction: (id) => api.delete(`/payments/transactions/${id}/delete/`),
  getAccounts: (params) => api.get('/payments/accounts/', { params }),
  createAccount: (data) => api.post('/payments/accounts/create/', data),
  updateAccount: (id, data) => api.patch(`/payments/accounts/${id}/`, data),
  getCheques: (params) => api.get('/payments/cheques/', { params }),
  createCheque: (data) => api.post('/payments/cheques/create/', data),
  updateChequeStatus: (id, data) => api.post(`/payments/cheques/${id}/update-status/`, data),
  getReconciliations: (params) => api.get('/payments/reconciliations/', { params }),
  createReconciliation: (data) => api.post('/payments/reconciliations/create/', data),
  export: () => api.get('/payments/export/', { responseType: 'blob' }),
  getTransaction: (id) => api.get(`/payments/transactions/${id}/`),
  deleteAccount: (id) => api.delete(`/payments/accounts/${id}/delete/`),
  getCheque: (id) => api.get(`/payments/cheques/${id}/`),
  deleteCheque: (id) => api.delete(`/payments/cheques/${id}/delete/`),
  getReconciliation: (id) => api.get(`/payments/reconciliations/${id}/`),
  updateReconciliation: (id, data) => api.patch(`/payments/reconciliations/${id}/update/`, data),
  deleteReconciliation: (id) => api.delete(`/payments/reconciliations/${id}/delete/`),
};

// Attachments API (Generic - link to any entity)
export const attachmentsAPI = {
  list: (contentType, objectId, params) => api.get('/attachments/', { params: { content_type: contentType, object_id: objectId, ...params } }),
  upload: (formData) => api.post('/attachments/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  get: (id) => api.get(`/attachments/${id}/`),
  update: (id, data) => api.patch(`/attachments/${id}/`, data),
  delete: (id) => api.delete(`/attachments/${id}/`),
  download: (id) => api.get(`/attachments/${id}/download/`, { responseType: 'blob' }),
  bulkDelete: (ids) => api.post('/attachments/bulk-delete/', { ids }),
};

export default api;
