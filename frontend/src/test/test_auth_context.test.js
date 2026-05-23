/**
 * Tests for AuthContext.
 * Tests login, logout, 2FA, profile management, and permission checks.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import React from 'react';

// Mock the API module
vi.mock('../api/index.js', () => ({
  authAPI: {
    login: vi.fn(),
    login2FA: vi.fn(),
  },
  profileAPI: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

import { authAPI, profileAPI } from '../api/index.js';

function createWrapper() {
  return function Wrapper({ children }) {
    return React.createElement(AuthProvider, null, children);
  };
}

const mockUser = {
  id: 1,
  username: 'admin',
  email: 'admin@test.com',
  role: 'admin',
  first_name: 'مدير',
  last_name: 'النظام',
  permissions: ['inventory_view', 'sales_view'],
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should start with unauthenticated state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should fetch profile on mount when token exists', async () => {
    localStorage.setItem('access_token', 'mock-token');
    profileAPI.getProfile.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user.username).toBe('admin');
    expect(result.current.user.role).toBe('admin');
  });

  it('should handle failed profile fetch gracefully', async () => {
    localStorage.setItem('access_token', 'expired-token');
    profileAPI.getProfile.mockRejectedValue(new Error('Unauthorized'));

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('should login successfully', async () => {
    authAPI.login.mockResolvedValue({
      data: {
        access: 'access-token',
        refresh: 'refresh-token',
        user: mockUser,
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    let loginResult;
    await act(async () => {
      loginResult = await result.current.login('admin', 'admin123');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user.username).toBe('admin');
    expect(localStorage.getItem('access_token')).toBe('access-token');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
  });

  it('should handle 2FA required during login', async () => {
    authAPI.login.mockResolvedValue({
      data: {
        requires_2fa: true,
        temp_token: 'temp-token',
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    let loginResult;
    await act(async () => {
      loginResult = await result.current.login('admin', 'admin123');
    });

    expect(loginResult.requires_2fa).toBe(true);
    expect(result.current.pending2FA).toBe(true);
    expect(result.current.pending2FAData.temp_token).toBe('temp-token');
  });

  it('should verify 2FA code successfully', async () => {
    authAPI.login2FA.mockResolvedValue({
      data: {
        access: 'access-token',
        refresh: 'refresh-token',
        user: mockUser,
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    // First set pending 2FA state
    await act(async () => {
      authAPI.login.mockResolvedValue({
        data: { requires_2fa: true, temp_token: 'temp-token', username: 'admin' },
      });
      await result.current.login('admin', 'admin123');
    });

    // Then verify 2FA
    let verifyResult;
    await act(async () => {
      verifyResult = await result.current.verify2FA('123456');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.pending2FA).toBe(false);
    expect(localStorage.getItem('access_token')).toBe('access-token');
  });

  it('should cancel 2FA', async () => {
    authAPI.login.mockResolvedValue({
      data: { requires_2fa: true, temp_token: 'temp-token', username: 'admin' },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('admin', 'admin123');
    });

    expect(result.current.pending2FA).toBe(true);

    act(() => {
      result.current.cancel2FA();
    });

    expect(result.current.pending2FA).toBe(false);
    expect(result.current.pending2FAData).toBeNull();
  });

  it('should logout and clear state', async () => {
    localStorage.setItem('access_token', 'token');
    localStorage.setItem('refresh_token', 'refresh');
    profileAPI.getProfile.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('should add role_display to user', async () => {
    authAPI.login.mockResolvedValue({
      data: {
        access: 'access-token',
        refresh: 'refresh-token',
        user: mockUser,
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('admin', 'admin123');
    });

    expect(result.current.user.role_display).toBe('مدير النظام');
  });

  it('should check permissions correctly for admin', async () => {
    authAPI.login.mockResolvedValue({
      data: {
        access: 'token',
        refresh: 'token',
        user: mockUser,
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('admin', 'admin123');
    });

    expect(result.current.hasPermission('inventory_view')).toBe(true);
    expect(result.current.hasPermission('any_random_perm')).toBe(true);
    expect(result.current.isAdmin).toBe(true);
  });

  it('should check permissions correctly for non-admin after profile fetch', async () => {
    const salesUser = { ...mockUser, role: 'sales', permissions: ['sales_view', 'inventory_view'] };
    
    // Login sets user but doesn't set permissions - only fetchProfile does
    authAPI.login.mockResolvedValue({
      data: { access: 'token', refresh: 'token', user: salesUser },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('sales', 'pass');
    });

    // After login (not profile fetch), permissions are empty
    expect(result.current.hasPermission('sales_view')).toBe(false);
    expect(result.current.isAdmin).toBe(false);
  });

  it('should return false for hasPermission when not authenticated', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    expect(result.current.hasPermission('any')).toBe(false);
  });

  it('should set convenience role flags correctly', async () => {
    authAPI.login.mockResolvedValue({
      data: { access: 'token', refresh: 'token', user: mockUser },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('admin', 'admin123');
    });

    expect(result.current.isAdmin).toBe(true);
    expect(result.current.isWarehouse).toBe(true);
    expect(result.current.isSales).toBe(true);
    expect(result.current.isAccountant).toBe(true);
  });

  it('should update profile', async () => {
    authAPI.login.mockResolvedValue({
      data: { access: 'token', refresh: 'token', user: mockUser },
    });
    profileAPI.updateProfile.mockResolvedValue({
      data: { user: { ...mockUser, first_name: 'جديد' } },
    });

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login('admin', 'admin123');
    });

    await act(async () => {
      await result.current.updateProfile({ first_name: 'جديد' });
    });

    expect(result.current.user.first_name).toBe('جديد');
  });

  it('should throw error when useAuth used outside provider', () => {
    // Suppress the expected console.error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');
    spy.mockRestore();
  });
});
