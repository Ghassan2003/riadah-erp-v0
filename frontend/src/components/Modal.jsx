/**
 * Modal - مكون نافذة منبثقة قابلة لإعادة الاستخدام.
 * يدعم: الأحجام، الوضع الداكن، RTL، الإغلاق بالنقر خارجاً، مفتاح ESC، الرسم البواب.
 */

import { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  footer,
  showClose = true,
}) {
  const { isRTL, t } = useI18n();

  // Close on ESC key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose?.();
    }
  }, [onClose]);

  // Bind ESC listener and prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {/* Glass morphism backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div
        className={`
          relative w-full ${sizeClasses[size] || sizeClasses.md}
          bg-white dark:bg-gray-800
          rounded-2xl shadow-2xl
          border border-gray-200 dark:border-gray-700
          animate-modal-enter
          max-h-[90vh] flex flex-col
          transition-colors duration-200
        `}
      >
        {/* Header */}
        {(title || showClose) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
              {title}
            </h2>
            {showClose && (
              <button
                onClick={onClose}
                className={`
                  p-1.5 rounded-lg text-gray-400 hover:text-gray-600
                  dark:text-gray-500 dark:hover:text-gray-300
                  hover:bg-gray-100 dark:hover:bg-gray-700
                  transition-colors min-w-[36px] min-h-[36px] flex items-center justify-center
                  ${!title ? 'ml-auto' : ''}
                `}
                aria-label={t('close')}
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-2xl">
            <div className={`flex items-center gap-3 ${isRTL ? 'justify-start' : 'justify-end'}`}>
              {footer}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
