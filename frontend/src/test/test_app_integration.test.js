/**
 * Integration tests for the App component.
 * Tests basic rendering and routing behavior.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
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
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
  dashboardAPI: { getStats: vi.fn(() => Promise.resolve({ data: {} })) },
  notificationsAPI: {
    list: vi.fn(() => Promise.resolve({ data: { results: [] } })),
    unreadCount: vi.fn(() => Promise.resolve({ data: { count: 0 } })),
  },
}));

import { profileAPI } from '../api/index.js';
import App from '../App';

describe('App Integration', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    profileAPI.getProfile.mockRejectedValue(new Error('Not authenticated'));
    // Set initial URL for BrowserRouter
    window.history.pushState({}, '', '/login');
  });

  it('should render App component without crashing', async () => {
    let container;
    await act(async () => {
      const result = render(React.createElement(App));
      container = result.container;
    });
    expect(container).toBeDefined();
    expect(document.body.children.length).toBeGreaterThan(0);
  });

  it('should render Toaster component', async () => {
    await act(async () => {
      render(React.createElement(App));
    });
    // Toaster renders a div with data-rht-toaster attribute
    const toaster = document.querySelector('[data-rht-toaster]');
    expect(toaster).toBeInTheDocument();
  });
});
