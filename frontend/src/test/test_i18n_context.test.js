/**
 * Tests for I18nContext.
 * Tests locale toggling, translation function, RTL/LTR, and persistence.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { I18nProvider, useI18n } from '../i18n/I18nContext';
import React from 'react';

function createWrapper() {
  return function Wrapper({ children }) {
    return React.createElement(I18nProvider, null, children);
  };
}

describe('I18nContext', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('dir');
    document.documentElement.removeAttribute('lang');
  });

  it('should default to Arabic locale', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.locale).toBe('ar');
  });

  it('should read saved locale from localStorage', () => {
    localStorage.setItem('erp_locale', 'en');
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.locale).toBe('en');
  });

  it('should toggle locale from ar to en', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleLocale();
    });
    expect(result.current.locale).toBe('en');
  });

  it('should toggle locale from en to ar', () => {
    localStorage.setItem('erp_locale', 'en');
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleLocale();
    });
    expect(result.current.locale).toBe('ar');
  });

  it('should set RTL direction for Arabic', () => {
    renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(document.documentElement.getAttribute('dir')).toBe('rtl');
    expect(document.documentElement.getAttribute('lang')).toBe('ar');
  });

  it('should set LTR direction for English', () => {
    localStorage.setItem('erp_locale', 'en');
    renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(document.documentElement.getAttribute('dir')).toBe('ltr');
    expect(document.documentElement.getAttribute('lang')).toBe('en');
  });

  it('should set isRTL correctly', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.isRTL).toBe(true);
    expect(result.current.isArabic).toBe(true);
  });

  it('should set isRTL to false for English', () => {
    localStorage.setItem('erp_locale', 'en');
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.isRTL).toBe(false);
    expect(result.current.isArabic).toBe(false);
  });

  it('should translate keys in Arabic', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    const translation = result.current.t('login');
    expect(translation).toBeDefined();
    expect(typeof translation).toBe('string');
    expect(translation.length).toBeGreaterThan(0);
  });

  it('should translate keys in English', () => {
    localStorage.setItem('erp_locale', 'en');
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    const translation = result.current.t('login');
    expect(translation).toBeDefined();
    expect(typeof translation).toBe('string');
  });

  it('should return fallback for unknown keys', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    const translation = result.current.t('unknown_key_xyz');
    expect(translation).toBe('unknown_key_xyz');
  });

  it('should return custom fallback when provided', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    const translation = result.current.t('unknown_key', 'Default Value');
    expect(translation).toBe('Default Value');
  });

  it('should save locale to localStorage on toggle', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleLocale();
    });
    expect(localStorage.getItem('erp_locale')).toBe('en');
  });

  it('should provide setLocale function', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    act(() => {
      result.current.setLocale('en');
    });
    expect(result.current.locale).toBe('en');
  });

  it('should update direction when locale changes', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(document.documentElement.getAttribute('dir')).toBe('rtl');
    act(() => {
      result.current.setLocale('en');
    });
    expect(document.documentElement.getAttribute('dir')).toBe('ltr');
  });

  it('should translate dashboard key', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.t('dashboard')).toBeDefined();
  });

  it('should translate products key', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.t('products')).toBeDefined();
  });

  it('should translate loginTitle key', () => {
    const { result } = renderHook(() => useI18n(), { wrapper: createWrapper() });
    expect(result.current.t('loginTitle')).toBeDefined();
  });
});
