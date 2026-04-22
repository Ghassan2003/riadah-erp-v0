/**
 * StatCard - بطاقة إحصائية KPI قابلة لإعادة الاستخدام.
 * يدعم: الألوان، اتجاه التغير، الوضع الداكن، RTL، النقر.
 */

import { TrendingUp, TrendingDown } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

const colorMap = {
  blue:    { bg: 'bg-riadah-100 dark:bg-riadah-900/30',    icon: 'text-accent-500 dark:text-accent-400' },
  green:   { bg: 'bg-emerald-100 dark:bg-emerald-900/30', icon: 'text-emerald-600 dark:text-emerald-400' },
  red:     { bg: 'bg-red-100 dark:bg-red-900/30',       icon: 'text-red-600 dark:text-red-400' },
  yellow:  { bg: 'bg-amber-100 dark:bg-amber-900/30',   icon: 'text-amber-600 dark:text-amber-400' },
  purple:  { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: 'text-purple-600 dark:text-purple-400' },
  indigo:  { bg: 'bg-indigo-100 dark:bg-indigo-900/30', icon: 'text-indigo-600 dark:text-indigo-400' },
  orange:  { bg: 'bg-orange-100 dark:bg-orange-900/30', icon: 'text-orange-600 dark:text-orange-400' },
  teal:    { bg: 'bg-teal-100 dark:bg-teal-900/30',     icon: 'text-teal-600 dark:text-teal-400' },
};

export default function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  color = 'blue',
  onClick,
}) {
  const { isRTL } = useI18n();
  const colors = colorMap[color] || colorMap.blue;

  return (
    <div
      onClick={onClick}
      className={`
        bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700
        p-5 card-hover transition-colors duration-200
        ${onClick ? 'cursor-pointer' : ''}
      `}
    >
      <div className="flex items-center gap-4">
        {/* Icon */}
        {Icon && (
          <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center flex-shrink-0`}>
            <Icon className={`w-6 h-6 ${colors.icon}`} />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
            {value}
          </p>

          {/* Trend */}
          {trend != null && (
            <div className="flex items-center gap-1.5 mt-1">
              {trend >= 0 ? (
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )}
              <span className={`text-xs font-medium ${trend >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
              {trendLabel && (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {trendLabel}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
