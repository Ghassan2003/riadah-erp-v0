/**
 * Breadcrumbs - مكون مسار التنقل القابل لإعادة الاستخدام.
 * يدعم: RTL، الوضع الداكن، الفاصل التلقائي حسب الاتجاه.
 */

import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export default function Breadcrumbs({ items = [] }) {
  const { isRTL } = useI18n();
  const SeparatorIcon = isRTL ? ChevronLeft : ChevronRight;

  if (items.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="animate-fade-in">
      <ol className="flex items-center gap-1.5 text-sm flex-wrap">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center gap-1.5">
              {index > 0 && (
                <SeparatorIcon className="w-3.5 h-3.5 text-gray-300 dark:text-gray-600 flex-shrink-0" />
              )}
              {isLast ? (
                <span className="text-gray-800 dark:text-gray-200 font-medium truncate">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.path}
                  className="text-gray-400 dark:text-gray-500 hover:text-accent-500 dark:hover:text-accent-400 transition-colors truncate"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
