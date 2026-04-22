/**
 * I18nContext - نظام اللغات (عربي/إنجليزي).
 * يدعم التبديل مع حفظ التفضيل وتبديل اتجاه الصفحة (RTL/LTR).
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import translations from './translations';

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [locale, setLocale] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('erp_locale') || 'ar';
    }
    return 'ar';
  });

  // Apply direction and lang attribute whenever locale changes
  useEffect(() => {
    const html = document.documentElement;
    if (locale === 'ar') {
      html.setAttribute('dir', 'rtl');
      html.setAttribute('lang', 'ar');
    } else {
      html.setAttribute('dir', 'ltr');
      html.setAttribute('lang', 'en');
    }
    localStorage.setItem('erp_locale', locale);
  }, [locale]);

  const toggleLocale = useCallback(() => {
    setLocale(prev => prev === 'ar' ? 'en' : 'ar');
  }, []);

  // Translation function with dot notation support and fallback
  const t = useCallback((key, fallback) => {
    const value = translations[locale]?.[key];
    if (value !== undefined) return value;
    // Try fallback locale
    const fallbackLocale = locale === 'ar' ? 'en' : 'ar';
    const fallbackValue = translations[fallbackLocale]?.[key];
    if (fallbackValue !== undefined) return fallbackValue;
    return fallback || key;
  }, [locale]);

  const isRTL = locale === 'ar';
  const isArabic = locale === 'ar';

  return (
    <I18nContext.Provider value={{ locale, setLocale, toggleLocale, t, isRTL, isArabic }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used within I18nProvider');
  return context;
}

export default I18nContext;
