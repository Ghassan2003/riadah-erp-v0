/**
 * PageHeader - مكون رأس الصفحة القابل لإعادة الاستخدام.
 * يدعم: الأيقونة، الوصف، الإجراءات، مسار التنقل، الوضع الداكن، RTL.
 */

import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';

export default function PageHeader({
  title,
  description,
  icon: Icon,
  actions,
  breadcrumbs = [],
}) {
  const { t, isRTL } = useI18n();

  return (
    <div className="animate-fade-in-down">
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <nav className="mb-3" aria-label="Breadcrumb">
          <ol className="flex items-center gap-1.5 text-sm">
            <li>
              <Link
                to="/dashboard"
                className="text-gray-400 dark:text-gray-500 hover:text-accent-500 dark:hover:text-accent-400 transition-colors"
              >
                {t('home')}
              </Link>
            </li>
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center gap-1.5">
                <span className="text-gray-300 dark:text-gray-600">/</span>
                {index === breadcrumbs.length - 1 ? (
                  <span className="text-gray-600 dark:text-gray-300 font-medium">
                    {crumb.label}
                  </span>
                ) : (
                  <Link
                    to={crumb.path}
                    className="text-gray-400 dark:text-gray-500 hover:text-accent-500 dark:hover:text-accent-400 transition-colors"
                  >
                    {crumb.label}
                  </Link>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Header content */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {Icon && (
            <div className="w-12 h-12 rounded-xl bg-riadah-100 dark:bg-riadah-900/30 flex items-center justify-center flex-shrink-0">
              <Icon className="w-6 h-6 text-accent-500 dark:text-accent-400" />
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {title}
            </h1>
            {description && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {description}
              </p>
            )}
          </div>
        </div>

        {actions && (
          <div className={`flex items-center gap-3 flex-shrink-0 ${isRTL ? 'sm:mr-auto' : 'sm:ml-auto'}`}>
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
