/**
 * Axios API client with JWT token management.
 * Automatically attaches the access token to every request.
 */

import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // 15 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper: remove only auth-related keys from localStorage (preserves theme, language, etc.)
function clearAuthData() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

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

// Token refresh mutex to prevent concurrent refresh requests
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor: handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, redirect to login
          clearAuthData();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);
        originalRequest.headers.Authorization = `Bearer ${access}`;

        processQueue(null, access);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Refresh failed, logout the user
        clearAuthData();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
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
  registerOwner: (userData) => api.post('/auth/register-owner/', userData),
  checkRegistrationAvailability: () => api.get('/auth/register-owner/'),
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

// Invitations API
export const invitationsAPI = {
  list: (params) => api.get('/auth/invitations/', { params }),
  create: (data) => api.post('/auth/invitations/create/', data),
  cancel: (id) => api.post(`/auth/invitations/${id}/cancel/`),
  getDetails: (token) => api.get(`/auth/invitations/${token}/accept/`),
  accept: (token, data) => api.post(`/auth/invitations/${token}/accept/`, data),
};

// Sales API (alias for ordersAPI.getStats)
export const salesAPI = {
  getStats: () => api.get('/sales/stats/'),
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
  // New accounting report APIs
  trialBalance: (params) => api.get('/accounting/reports/trial-balance/', { params }),
  generalLedger: (params) => api.get('/accounting/reports/general-ledger/', { params }),
  cashFlowStatement: (params) => api.get('/accounting/reports/cash-flow/', { params }),
  vatReturn: (params) => api.get('/accounting/reports/vat-return/', { params }),
  arAging: () => api.get('/accounting/reports/ar-aging/'),
  apAging: () => api.get('/accounting/reports/ap-aging/'),
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
  getDepartmentTree: () => api.get('/hr/departments/tree/'),
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

// HR - Leave Balances API
export const leaveBalancesAPI = {
  list: (params) => api.get('/hr/leave-balances/', { params }),
  initialize: (data) => api.post('/hr/leave-balances/initialize/', data),
};

// HR - Holiday Calendar API
export const holidayCalendarAPI = {
  list: (params) => api.get('/hr/holiday-calendars/', { params }),
  get: (id) => api.get(`/hr/holiday-calendars/${id}/`),
  create: (data) => api.post('/hr/holiday-calendars/', data),
  update: (id, data) => api.patch(`/hr/holiday-calendars/${id}/`, data),
  getHolidays: (params) => api.get('/hr/holidays/', { params }),
  createHoliday: (data) => api.post('/hr/holidays/create/', data),
  bulkCreateHolidays: (data) => api.post('/hr/holidays/bulk-create/', data),
  deleteHoliday: (id) => api.delete(`/hr/holidays/${id}/delete/`),
  getYearCalendar: (params) => api.get('/hr/holidays/year-calendar/', { params }),
};

// HR - Employment History API
export const employmentHistoryAPI = {
  list: (params) => api.get('/hr/employment-history/', { params }),
  create: (data) => api.post('/hr/employment-history/create/', data),
  getEmployeeFullHistory: (id) => api.get(`/hr/employees/${id}/full-history/`),
};

// HR - Payslips API
export const payslipsAPI = {
  list: (params) => api.get('/hr/payslips/', { params }),
  get: (id) => api.get(`/hr/payslips/${id}/`),
  generate: (data) => api.post('/hr/payslips/generate/', data),
  approve: (id, data) => api.post(`/hr/payslips/${id}/approve/`, data),
  getStats: (params) => api.get('/hr/payslips/stats/', { params }),
};

// HR - Performance Reviews API
export const performanceReviewsAPI = {
  list: (params) => api.get('/hr/performance-reviews/', { params }),
  create: (data) => api.post('/hr/performance-reviews/create/', data),
  get: (id) => api.get(`/hr/performance-reviews/${id}/`),
  update: (id, data) => api.patch(`/hr/performance-reviews/${id}/`, data),
};

// HR - Shifts API
export const shiftsAPI = {
  list: (params) => api.get('/hr/shifts/', { params }),
  create: (data) => api.post('/hr/shifts/', data),
  get: (id) => api.get(`/hr/shifts/${id}/`),
  update: (id, data) => api.patch(`/hr/shifts/${id}/`, data),
  delete: (id) => api.delete(`/hr/shifts/${id}/`),
};

// HR - Employee Shifts API
export const employeeShiftsAPI = {
  list: (params) => api.get('/hr/employee-shifts/', { params }),
  create: (data) => api.post('/hr/employee-shifts/', data),
  get: (id) => api.get(`/hr/employee-shifts/${id}/`),
  update: (id, data) => api.patch(`/hr/employee-shifts/${id}/`, data),
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

// Purchase Requisitions API
export const purchaseRequisitionsAPI = {
  list: (params) => api.get('/purchases/requisitions/', { params }),
  create: (data) => api.post('/purchases/requisitions/', data),
  get: (id) => api.get(`/purchases/requisitions/${id}/`),
  approve: (id, data) => api.post(`/purchases/requisitions/${id}/approve/`, data),
  convert: (id, data) => api.post(`/purchases/requisitions/${id}/convert/`, data),
  delete: (id) => api.delete(`/purchases/requisitions/${id}/delete/`),
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
  getGanttData: (params) => api.get('/projects/gantt-data/', { params }),
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

// Projects Extended API - Phases, Milestones, Budget, Risks, Time, Contracts, Documents
export const projectPhasesAPI = {
  list: () => api.get('/projects/phases/'),
  create: (data) => api.post('/projects/phases/', data),
  update: (id, data) => api.patch(`/projects/phases/${id}/`, data),
  delete: (id) => api.delete(`/projects/phases/${id}/delete/`),
};

export const projectMilestonesAPI = {
  list: () => api.get('/projects/milestones/'),
  create: (data) => api.post('/projects/milestones/', data),
  update: (id, data) => api.patch(`/projects/milestones/${id}/`, data),
  delete: (id) => api.delete(`/projects/milestones/${id}/delete/`),
};

export const projectBudgetAPI = {
  items: (projectId) => api.get('/projects/budget-items/', { params: { project: projectId } }),
  createItem: (data) => api.post('/projects/budget-items/', data),
  updateItem: (id, data) => api.patch(`/projects/budget-items/${id}/`, data),
  deleteItem: (id) => api.delete(`/projects/budget-items/${id}/delete/`),
  stats: (projectId) => api.get('/projects/budget-stats/', { params: { project_id: projectId } }),
};

export const projectRisksAPI = {
  list: (projectId) => api.get('/projects/risks/', { params: { project: projectId } }),
  create: (data) => api.post('/projects/risks/', data),
  update: (id, data) => api.patch(`/projects/risks/${id}/`, data),
  delete: (id) => api.delete(`/projects/risks/${id}/delete/`),
  riskMatrix: (projectId) => api.get('/projects/risk-matrix/', { params: { project_id: projectId } }),
};

export const projectTimeAPI = {
  entries: (projectId) => api.get('/projects/time-entries/', { params: { project: projectId } }),
  createEntry: (data) => api.post('/projects/time-entries/', data),
  deleteEntry: (id) => api.delete(`/projects/time-entries/${id}/delete/`),
  report: (projectId) => api.get('/projects/time-report/', { params: { project_id: projectId } }),
};

export const projectContractsAPI = {
  list: () => api.get('/projects/contracts/'),
  create: (data) => api.post('/projects/contracts/', data),
  update: (id, data) => api.patch(`/projects/contracts/${id}/`, data),
  delete: (id) => api.delete(`/projects/contracts/${id}/delete/`),
};

export const projectDocumentsAPI = {
  list: (projectId) => api.get('/projects/documents/', { params: { project: projectId } }),
  create: (data) => api.post('/projects/documents/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/projects/documents/${id}/delete/`),
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

// Chatbot API
export const chatbotAPI = {
  listConversations: () => api.get('/chatbot/conversations/'),
  getConversation: (id) => api.get(`/chatbot/conversations/${id}/`),
  createConversation: (data) => api.post('/chatbot/conversations/', data),
  deleteConversation: (id) => api.delete(`/chatbot/conversations/${id}/`),
  sendMessage: (data) => api.post('/chatbot/chat/', data),
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
  financial: (params) => api.get('/reports/financial-analytics/', { params }),
  hr: (params) => api.get('/reports/hr-analytics/', { params }),

  // ML Forecasting
  salesForecast: () => api.get('/analytics/forecast/sales/'),
  demandForecast: (productId) => api.get(`/analytics/forecast/demand/${productId ? `?product_id=${productId}` : ''}`),
  cashflowForecast: () => api.get('/analytics/forecast/cashflow/'),

  // ML Anomaly Detection
  anomalies: (params = {}) => api.get('/analytics/anomalies/', { params }),
  anomalyStats: () => api.get('/analytics/anomalies/stats/'),
  reviewAnomaly: (id, data) => api.post(`/analytics/anomalies/${id}/review/`, data),

  // ML Customer Segments
  customerSegments: () => api.get('/analytics/segments/customers/'),
  segmentSummary: () => api.get('/analytics/segments/customers/summary/'),

  // ML Supplier Scores
  supplierScores: () => api.get('/analytics/suppliers/scores/'),

  // ML Model Metrics
  modelMetrics: () => api.get('/analytics/models/metrics/'),

  // Run ML (admin only)
  runForecast: () => api.post('/analytics/run-forecast/'),
  runAnomalyDetection: () => api.post('/analytics/run-anomaly-detection/'),
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
  deleteHold: (id) => api.delete(`/pos/holds/${id}/delete/`),
  getDrawerTransactions: (params) => api.get('/pos/drawer/', { params }),
  createDrawerTransaction: (data) => api.post('/pos/drawer/create/', data),
  export: () => api.get('/pos/export/', { responseType: 'blob' }),
  getRefund: (id) => api.get(`/pos/refunds/${id}/`),
  getHold: (id) => api.get(`/pos/holds/${id}/`),
  getDrawerTransaction: (id) => api.get(`/pos/drawer/${id}/`),

  // Price Lists
  priceLists: () => api.get('/pos/price-lists/'),
  createPriceList: (data) => api.post('/pos/price-lists/', data),
  updatePriceList: (id, data) => api.patch(`/pos/price-lists/${id}/`, data),
  deletePriceList: (id) => api.delete(`/pos/price-lists/${id}/delete/`),

  // Discount Rules
  discountRules: () => api.get('/pos/discount-rules/'),
  createDiscountRule: (data) => api.post('/pos/discount-rules/', data),
  updateDiscountRule: (id, data) => api.patch(`/pos/discount-rules/${id}/`, data),
  deleteDiscountRule: (id) => api.delete(`/pos/discount-rules/${id}/delete/`),
  applyDiscountRules: (params) => api.get('/pos/discount-rules/apply/', { params }),

  // Promo Codes
  promoCodes: () => api.get('/pos/promo-codes/'),
  createPromoCode: (data) => api.post('/pos/promo-codes/', data),
  updatePromoCode: (id, data) => api.patch(`/pos/promo-codes/${id}/`, data),
  deletePromoCode: (id) => api.delete(`/pos/promo-codes/${id}/delete/`),
  validatePromoCode: (data) => api.post('/pos/promo-codes/validate/', data),

  // Loyalty Programs
  loyaltyPrograms: () => api.get('/pos/loyalty-programs/'),
  createLoyaltyProgram: (data) => api.post('/pos/loyalty-programs/', data),
  updateLoyaltyProgram: (id, data) => api.patch(`/pos/loyalty-programs/${id}/`, data),
  deleteLoyaltyProgram: (id) => api.delete(`/pos/loyalty-programs/${id}/delete/`),
  loyaltyBalance: (customerId) => api.get('/pos/loyalty/balance/', { params: { customer_id: customerId } }),
  redeemLoyalty: (data) => api.post('/pos/loyalty/redeem/', data),

  // Restaurant Tables
  tables: () => api.get('/pos/tables/'),
  createTable: (data) => api.post('/pos/tables/', data),
  updateTable: (id, data) => api.patch(`/pos/tables/${id}/`, data),
  updateTableStatus: (id, data) => api.post(`/pos/tables/${id}/status/`, data),

  // Installments
  installments: (params) => api.get('/pos/installments/', { params }),
  installmentStats: () => api.get('/pos/installments/stats/'),
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

// Fiscal Closure API
export const fiscalClosureAPI = {
  getFiscalYears: (params) => api.get('/accounting/closure/fiscal-years/', { params }),
  createFiscalYear: (data) => api.post('/accounting/closure/fiscal-years/create/', data),
  getFiscalYear: (id) => api.get(`/accounting/closure/fiscal-years/${id}/`),
  closeFiscalYear: (id) => api.post(`/accounting/closure/fiscal-years/${id}/close/`),
  getFiscalPeriod: (id) => api.get(`/accounting/closure/fiscal-periods/${id}/`),
  closeFiscalPeriod: (id) => api.post(`/accounting/closure/fiscal-periods/${id}/close/`),
  reopenFiscalPeriod: (id) => api.post(`/accounting/closure/fiscal-periods/${id}/reopen/`),
  getPeriodBalances: (id) => api.get(`/accounting/closure/fiscal-periods/${id}/balances/`),
};

// Multi-Currency & Branches API
export const multiCurrencyAPI = {
  getCurrencies: (params) => api.get('/accounting/multi/currencies/', { params }),
  createCurrency: (data) => api.post('/accounting/multi/currencies/create/', data),
  getCurrency: (id) => api.get(`/accounting/multi/currencies/${id}/`),
  updateCurrency: (id, data) => api.patch(`/accounting/multi/currencies/${id}/update/`, data),
  updateExchangeRate: (id, data) => api.post(`/accounting/multi/currencies/${id}/update-rate/`, data),
  getExchangeRates: (id, params) => api.get(`/accounting/multi/currencies/${id}/exchange-rates/`, { params }),
  convertCurrency: (data) => api.post('/accounting/multi/currencies/convert/', data),
  getBranches: (params) => api.get('/accounting/multi/branches/', { params }),
  createBranch: (data) => api.post('/accounting/multi/branches/create/', data),
  getBranch: (id) => api.get(`/accounting/multi/branches/${id}/`),
  updateBranch: (id, data) => api.patch(`/accounting/multi/branches/${id}/update/`, data),
};

// Cost Allocation API
export const costAllocationAPI = {
  getCostCenters: (params) => api.get('/accounting/cost/cost-centers/', { params }),
  createCostCenter: (data) => api.post('/accounting/cost/cost-centers/create/', data),
  getCostCenter: (id) => api.get(`/accounting/cost/cost-centers/${id}/`),
  updateCostCenter: (id, data) => api.patch(`/accounting/cost/cost-centers/${id}/update/`, data),
  getAllocationRules: (params) => api.get('/accounting/cost/allocation-rules/', { params }),
  createAllocationRule: (data) => api.post('/accounting/cost/allocation-rules/create/', data),
  getAllocationRule: (id) => api.get(`/accounting/cost/allocation-rules/${id}/`),
  executeAllocationRule: (id) => api.post(`/accounting/cost/allocation-rules/${id}/execute/`),
  batchExecuteRules: () => api.post('/accounting/cost/allocation-rules/batch-execute/'),
  getAllocationLogs: (params) => api.get('/accounting/cost/allocation-logs/', { params }),
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
  updateChequeStatus: (id, data) => api.post(`/payments/cheques/${id}/status/`, data),
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

// Tenders API
export const tendersAPI = {
  getStats: () => api.get('/tenders/stats/'),
  getTenders: (params) => api.get('/tenders/', { params }),
  getTender: (id) => api.get(`/tenders/${id}/`),
  deleteTender: (id) => api.delete(`/tenders/${id}/delete/`),
  publishTender: (id) => api.post(`/tenders/${id}/publish/`),
  getDocuments: (params) => api.get('/tenders/documents/', { params }),
  getDocument: (id) => api.get(`/tenders/documents/${id}/`),
  getBids: (params) => api.get('/tenders/bids/', { params }),
  getBid: (id) => api.get(`/tenders/bids/${id}/`),
  disqualifyBid: (id) => api.post(`/tenders/bids/${id}/disqualify/`),
  getEvaluations: (params) => api.get('/tenders/evaluations/', { params }),
  getEvaluation: (id) => api.get(`/tenders/evaluations/${id}/`),
  getAwards: (params) => api.get('/tenders/awards/', { params }),
  createAward: (data) => api.post('/tenders/awards/create/', data),
  getAward: (id) => api.get(`/tenders/awards/${id}/`),
  approveAward: (id) => api.post(`/tenders/awards/${id}/approve/`),
  export: () => api.get('/tenders/export/', { responseType: 'blob' }),
};

// Import/Export API
export const importExportAPI = {
  getStats: () => api.get('/import-export/stats/'),
  getImportOrders: (params) => api.get('/import-export/import-orders/', { params }),
  createImportOrder: (data) => api.post('/import-export/import-orders/create/', data),
  getImportOrder: (id) => api.get(`/import-export/import-orders/${id}/`),
  changeImportStatus: (id, data) => api.post(`/import-export/import-orders/${id}/change-status/`, data),
  getImportItems: (params) => api.get('/import-export/import-items/', { params }),
  getImportItem: (id) => api.get(`/import-export/import-items/${id}/`),
  getExportOrders: (params) => api.get('/import-export/export-orders/', { params }),
  createExportOrder: (data) => api.post('/import-export/export-orders/create/', data),
  getExportOrder: (id) => api.get(`/import-export/export-orders/${id}/`),
  changeExportStatus: (id, data) => api.post(`/import-export/export-orders/${id}/change-status/`, data),
  getExportItems: (params) => api.get('/import-export/export-items/', { params }),
  getExportItem: (id) => api.get(`/import-export/export-items/${id}/`),
  getCustomsDeclarations: (params) => api.get('/import-export/customs-declarations/', { params }),
  createCustomsDeclaration: (data) => api.post('/import-export/customs-declarations/create/', data),
  getCustomsDeclaration: (id) => api.get(`/import-export/customs-declarations/${id}/`),
  changeCustomsStatus: (id, data) => api.post(`/import-export/customs-declarations/${id}/change-status/`, data),
  export: () => api.get('/import-export/export/', { responseType: 'blob' }),
};

// Equipment Maintenance API
export const equipMaintAPI = {
  getStats: () => api.get('/equip-maint/stats/'),
  getEquipment: (params) => api.get('/equip-maint/equipment/', { params }),
  createEquipment: (data) => api.post('/equip-maint/equipment/create/', data),
  getEquipmentDetail: (id) => api.get(`/equip-maint/equipment/${id}/`),
  getSchedules: (params) => api.get('/equip-maint/schedules/', { params }),
  getSchedule: (id) => api.get(`/equip-maint/schedules/${id}/`),
  createSchedule: (data) => api.post('/equip-maint/schedules/', data),
  getWorkOrders: (params) => api.get('/equip-maint/work-orders/', { params }),
  createWorkOrder: (data) => api.post('/equip-maint/work-orders/create/', data),
  getWorkOrder: (id) => api.get(`/equip-maint/work-orders/${id}/`),
  approveWorkOrder: (id) => api.post(`/equip-maint/work-orders/${id}/approve/`),
  startWorkOrder: (id) => api.post(`/equip-maint/work-orders/${id}/start/`),
  completeWorkOrder: (id) => api.post(`/equip-maint/work-orders/${id}/complete/`),
  getParts: (params) => api.get('/equip-maint/parts/', { params }),
  getPart: (id) => api.get(`/equip-maint/parts/${id}/`),
  getInspections: (params) => api.get('/equip-maint/inspections/', { params }),
  createInspection: (data) => api.post('/equip-maint/inspections/create/', data),
  export: () => api.get('/equip-maint/export/', { responseType: 'blob' }),
};

// CRM API
export const crmAPI = {
  getStats: () => api.get('/crm/stats/'),
  getContacts: (params) => api.get('/crm/contacts/', { params }),
  getContact: (id) => api.get(`/crm/contacts/${id}/`),
  createContact: (data) => api.post('/crm/contacts/', data),
  getLeads: (params) => api.get('/crm/leads/', { params }),
  getLead: (id) => api.get(`/crm/leads/${id}/`),
  createLead: (data) => api.post('/crm/leads/', data),
  changeLeadStatus: (id, data) => api.post(`/crm/leads/${id}/change-status/`, data),
  getLeadActivities: (leadId) => api.get(`/crm/leads/${leadId}/activities/`),
  completeLeadActivity: (id) => api.post(`/crm/leads/activities/${id}/complete/`),
  getSegments: (params) => api.get('/crm/segments/', { params }),
  getSegment: (id) => api.get(`/crm/segments/${id}/`),
  getCampaigns: (params) => api.get('/crm/campaigns/', { params }),
  getCampaign: (id) => api.get(`/crm/campaigns/${id}/`),
  createCampaign: (data) => api.post('/crm/campaigns/', data),
  changeCampaignStatus: (id, data) => api.post(`/crm/campaigns/${id}/change-status/`, data),
  getCampaignActivities: (campaignId) => api.get(`/crm/campaigns/${campaignId}/activities/`),
  export: () => api.get('/crm/export/', { responseType: 'blob' }),
  // New CRM APIs
  convertLead: (id) => api.post(`/crm/leads/${id}/convert/`),
  getPipelineFunnel: () => api.get('/crm/pipeline/funnel/'),
  getSalesForecast: (params) => api.get('/crm/sales-forecast/', { params }),
  // Companies (Accounts) APIs
  getCompanies: (params) => api.get('/crm/companies/', { params }),
  getCompany: (id) => api.get(`/crm/companies/${id}/`),
  createCompany: (data) => api.post('/crm/companies/', data),
  updateCompany: (id, data) => api.patch(`/crm/companies/${id}/`, data),
  deleteCompany: (id) => api.delete(`/crm/companies/${id}/`),
  getCompanyContacts: (id, params) => api.get(`/crm/companies/${id}/contacts/`, { params }),
  getCompanyStats: (id) => api.get(`/crm/companies/${id}/stats/`),
  // Lead Detail with Activities
  getLeadDetail: (id) => api.get(`/crm/leads/${id}/detail/`),
  // Sales Stage Analytics
  getSalesStageAnalytics: (params) => api.get('/crm/sales-stage-analytics/', { params }),

  // SLA Policies
  slaPolicies: () => api.get('/crm/sla-policies/'),
  createSLAPolicy: (data) => api.post('/crm/sla-policies/', data),
  updateSLAPolicy: (id, data) => api.patch(`/crm/sla-policies/${id}/`, data),
  deleteSLAPolicy: (id) => api.delete(`/crm/sla-policies/${id}/delete/`),

  // Tickets
  tickets: (params) => api.get('/crm/tickets/', { params }),
  createTicket: (data) => api.post('/crm/tickets/', data),
  updateTicket: (id, data) => api.patch(`/crm/tickets/${id}/`, data),
  deleteTicket: (id) => api.delete(`/crm/tickets/${id}/delete/`),
  assignTicket: (id, data) => api.post(`/crm/tickets/${id}/assign/`, data),
  resolveTicket: (id, data) => api.post(`/crm/tickets/${id}/resolve/`, data),
  ticketStats: () => api.get('/crm/ticket-stats/'),
  ticketComments: (ticketId) => api.get(`/crm/tickets/${ticketId}/comments/`),
  createTicketComment: (ticketId, data) => api.post(`/crm/tickets/${ticketId}/comments/`, data),

  // Quotations
  quotations: (params) => api.get('/crm/quotations/', { params }),
  createQuotation: (data) => api.post('/crm/quotations/', data),
  updateQuotation: (id, data) => api.patch(`/crm/quotations/${id}/`, data),
  deleteQuotation: (id) => api.delete(`/crm/quotations/${id}/delete/`),
  convertQuotation: (id) => api.post(`/crm/quotations/${id}/convert/`),

  // Top Sales Reps Analytics
  getTopReps: () => api.get('/crm/top-reps/'),
  // Lead Source Distribution
  getLeadSources: () => api.get('/crm/lead-sources/'),

  // Commissions
  commissions: (params) => api.get('/crm/commissions/', { params }),
  createCommission: (data) => api.post('/crm/commissions/', data),
  updateCommission: (id, data) => api.patch(`/crm/commissions/${id}/`, data),
  deleteCommission: (id) => api.delete(`/crm/commissions/${id}/delete/`),
  commissionStats: (params) => api.get('/crm/commission-stats/', { params }),
};

// ── Startup Finance API ──
export const startupFinanceAPI = {
  getDashboard: (params = {}) => api.get('/startup-finance/dashboard/', { params }),

  // Startup Profiles
  getProfiles: (params = {}) => api.get('/startup-finance/profiles/', { params }),
  getProfile: (id) => api.get(`/startup-finance/profiles/${id}/`),
  createProfile: (data) => api.post('/startup-finance/profiles/', data),
  updateProfile: (id, data) => api.patch(`/startup-finance/profiles/${id}/`, data),

  // Funding Rounds
  getFundingRounds: (params = {}) => api.get('/startup-finance/funding-rounds/', { params }),
  createFundingRound: (data) => api.post('/startup-finance/funding-rounds/', data),
  updateFundingRound: (id, data) => api.patch(`/startup-finance/funding-rounds/${id}/`, data),
  deleteFundingRound: (id) => api.delete(`/startup-finance/funding-rounds/${id}/`),

  // Burn Rate
  getBurnRateEntries: (params = {}) => api.get('/startup-finance/burn-rate/', { params }),
  createBurnRateEntry: (data) => api.post('/startup-finance/burn-rate/', data),

  // Subscription Plans
  getSubscriptionPlans: (params = {}) => api.get('/startup-finance/subscription-plans/', { params }),
  createSubscriptionPlan: (data) => api.post('/startup-finance/subscription-plans/', data),

  // Subscriptions
  getSubscriptions: (params = {}) => api.get('/startup-finance/subscriptions/', { params }),
  createSubscription: (data) => api.post('/startup-finance/subscriptions/', data),
  updateSubscription: (id, data) => api.patch(`/startup-finance/subscriptions/${id}/`, data),

  // Customer Metrics
  getCustomerMetrics: (params = {}) => api.get('/startup-finance/customer-metrics/', { params }),
  createCustomerMetric: (data) => api.post('/startup-finance/customer-metrics/', data),

  // Financial Entries
  getFinancialEntries: (params = {}) => api.get('/startup-finance/entries/', { params }),
  createFinancialEntry: (data) => api.post('/startup-finance/entries/', data),

  // KPIs
  getKPIs: (params = {}) => api.get('/startup-finance/kpis/', { params }),
  calculateKPIs: (data) => api.post('/startup-finance/calculate-kpis/', data),
};

// Recruitment API
export const recruitmentAPI = {
  getRequisitions: (params) => api.get('/hr/recruitment/requisitions/', { params }),
  getRequisition: (id) => api.get(`/hr/recruitment/requisitions/${id}/`),
  createRequisition: (data) => api.post('/hr/recruitment/requisitions/', data),
  getPostings: (params) => api.get('/hr/recruitment/postings/', { params }),
  getPosting: (id) => api.get(`/hr/recruitment/postings/${id}/`),
  createPosting: (data) => api.post('/hr/recruitment/postings/', data),
  getApplications: (params) => api.get('/hr/recruitment/applications/', { params }),
  getApplication: (id) => api.get(`/hr/recruitment/applications/${id}/`),
  updateApplication: (id, data) => api.patch(`/hr/recruitment/applications/${id}/`, data),
  getInterviews: (params) => api.get('/hr/recruitment/interviews/', { params }),
  createInterview: (data) => api.post('/hr/recruitment/interviews/create/', data),
  getInterview: (id) => api.get(`/hr/recruitment/interviews/${id}/`),
  updateInterview: (id, data) => api.patch(`/hr/recruitment/interviews/${id}/`, data),
  getOffers: (params) => api.get('/hr/recruitment/offers/', { params }),
  getOffer: (id) => api.get(`/hr/recruitment/offers/${id}/`),
  updateOffer: (id, data) => api.patch(`/hr/recruitment/offers/${id}/`, data),
  hireCandidate: (data) => api.post('/hr/recruitment/hire/', data),
};

// Qualifications & Documents API
export const qualificationsAPI = {
  getEducation: (employeeId) => api.get('/hr/qualifications/education/', { params: { employee: employeeId } }),
  addEducation: (data) => api.post('/hr/qualifications/education/', data),
  getExperience: (employeeId) => api.get('/hr/qualifications/experience/', { params: { employee: employeeId } }),
  addExperience: (data) => api.post('/hr/qualifications/experience/', data),
  getSkills: (employeeId) => api.get('/hr/qualifications/skills/', { params: { employee: employeeId } }),
  addSkill: (data) => api.post('/hr/qualifications/skills/', data),
  getLanguages: (employeeId) => api.get('/hr/qualifications/languages/', { params: { employee: employeeId } }),
  addLanguage: (data) => api.post('/hr/qualifications/languages/', data),
  getCertifications: (employeeId) => api.get('/hr/qualifications/certifications/', { params: { employee: employeeId } }),
  addCertification: (data) => api.post('/hr/qualifications/certifications/', data),
  getDocuments: (employeeId) => api.get('/hr/documents/documents/', { params: { employee: employeeId } }),
  uploadDocument: (data) => api.post('/hr/documents/documents/', data),
  getDocumentTemplates: () => api.get('/hr/documents/templates/'),
};

// Training API
export const trainingAPI = {
  getNeeds: (params) => api.get('/hr/training/needs/', { params }),
  createNeed: (data) => api.post('/hr/training/needs/', data),
  getCourses: (params) => api.get('/hr/training/courses/', { params }),
  getCourse: (id) => api.get(`/hr/training/courses/${id}/`),
  getSessions: (params) => api.get('/hr/training/sessions/', { params }),
  createSession: (data) => api.post('/hr/training/sessions/', data),
  getEnrollments: (params) => api.get('/hr/training/enrollments/', { params }),
  createEnrollment: (data) => api.post('/hr/training/enrollments/', data),
  getBudgets: (params) => api.get('/hr/training/budgets/', { params }),
};

// Employee Finances API
export const employeeFinancesAPI = {
  getLoans: (params) => api.get('/hr/finances/loans/', { params }),
  createLoan: (data) => api.post('/hr/finances/loans/', data),
  getLoan: (id) => api.get(`/hr/finances/loans/${id}/`),
  getLoanPayments: (loanId) => api.get('/hr/finances/loan-payments/', { params: { loan: loanId } }),
  getAdvances: (params) => api.get('/hr/finances/salary-advances/', { params }),
  createAdvance: (data) => api.post('/hr/finances/salary-advances/', data),
  getOvertime: (params) => api.get('/hr/finances/overtime-requests/', { params }),
  createOvertime: (data) => api.post('/hr/finances/overtime-requests/', data),
  approveOvertime: (id) => api.post(`/hr/finances/overtime-requests/${id}/approve/`),
};

// Benefits & Discipline API
export const benefitsAPI = {
  getInsurancePlans: () => api.get('/hr/benefits/health-insurance/'),
  getInsurancePlan: (id) => api.get(`/hr/benefits/health-insurance/${id}/`),
  getEmployeeInsurance: (params) => api.get('/hr/benefits/employee-insurance/', { params }),
  enrollInsurance: (data) => api.post('/hr/benefits/employee-insurance/', data),
  getDisciplinaryActions: (params) => api.get('/hr/benefits/disciplinary-actions/', { params }),
  createDisciplinaryAction: (data) => api.post('/hr/benefits/disciplinary-actions/', data),
  getGrievances: (params) => api.get('/hr/benefits/grievances/', { params }),
  createGrievance: (data) => api.post('/hr/benefits/grievances/', data),
  getGrievance: (id) => api.get(`/hr/benefits/grievances/${id}/`),
  getOffboarding: (params) => api.get('/hr/benefits/offboarding/', { params }),
  createOffboarding: (data) => api.post('/hr/benefits/offboarding/', data),
};

// HR Reports API
export const hrReportsAPI = {
  getWorkforceReport: (params) => api.get('/hr/reports/workforce/', { params }),
  getTurnoverReport: (params) => api.get('/hr/reports/turnover/', { params }),
  getEmployeeCostReport: (params) => api.get('/hr/reports/employee-cost/', { params }),
  getLeaveReport: (params) => api.get('/hr/reports/leaves/', { params }),
  getAttendanceReport: (params) => api.get('/hr/reports/attendance/', { params }),
  getPerformanceReport: (params) => api.get('/hr/reports/performance/', { params }),
  getOrgChart: (params) => api.get('/hr/org-chart/', { params }),
  getOrgStats: () => api.get('/hr/org-chart/stats/'),
};

export default api;
