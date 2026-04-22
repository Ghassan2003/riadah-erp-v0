/**
 * StatusBadge - شارة حالة قابلة لإعادة الاستخدام.
 * يدعم: خريطة حالات مخصصة، الوضع الداكن، ألوان متعددة.
 */

import { useI18n } from '../i18n/I18nContext';

const colorStyles = {
  green:  'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
  red:    'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  yellow: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
  blue:   'bg-riadah-100 dark:bg-riadah-900/30 text-riadah-700 dark:text-accent-400',
  gray:   'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
  orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
};

const defaultStatusMap = {
  active:     { label: 'نشط',         color: 'green' },
  inactive:   { label: 'غير نشط',     color: 'gray' },
  pending:    { label: 'معلق',        color: 'yellow' },
  approved:   { label: 'موافق عليه',   color: 'green' },
  rejected:   { label: 'مرفوض',       color: 'red' },
  completed:  { label: 'مكتمل',       color: 'blue' },
  cancelled:  { label: 'ملغي',        color: 'red' },
  processing: { label: 'قيد التنفيذ',  color: 'orange' },
  draft:      { label: 'مسودة',       color: 'gray' },
  shipped:    { label: 'مُرسل',       color: 'blue' },
  posted:     { label: 'مرحّل',       color: 'green' },
  on_hold:    { label: 'معلق',        color: 'yellow' },
  not_started:{ label: 'لم يبدأ',     color: 'gray' },
  in_progress:{ label: 'قيد التنفيذ',  color: 'blue' },
};

export default function StatusBadge({ status, statusMap }) {
  const { t } = useI18n();
  const map = statusMap || defaultStatusMap;
  const statusInfo = map[status];

  if (!statusInfo) {
    return (
      <span className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        ${colorStyles.gray}
      `}>
        {status || '-'}
      </span>
    );
  }

  const colorClass = colorStyles[statusInfo.color] || colorStyles.gray;

  return (
    <span className={`
      inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
      ${colorClass}
      transition-colors duration-200
    `}>
      {statusInfo.label}
    </span>
  );
}
