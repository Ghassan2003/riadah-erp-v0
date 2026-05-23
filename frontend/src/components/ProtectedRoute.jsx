/**
 * مكون حماية المسارات - يتحقق من المصادقة والدور والصلاحيات.
 * إذا لم يكن المستخدم مصرحاً له، يعرض صفحة "وصول مرفوض" بدل التوجيه الصامت.
 * يدعم:
 * - التحقق من المصادقة (isAuthenticated)
 * - التحقق من الدور (roles)
 * - التحقق من الصلاحية التفصيلية (permission)
 */

import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import LoadingSpinner from './LoadingSpinner';
import { ShieldX, Home, ArrowRight } from 'lucide-react';

// خريطة الصفحات الرئيسية لكل دور
const ROLE_HOME_MAP = {
  admin: '/dashboard',
  sales: '/orders',
  accountant: '/accounts',
  hr: '/employees',
  purchasing: '/purchases',
  project_manager: '/projects',
};

// تسميات الأدوار بالعربية
const ROLE_LABELS = {
  admin: 'مدير النظام',
  sales: 'موظف المبيعات',
  accountant: 'المحاسب',
  hr: 'موظف الموارد البشرية',
  purchasing: 'موظف المشتريات',
  project_manager: 'مدير المشاريع',
};

export default function ProtectedRoute({ children, roles = [], permission = null }) {
  const { isAuthenticated, loading, user, hasPermission } = useAuth();
  const location = useLocation();

  // 1. جاري التحميل
  if (loading) {
    return <LoadingSpinner />;
  }

  // 2. غير مصادق - إعادة لتسجيل الدخول مع حفظ المسار المطلوب
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // 3. التحقق من الدور
  if (roles.length > 0 && !roles.includes(user?.role)) {
    return (
      <AccessDeniedInline
        userRole={user?.role}
        homePath={ROLE_HOME_MAP[user?.role] || '/dashboard'}
      />
    );
  }

  // 4. التحقق من الصلاحية التفصيلية
  if (permission && !hasPermission(permission)) {
    return (
      <AccessDeniedInline
        userRole={user?.role}
        homePath={ROLE_HOME_MAP[user?.role] || '/dashboard'}
        requiredPermission={permission}
      />
    );
  }

  // 5. كل شيء على ما يرام - عرض المحتوى
  return children;
}

/**
 * مكون داخلي يعرض رسالة "وصول مرفوض" مباشرة بدون إعادة توجيه.
 * يوضح للمستخدم سبب الرفض ويوفر زر العودة للواجهة الرئيسية الخاصة بدوره.
 */
function AccessDeniedInline({ userRole, homePath, requiredPermission }) {
  const navigate = useNavigate();
  const { locale } = useI18n();

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        {/* أيقونة التحذير */}
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-red-100 dark:bg-red-900/30 text-red-500 mb-6 shadow-lg">
          <ShieldX className="w-10 h-10" />
        </div>

        <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
          {locale === 'ar' ? 'غير مصرح بالوصول' : 'Access Denied'}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {locale === 'ar'
            ? 'ليس لديك صلاحية للوصول إلى هذه الصفحة'
            : 'You do not have permission to access this page'}
        </p>

        {/* معلومات الدور */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-6 border border-gray-100 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {locale === 'ar' ? 'دورك الحالي:' : 'Your role:'}{' '}
            <span className="font-semibold text-gray-800 dark:text-white">
              {ROLE_LABELS[userRole] || userRole}
            </span>
          </p>
          {requiredPermission && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {locale === 'ar' ? 'الصلاحية المطلوبة:' : 'Required permission:'}{' '}
              <span className="font-mono bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-2 py-0.5 rounded text-xs">
                {requiredPermission}
              </span>
            </p>
          )}
        </div>

        {/* نصيحة */}
        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl mb-6">
          <p className="text-sm text-amber-700 dark:text-amber-400">
            {locale === 'ar'
              ? 'إذا كنت تعتقد أن هذا خطأ، تواصل مع مدير النظام لطلب الصلاحية المناسبة.'
              : 'If you believe this is an error, contact your system administrator.'}
          </p>
        </div>

        {/* أزرار */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate(homePath, { replace: true })}
            className="flex items-center gap-2 bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 text-white font-medium py-2.5 px-5 rounded-xl transition-colors shadow-lg shadow-accent-500/20"
          >
            <Home className="w-4 h-4" />
            {locale === 'ar' ? 'الواجهة الرئيسية' : 'Go Home'}
          </button>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium py-2.5 px-5 rounded-xl transition-colors"
          >
            <ArrowRight className="w-4 h-4" />
            {locale === 'ar' ? 'رجوع' : 'Back'}
          </button>
        </div>
      </div>
    </div>
  );
}
