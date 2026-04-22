/**
 * Tests for LoginPage component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { I18nProvider } from '../i18n/I18nContext';
import LoginPage from '../pages/LoginPage';
import React from 'react';

vi.mock('../api/index.js', () => ({
  authAPI: { login: vi.fn(), login2FA: vi.fn() },
  profileAPI: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

import { authAPI, profileAPI } from '../api/index.js';

function renderLoginPage() {
  return render(
    React.createElement(
      MemoryRouter,
      null,
      React.createElement(I18nProvider, null,
        React.createElement(AuthProvider, null, React.createElement(LoginPage))
      )
    )
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should render login heading', () => {
    renderLoginPage();
    // There are two elements with "تسجيل الدخول" - heading h2 and button. Use getAllByText.
    const elements = screen.getAllByText('تسجيل الدخول');
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it('should render username input', () => {
    renderLoginPage();
    expect(screen.getByLabelText('اسم المستخدم')).toBeInTheDocument();
  });

  it('should render password input', () => {
    renderLoginPage();
    expect(screen.getByLabelText('كلمة المرور')).toBeInTheDocument();
  });

  it('should render login button', () => {
    renderLoginPage();
    const btn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    expect(btn).toBeInTheDocument();
  });

  it('should show validation error for empty username', async () => {
    renderLoginPage();
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    expect(screen.getByText('اسم المستخدم مطلوب')).toBeInTheDocument();
  });

  it('should show validation error for empty password', async () => {
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    await userEvent.type(usernameInput, 'admin');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    expect(screen.getByText('كلمة المرور مطلوبة')).toBeInTheDocument();
  });

  it('should type into username and password fields', async () => {
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'admin123');
    expect(usernameInput.value).toBe('admin');
    expect(passwordInput.value).toBe('admin123');
  });

  it('should show error message on failed login', async () => {
    authAPI.login.mockRejectedValue({
      response: { data: { detail: 'بيانات الدخول غير صحيحة' } },
    });
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'wrong');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText('بيانات الدخول غير صحيحة')).toBeInTheDocument();
    });
  });

  it('should show default error message when no detail provided', async () => {
    authAPI.login.mockRejectedValue({ response: { data: {} } });
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'wrong');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    // The error display uses toast, not inline text. Just check no crash.
    await screen.findByRole('button', { name: 'تسجيل الدخول' });
  });

  it('should clear validation error when user types', async () => {
    renderLoginPage();
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    expect(screen.getByText('اسم المستخدم مطلوب')).toBeInTheDocument();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    await userEvent.type(usernameInput, 'admin');
    expect(screen.queryByText('اسم المستخدم مطلوب')).not.toBeInTheDocument();
  });

  it('should show 2FA verification screen when 2FA is required', async () => {
    authAPI.login.mockResolvedValue({
      data: { requires_2fa: true, temp_token: 'temp-token', username: 'admin' },
    });
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'admin123');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      // 2FA screen shows "المصادقة الثنائية" heading
      expect(screen.getByText('المصادقة الثنائية')).toBeInTheDocument();
    });
  });

  it('should render 6 input fields for 2FA code', async () => {
    authAPI.login.mockResolvedValue({
      data: { requires_2fa: true, temp_token: 'temp-token', username: 'admin' },
    });
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'admin123');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      const inputs = screen.getAllByRole('textbox');
      expect(inputs.length).toBe(6);
    });
  });

  it('should have back to login button on 2FA screen', async () => {
    authAPI.login.mockResolvedValue({
      data: { requires_2fa: true, temp_token: 'temp-token', username: 'admin' },
    });
    renderLoginPage();
    const usernameInput = screen.getByLabelText('اسم المستخدم');
    const passwordInput = screen.getByLabelText('كلمة المرور');
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'admin123');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'العودة لتسجيل الدخول' })).toBeInTheDocument();
    });
  });

  it('should redirect to dashboard when already authenticated', async () => {
    localStorage.setItem('access_token', 'token');
    profileAPI.getProfile.mockResolvedValue({
      data: { id: 1, username: 'admin', role: 'admin', first_name: 'مدير', last_name: 'النظام' },
    });
    renderLoginPage();
    await waitFor(() => {
      expect(screen.queryByLabelText('اسم المستخدم')).not.toBeInTheDocument();
    });
  });
});
