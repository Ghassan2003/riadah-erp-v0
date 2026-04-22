/**
 * ConfirmDialog - حوار تأكيد قابلة لإعادة الاستخدام.
 * يدعم: الأنواع (خطر/تحذير/معلومات)، حالة التحميل، الوضع الداكن.
 */

import { AlertTriangle, Info, Loader2 } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import Modal from './Modal';

const typeStyles = {
  danger: {
    icon: AlertTriangle,
    iconBg: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600 dark:text-red-400',
    btnBg: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-amber-100 dark:bg-amber-900/30',
    iconColor: 'text-amber-600 dark:text-amber-400',
    btnBg: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500',
  },
  info: {
    icon: Info,
    iconBg: 'bg-riadah-100 dark:bg-riadah-900/30',
    iconColor: 'text-accent-500 dark:text-accent-400',
    btnBg: 'bg-riadah-500 hover:bg-riadah-600 focus:ring-accent-500',
  },
};

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText,
  cancelText,
  type = 'danger',
  loading = false,
}) {
  const { t, isRTL } = useI18n();
  const styles = typeStyles[type] || typeStyles.danger;
  const TypeIcon = styles.icon;

  const resolvedTitle = title || t('confirmAction');
  const resolvedMessage = message || t('thisActionCannot');
  const resolvedConfirmText = confirmText || t('deleteBtn');
  const resolvedCancelText = cancelText || t('cancelBtn');

  return (
    <Modal
      isOpen={isOpen}
      onClose={loading ? undefined : onClose}
      title={resolvedTitle}
      size="sm"
      footer={
        <>
          <button
            onClick={onClose}
            disabled={loading}
            className="
              px-4 py-2 rounded-lg text-sm font-medium
              text-gray-700 dark:text-gray-300
              bg-gray-100 dark:bg-gray-700
              hover:bg-gray-200 dark:hover:bg-gray-600
              transition-colors disabled:opacity-50
            "
          >
            {resolvedCancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium text-white
              focus:outline-none focus:ring-2 focus:ring-offset-2
              dark:focus:ring-offset-gray-800
              transition-colors disabled:opacity-50
              ${styles.btnBg}
            `}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                {t('loading')}
              </span>
            ) : (
              resolvedConfirmText
            )}
          </button>
        </>
      }
    >
      <div className="flex flex-col items-center text-center py-2">
        <div className={`w-14 h-14 rounded-full ${styles.iconBg} flex items-center justify-center mb-4`}>
          <TypeIcon className={`w-7 h-7 ${styles.iconColor}`} />
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          {resolvedMessage}
        </p>
      </div>
    </Modal>
  );
}
