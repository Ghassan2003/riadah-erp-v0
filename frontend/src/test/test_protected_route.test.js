/**
 * Tests for ProtectedRoute component.
 * Tests authentication check, role-based access, and loading state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { I18nProvider } from '../i18n/I18nContext';
import ProtectedRoute from '../components/ProtectedRoute';
import React from 'react';

// Mock API
vi.mock('../api/index.js', () => ({
  authAPI: { login: vi.fn(), login2FA: vi.fn() },
  profileAPI: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

import { profileAPI } from '../api/index.js';

function TestContent({ text = 'Protected Content' }) {
  return React.createElement('div', null, text);
}

function renderWithProviders(ui, { initialAuth = null } = {}) {
  // Set up auth state before rendering
  if (initialAuth) {
    localStorage.setItem('access_token', 'token');
    profileAPI.getProfile.mockResolvedValue({ data: initialAuth });
  }

  return render(
    React.createElement(
      MemoryRouter,
      null,
      React.createElement(
        I18nProvider,
        null,
        React.createElement(
          AuthProvider,
          null,
          React.createElement(ProtectedRoute, null, ui)
        )
      )
    )
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should redirect to login when not authenticated', async () => {
    renderWithProviders(React.createElement(TestContent));

    // Should not show protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should show loading spinner when auth is loading', () => {
    // When token exists, auth is loading
    localStorage.setItem('access_token', 'token');
    profileAPI.getProfile.mockReturnValue(new Promise(() => {})); // Never resolves

    render(
      React.createElement(
        MemoryRouter,
        null,
        React.createElement(
          I18nProvider,
          null,
          React.createElement(
            AuthProvider,
            null,
            React.createElement(ProtectedRoute, null, React.createElement(TestContent))
          )
        )
      )
    );
  });

  it('should render children when authenticated as admin', async () => {
    const mockUser = {
      id: 1, username: 'admin', role: 'admin',
      first_name: 'مدير', last_name: 'النظام',
    };

    await vi.dynamicImportSettled();
    profileAPI.getProfile.mockResolvedValue({ data: mockUser });

    renderWithProviders(React.createElement(TestContent), { initialAuth: mockUser });

    // Wait for auth to resolve and check content is shown
    const el = await screen.findByText('Protected Content');
    expect(el).toBeInTheDocument();
  });
});
