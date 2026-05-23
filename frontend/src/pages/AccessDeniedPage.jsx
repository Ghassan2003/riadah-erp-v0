/**
 * صفحة "وصول مرفوض" - تظهر عندما يحاول المستخدم الوصول لصفحة ليس لديه صلاحية لها.
 * تعرض الدور الحالي للمستخدم والصفحة المطلوبة وتوفر زر العودة للواجهة الرئيسية.
 */

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import {
  ShieldX, ArrowRight, Home, LayoutDashboard, UserCog, Package,
  ShoppingCart, BookOpen, UserCog as UsersIcon, ClipboardList, Truck,
  FolderKanban, Calculator, Store, Warehouse, Building2, Wrench
} from 'lucide-react';

// خريطة الأدوار مع الواجهة الرئيسية لكل دور
export const ROLE_HOME_MAP = {
  admin: '/dashboard',
  warehouse: '/warehouse-dashboard',
  sales: '/orders',
  accountant: '/accounts',
  hr: '/employees',
  purchasing: '/purchases',
  project_manager: '/projects',
};

// أيقونة لكل دور
const ROLE_ICONS = {
  admin: LayoutDashboard,
  warehouse: Warehouse,
  sales: ShoppingCart,
  accountant: BookOpen,
  hr: UserCog,
  purchasing: Truck,
  project_manager: FolderKanban,
};

// تسميات الأقسام لكل دور
const ROLE_SECTIONS = {
  admin: 'إدارة النظام - جميع الأقسام متاحة',
  warehouse: 'إدارة المخازن - المنتجات والمستودعات والتصنيع',
  sales: 'المبيعات - الطلبات والعملاء ونقاط البيع',
  accountant: 'المحاسبة - الحسابات والقيود والتقارير المالية',
  hr: 'الموارد البشرية - الموظفون والحضور والرواتب',
  purchasing: 'المشتريات - الموردين وأوامر الشراء',
  project_manager: 'إدارة المشاريع - المشاريع والعقود والميزانيات',
};

export default function AccessDeniedPage() {
  const { user } = useAuth();
  const { t, locale } = useI18n();
  const navigate = useNavigate();

  const role = user?.role || 'unknown';
  const RoleIcon = ROLE_ICONS[role] || ShieldX;
  const homePath = ROLE_HOME_MAP[role] || '/dashboard';
  const sectionInfo = ROLE_SECTIONS[role] || '';

  const goHome = () => {
    navigate(homePath, { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* أيقونة التحذير */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-red-100 dark:bg-red-900/30 text-red-500 mb-6 shadow-lg">
            <ShieldX className="w-12 h-12" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            {locale === 'ar' ? 'غير مصرح بالوصول' : 'Access Denied'}
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            {locale === 'ar'
              ? 'ليس لديك صلاحية للوصول إلى هذه الصفحة'
              : 'You do not have permission to access this page'}
          </p>
        </div>

        {/* بطاقة معلومات الدور */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 mb-6 border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            {locale === 'ar' ? 'صلاحياتك الحالية' : 'Your Current Permissions'}
          </h3>

          <div className="flex items-center gap-4 mb-4 p-3 bg-riadah-50 dark:bg-riadah-900/20 rounded-xl">
            <div className="w-12 h-12 rounded-xl bg-riadah-500/10 dark:bg-riadah-500/20 flex items-center justify-center">
              <RoleIcon className="w-6 h-6 text-riadah-600 dark:text-riadah-400" />
            </div>
            <div>
              <p className="font-semibold text-gray-800 dark:text-white">
                {user?.role_display || user?.username}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {sectionInfo}
              </p>
            </div>
          </div>

          {/* نصيحة */}
          <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
            <p className="text-sm text-amber-700 dark:text-amber-400">
              {locale === 'ar'
                ? 'إذا كنت تعتقد أن هذا خطأ، تواصل مع مدير النظام لطلب الصلاحية المناسبة.'
                : 'If you believe this is an error, contact your system administrator to request the appropriate permission.'}
            </p>
          </div>
        </div>

        {/* أزرار الإجراء */}
        <div className="flex gap-3">
          <button
            onClick={goHome}
            className="flex-1 flex items-center justify-center gap-2 bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 text-white font-medium py-3 px-4 rounded-xl transition-colors shadow-lg shadow-accent-500/20"
          >
            <Home className="w-5 h-5" />
            {locale === 'ar' ? 'الذهاب للواجهة الرئيسية' : 'Go to Home'}
          </button>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center gap-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium py-3 px-4 rounded-xl transition-colors"
          >
            <ArrowRight className="w-5 h-5" />
            {locale === 'ar' ? 'رجوع' : 'Back'}
          </button>
        </div>

        {/* معلومة للمسؤول */}
        {role === 'admin' && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl text-center">
            <p className="text-sm text-blue-700 dark:text-blue-400">
              {locale === 'ar'
                ? 'بصفتك مدير النظام، يمكنك إدارة الصلاحيات من صفحة الصلاحيات.'
                : 'As system admin, you can manage permissions from the Permissions page.'}
            </p>
            <button
              onClick={() => navigate('/permissions')}
              className="mt-2 text-sm text-accent-500 hover:text-accent-600 font-medium"
            >
              {locale === 'ar' ? 'إدارة الصلاحيات' : 'Manage Permissions'} →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
