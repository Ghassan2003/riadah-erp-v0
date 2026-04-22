/**
 * Tests for the API module (src/api/index.js).
 * Tests that all API endpoint groups are properly defined.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios before importing the API module
vi.mock('axios', () => {
  const createFn = vi.fn(() => {
    const api = {
      get: vi.fn(() => Promise.resolve({ data: {} })),
      post: vi.fn(() => Promise.resolve({ data: {} })),
      put: vi.fn(() => Promise.resolve({ data: {} })),
      patch: vi.fn(() => Promise.resolve({ data: {} })),
      delete: vi.fn(() => Promise.resolve({ data: {} })),
      defaults: { headers: { common: {} } },
      interceptors: {
        request: { use: vi.fn(), handlers: [] },
        response: { use: vi.fn(), handlers: [] },
      },
    };
    return api;
  });
  // Also expose create on the default export
  createFn.create = createFn;
  return { default: createFn };
});

describe('API Module', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should export api instance', async () => {
    const mod = await import('../api/index.js');
    expect(mod.default).toBeDefined();
    expect(mod.default.get).toBeDefined();
    expect(mod.default.post).toBeDefined();
    expect(mod.default.put).toBeDefined();
    expect(mod.default.patch).toBeDefined();
    expect(mod.default.delete).toBeDefined();
  });

  it('should export auth API endpoints', async () => {
    const { authAPI } = await import('../api/index.js');
    expect(authAPI.login).toBeDefined();
    expect(authAPI.login2FA).toBeDefined();
    expect(authAPI.register).toBeDefined();
    expect(authAPI.refreshToken).toBeDefined();
  });

  it('should export profile API endpoints', async () => {
    const { profileAPI } = await import('../api/index.js');
    expect(profileAPI.getProfile).toBeDefined();
    expect(profileAPI.updateProfile).toBeDefined();
    expect(profileAPI.changePassword).toBeDefined();
  });

  it('should export products API endpoints', async () => {
    const { productsAPI } = await import('../api/index.js');
    expect(productsAPI.list).toBeDefined();
    expect(productsAPI.get).toBeDefined();
    expect(productsAPI.create).toBeDefined();
    expect(productsAPI.update).toBeDefined();
    expect(productsAPI.softDelete).toBeDefined();
    expect(productsAPI.restore).toBeDefined();
    expect(productsAPI.getStats).toBeDefined();
  });

  it('should export customers API endpoints', async () => {
    const { customersAPI } = await import('../api/index.js');
    expect(customersAPI.list).toBeDefined();
    expect(customersAPI.create).toBeDefined();
    expect(customersAPI.update).toBeDefined();
    expect(customersAPI.softDelete).toBeDefined();
  });

  it('should export orders API endpoints', async () => {
    const { ordersAPI } = await import('../api/index.js');
    expect(ordersAPI.list).toBeDefined();
    expect(ordersAPI.get).toBeDefined();
    expect(ordersAPI.create).toBeDefined();
    expect(ordersAPI.changeStatus).toBeDefined();
    expect(ordersAPI.getStats).toBeDefined();
  });

  it('should export accounting API endpoints', async () => {
    const { accountsAPI, journalEntriesAPI, reportsAPI, accountingAPI } = await import('../api/index.js');
    expect(accountsAPI.list).toBeDefined();
    expect(accountsAPI.create).toBeDefined();
    expect(journalEntriesAPI.create).toBeDefined();
    expect(journalEntriesAPI.post).toBeDefined();
    expect(journalEntriesAPI.reverse).toBeDefined();
    expect(reportsAPI.incomeStatement).toBeDefined();
    expect(reportsAPI.balanceSheet).toBeDefined();
    expect(accountingAPI.getStats).toBeDefined();
  });

  it('should export HR API endpoints', async () => {
    const { departmentsAPI, employeesAPI, attendanceAPI, leavesAPI, hrAPI } = await import('../api/index.js');
    expect(departmentsAPI.list).toBeDefined();
    expect(employeesAPI.create).toBeDefined();
    expect(attendanceAPI.create).toBeDefined();
    expect(leavesAPI.create).toBeDefined();
    expect(leavesAPI.approve).toBeDefined();
    expect(hrAPI.getStats).toBeDefined();
  });

  it('should export notifications API endpoints', async () => {
    const { notificationsAPI } = await import('../api/index.js');
    expect(notificationsAPI.list).toBeDefined();
    expect(notificationsAPI.unreadCount).toBeDefined();
    expect(notificationsAPI.markRead).toBeDefined();
    expect(notificationsAPI.markAllRead).toBeDefined();
  });

  it('should export dashboard API endpoint', async () => {
    const { dashboardAPI } = await import('../api/index.js');
    expect(dashboardAPI.getStats).toBeDefined();
  });

  it('should export permissions API endpoints', async () => {
    const { permissionsAPI } = await import('../api/index.js');
    expect(permissionsAPI.list).toBeDefined();
    expect(permissionsAPI.check).toBeDefined();
    expect(permissionsAPI.myPermissions).toBeDefined();
  });

  it('should export documents API endpoints', async () => {
    const { documentsAPI } = await import('../api/index.js');
    expect(documentsAPI.list).toBeDefined();
    expect(documentsAPI.upload).toBeDefined();
    expect(documentsAPI.delete).toBeDefined();
    expect(documentsAPI.download).toBeDefined();
    expect(documentsAPI.categories).toBeDefined();
  });

  it('should export projects API endpoints', async () => {
    const { projectsAPI, projectTasksAPI, projectExpensesAPI } = await import('../api/index.js');
    expect(projectsAPI.list).toBeDefined();
    expect(projectsAPI.getStats).toBeDefined();
    expect(projectTasksAPI.list).toBeDefined();
    expect(projectTasksAPI.create).toBeDefined();
    expect(projectExpensesAPI.list).toBeDefined();
  });

  it('should export purchase API endpoints', async () => {
    const { suppliersAPI, purchaseOrdersAPI } = await import('../api/index.js');
    expect(suppliersAPI.list).toBeDefined();
    expect(suppliersAPI.create).toBeDefined();
    expect(purchaseOrdersAPI.list).toBeDefined();
    expect(purchaseOrdersAPI.create).toBeDefined();
    expect(purchaseOrdersAPI.getStats).toBeDefined();
  });

  it('should export system/maintenance API endpoints', async () => {
    const { backupAPI, errorLogAPI, settingsAPI, cronJobAPI, auditLogAPI } = await import('../api/index.js');
    expect(backupAPI.list).toBeDefined();
    expect(backupAPI.create).toBeDefined();
    expect(errorLogAPI.list).toBeDefined();
    expect(settingsAPI.get).toBeDefined();
    expect(cronJobAPI.list).toBeDefined();
    expect(cronJobAPI.runNow).toBeDefined();
    expect(auditLogAPI.list).toBeDefined();
  });

  it('should export PDF and export API endpoints', async () => {
    const { pdfAPI, exportAPI } = await import('../api/index.js');
    expect(pdfAPI.incomeStatement).toBeDefined();
    expect(pdfAPI.balanceSheet).toBeDefined();
    expect(exportAPI.users).toBeDefined();
    expect(exportAPI.products).toBeDefined();
    expect(exportAPI.orders).toBeDefined();
  });
});
