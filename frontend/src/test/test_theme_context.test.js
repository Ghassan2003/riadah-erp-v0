/**
 * Tests for ThemeContext.
 * Tests theme toggling, localStorage persistence, and DOM class updates.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../context/ThemeContext';
import React from 'react';

function createWrapper() {
  return function Wrapper({ children }) {
    return React.createElement(ThemeProvider, null, children);
  };
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.remove('light');
  });

  it('should default to light theme', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
  });

  it('should read saved theme from localStorage', () => {
    localStorage.setItem('erp_theme', 'dark');
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('should toggle theme from light to dark', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleTheme();
    });
    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('should toggle theme from dark to light', () => {
    localStorage.setItem('erp_theme', 'dark');
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleTheme();
    });
    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
  });

  it('should save theme to localStorage on toggle', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleTheme();
    });
    expect(localStorage.getItem('erp_theme')).toBe('dark');
  });

  it('should add dark class to document when dark theme', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleTheme();
    });
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('should remove dark class when switching to light', () => {
    localStorage.setItem('erp_theme', 'dark');
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.toggleTheme();
    });
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('should provide setTheme function', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.setTheme('dark');
    });
    expect(result.current.theme).toBe('dark');
  });

  it('should persist setTheme change to localStorage', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    act(() => {
      result.current.setTheme('dark');
    });
    expect(localStorage.getItem('erp_theme')).toBe('dark');
  });

  it('should toggle theme multiple times correctly', () => {
    const { result } = renderHook(() => useTheme(), { wrapper: createWrapper() });
    // light -> dark
    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('dark');
    // dark -> light
    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('light');
    // light -> dark
    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('dark');
  });
});
