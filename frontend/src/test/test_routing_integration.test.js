/**
 * Integration tests for App routing with authentication.
 * Tests that authenticated users see the main layout.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import React from 'react';

vi.mock('../api/index.js', () => ({
  api: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    patch: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: vi.fn(), handlers: [] },
      response: { use: vi.fn(), handlers: [] },
    },
    defaults: { headers: { common: {} } },
  },
  authAPI: { login: vi.fn(), login2FA: vi.fn() },
  profileAPI: {
    getProfile: vi.fn(() => Promise.resolve({
      data: {
        id: 1, username: 'admin', role: 'admin',
        first_name: 'مدير', last_name: 'النظام', permissions: [],
      },
    })),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
  dashboardAPI: { getStats: vi.fn(() => Promise.resolve({ data: {} })) },
  notificationsAPI: {
    list: vi.fn(() => Promise.resolve({ data: { results: [] } })),
    unreadCount: vi.fn(() => Promise.resolve({ data: { count: 0 } })),
    markRead: vi.fn(),
    markAllRead: vi.fn(),
  },
  productsAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  customersAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  ordersAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  suppliersAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  projectsAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  documentsAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  accountsAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  journalEntriesAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  departmentsAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  employeesAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  auditLogAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  backupAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  errorLogAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  settingsAPI: { get: vi.fn(() => Promise.resolve({ data: {} })) },
  cronJobAPI: { list: vi.fn(() => Promise.resolve({ data: { results: [] } })) },
  permissionsAPI: { list: vi.fn(() => Promise.resolve({ data: [] })) },
}));

import App from '../App';

describe('App Routing Integration', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'mock-token');
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should render App without crashing when authenticated', async () => {
    let container;
    await act(async () => {
      const result = render(React.createElement(App));
      container = result.container;
    });
    expect(container).toBeDefined();
    expect(document.body.children.length).toBeGreaterThan(0);
  });

  it('should not show login form when authenticated', async () => {
    await act(async () => {
      render(React.createElement(App));
    });
    // Wait for auth to resolve and check that login form is NOT present
    // The App redirects "/" to "/dashboard" and auth loads user
    await new Promise(r => setTimeout(r, 1000));
    expect(screen.queryByLabelText('اسم المستخدم')).not.toBeInTheDocument();
  });
});
