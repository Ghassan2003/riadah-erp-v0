/**
 * EmptyState - عرض حالة فارغة قابلة لإعادة الاستخدام.
 * يدعم: الأيقونة، الوضع الداكن، زر الإجراء.
 */

import { useI18n } from '../i18n/I18nContext';

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}) {
  const { t } = useI18n();

  const displayTitle = title || t('emptyTitle');
  const displayDescription = description || t('emptyDescription');

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 animate-fade-in">
      {Icon && (
        <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-6">
          <Icon className="w-10 h-10 text-gray-300 dark:text-gray-600" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-gray-500 dark:text-gray-400 mb-2">
        {displayTitle}
      </h3>
      <p className="text-sm text-gray-400 dark:text-gray-500 text-center max-w-sm mb-6">
        {displayDescription}
      </p>
      {action && (
        <div>{action}</div>
      )}
    </div>
  );
}
