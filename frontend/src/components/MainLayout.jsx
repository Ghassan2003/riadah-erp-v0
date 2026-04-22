/**
 * Main application layout with sidebar, header, theme toggle, language switcher.
 * Supports dark/light mode, RTL/LTR, and smooth animations.
 */

import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useI18n } from '../i18n/I18nContext';
import {
  LayoutDashboard, User, LogOut, Menu, X, Users, Shield,
  Package, ShoppingCart, UsersRound, BookOpen, FileText,
  BarChart3, UserCog, ClipboardList, PieChart, Truck,
  FolderOpen, FolderKanban, Bell, BellOff, Check,
  ClipboardCheck, FileSpreadsheet, Database, Bug, Settings,
  Clock, Sun, Moon, Languages, ChevronDown, Video,
  Wallet, Receipt, Store, Warehouse as WarehouseIcon, Building2, ScrollText, Landmark, ExternalLink,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { notificationsAPI } from '../api';
import { useWebSocket } from '../hooks/useWebSocket';

export default function MainLayout() {
  const { user, logout, hasPermission } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const { t, locale, toggleLocale, isRTL } = useI18n();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [mounted, setMounted] = useState(false);
  const location = useLocation();
  const { isConnected, lastMessage } = useWebSocket('notifications/');

  // Prevent hydration mismatch
  useEffect(() => { setMounted(true); }, []);

  // Fetch notifications with caching
  useEffect(() => {
    const fetchNotifs = async () => {
      try {
        const [countRes, listRes] = await Promise.all([
          notificationsAPI.unreadCount(),
          notificationsAPI.list(),
        ]);
        setUnreadCount(countRes.data.count || countRes.data.unread_count || 0);
        const notifData = listRes.data.results || (Array.isArray(listRes.data) ? listRes.data : []);
        setNotifications(notifData.slice(0, 8));
      } catch { /* silent */ }
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 60000);
    return () => clearInterval(interval);
  }, []);

  // Handle real-time WebSocket notification messages
  useEffect(() => {
    if (lastMessage?.type === 'notification') {
      setUnreadCount(prev => prev + 1);
      setNotifications(prev => [lastMessage.data, ...prev].slice(0, 8));
      // Optional: show a browser notification
      if (Notification.permission === 'granted') {
        new Notification(lastMessage.data.title || 'إشعار جديد', {
          body: lastMessage.data.message || '',
          icon: '/logo.png',
        });
      }
    }
    if (lastMessage?.type === 'unread_count') {
      setUnreadCount(lastMessage.data.count || 0);
    }
  }, [lastMessage]);

  const handleLogout = () => {
    logout();
    toast.success(locale === 'ar' ? 'تم تسجيل الخروج بنجاح' : 'Logged out successfully');
    return <Navigate to="/login" replace />;
  };

  const navSections = [
    {
      title: t('main'),
      items: [
        { name: t('dashboard'), path: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
      ],
    },
    {
      title: t('sales'),
      items: [
        { name: t('salesOrders'), path: '/orders', icon: ShoppingCart, roles: ['admin', 'warehouse', 'sales', 'accountant'] },
        { name: t('customers'), path: '/customers', icon: UsersRound, roles: ['admin', 'sales', 'accountant'] },
      ],
    },
    {
      title: t('accounting'),
      items: [
        { name: t('chartOfAccounts'), path: '/accounts', icon: BookOpen, roles: ['admin', 'accountant'] },
        { name: t('journalEntries'), path: '/journal-entries', icon: FileText, roles: ['admin', 'accountant'] },
        { name: t('financialReports'), path: '/reports', icon: BarChart3, roles: ['admin', 'accountant', 'sales'] },
      ],
    },
    {
      title: t('hr'),
      items: [
        { name: t('employees'), path: '/employees', icon: UserCog, roles: ['admin', 'hr'] },
        { name: t('attendance'), path: '/attendance', icon: ClipboardList, roles: ['admin', 'hr'] },
        { name: t('payroll'), path: '/payroll', icon: Wallet, roles: ['admin', 'accountant', 'hr'] },
      ],
    },
    {
      title: t('purchasesAndProjects'),
      items: [
        { name: t('purchases'), path: '/purchases', icon: Truck, roles: ['admin', 'warehouse', 'sales', 'accountant', 'purchasing'] },
        { name: t('projects'), path: '/projects', icon: FolderKanban, roles: ['admin', 'sales', 'accountant', 'project_manager'] },
        { name: t('documents'), path: '/documents', icon: FolderOpen, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
        { name: t('contracts'), path: '/contracts', icon: ScrollText, roles: ['admin', 'sales', 'accountant'] },
      ],
    },
    {
      title: t('finance'),
      items: [
        { name: t('invoicing'), path: '/invoicing', icon: Receipt, roles: ['admin', 'accountant', 'sales'] },
        { name: t('payments'), path: '/payments', icon: Landmark, roles: ['admin', 'accountant'] },
        { name: t('assets'), path: '/assets', icon: Building2, roles: ['admin', 'accountant'] },
      ],
    },
    {
      title: t('inventoryManagement'),
      items: [
        { name: t('products'), path: '/products', icon: Package, roles: ['admin', 'warehouse', 'sales', 'accountant'] },
        { name: t('warehouse'), path: '/warehouse', icon: WarehouseIcon, roles: ['admin', 'warehouse'] },
        { name: t('pos'), path: '/pos', icon: Store, roles: ['admin', 'sales', 'warehouse'] },
      ],
    },
    {
      title: t('reports'),
      items: [
        { name: t('comprehensiveReport'), path: '/final-report', icon: PieChart, roles: ['admin', 'accountant'] },
        { name: t('advancedReports'), path: '/advanced-reports', icon: BarChart3, roles: ['admin', 'accountant', 'sales'] },
      ],
    },
    {
      title: t('admin'),
      items: [
        { name: t('notifications'), path: '/notifications', icon: Bell, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
        { name: t('profile'), path: '/profile', icon: User, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
        { name: t('users'), path: '/users', icon: Users, roles: ['admin'] },
        { name: t('videoInstructions'), path: '/video-instructions', icon: Video, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
      ],
    },
    {
      title: t('system'),
      items: [
        { name: t('auditLog'), path: '/audit-log', icon: ClipboardCheck, roles: ['admin'], permission: 'auditlog_view' },
        { name: t('permissions'), path: '/permissions', icon: Shield, roles: ['admin'], permission: 'permissions_view' },
        { name: t('reportsCenter'), path: '/reports-center', icon: FileSpreadsheet, roles: ['admin', 'accountant', 'sales'], permission: 'reports_view' },
      ],
    },
    {
      title: t('maintenance'),
      items: [
        { name: t('backup'), path: '/backup', icon: Database, roles: ['admin'], permission: 'backup_manage' },
        { name: t('errorLog'), path: '/error-log', icon: Bug, roles: ['admin'] },
        { name: t('systemSettings'), path: '/system-settings', icon: Settings, roles: ['admin'] },
        { name: t('cronJobs'), path: '/cron-jobs', icon: Clock, roles: ['admin'] },
      ],
    },
  ];

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  if (!mounted) return null;

  const sidebarWidth = sidebarCollapsed ? 'w-20' : 'w-64';

  return (
    <div className={`flex h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-300`} dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 ${isRTL ? 'right-0' : 'left-0'} z-50 ${sidebarWidth} bg-gradient-to-b from-riadah-500 via-riadah-700 to-riadah-900 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-white transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 overflow-y-auto overflow-x-hidden ${
          sidebarOpen ? 'translate-x-0' : (isRTL ? 'translate-x-full' : '-translate-x-full')
        } ${sidebarCollapsed ? 'lg:w-20' : 'lg:w-64'}`}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between h-16 px-4 bg-black/10 dark:bg-black/20 sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3 min-w-0">
            <img src="/logo.png" alt="RIADAH" className="w-8 h-8 object-contain flex-shrink-0" />
            {!sidebarCollapsed && (
              <span className="text-lg font-bold truncate animate-fade-in tracking-wide">
                RIADAH
              </span>
            )}
          </div>
          <button
            onClick={() => { setSidebarOpen(false); }}
            className="lg:hidden text-white/70 hover:text-white hover:bg-white/10 p-1 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User card */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-white/10 animate-fade-in">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-400 to-riadah-500 flex items-center justify-center text-sm font-bold shadow-lg flex-shrink-0">
                {user?.first_name?.[0] || user?.username?.[0] || 'م'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate">{user?.first_name || user?.username}</p>
                <p className="text-xs text-accent-300 dark:text-gray-400 truncate">{user?.role_display}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="mt-2 px-2 space-y-3 pb-4">
          {navSections.map((section) => {
            const visibleItems = section.items.filter(item => {
              if (!item.roles.includes(user?.role)) return false;
              if (item.permission && !hasPermission(item.permission)) return false;
              return true;
            });
            if (visibleItems.length === 0) return null;
            return (
              <div key={section.title} className="animate-fade-in">
                {!sidebarCollapsed && (
                  <p className="px-4 py-1 text-[10px] font-bold text-accent-300/70 dark:text-gray-500 uppercase tracking-widest">
                    {section.title}
                  </p>
                )}
                <div className="space-y-0.5 mt-1">
                  {visibleItems.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.path);
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setSidebarOpen(false)}
                        title={sidebarCollapsed ? item.name : ''}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                          sidebarCollapsed ? 'justify-center' : ''
                        } ${
                          active
                            ? 'bg-accent-500/20 text-white shadow-lg shadow-accent-500/10 backdrop-blur-sm'
                            : 'text-blue-100/80 hover:bg-white/10 hover:text-white dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-200'
                        }`}
                      >
                        <Icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-110 ${active ? 'text-accent-400' : ''}`} />
                        {!sidebarCollapsed && <span className="truncate">{item.name}</span>}
                        {active && !sidebarCollapsed && (
                          <div className={`w-1.5 h-1.5 rounded-full bg-accent-500 ${isRTL ? 'mr-auto' : 'ml-auto'}`} />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="sticky bottom-0 bg-black/10 dark:bg-black/20 backdrop-blur-sm border-t border-white/10 p-3">
          {/* Collapse button (desktop) */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden lg:flex items-center gap-3 w-full px-3 py-2 rounded-xl text-sm text-blue-200/70 hover:bg-white/10 hover:text-white transition-colors mb-1"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${sidebarCollapsed ? '-rotate-90' : ''}`} />
            {!sidebarCollapsed && <span>{isRTL ? 'طي القائمة' : 'Collapse'}</span>}
          </button>
          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-red-300 hover:bg-red-500/20 hover:text-red-200 transition-colors"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span>{t('logout')}</span>}
          </button>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Header */}
        <header className="h-16 glass border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 lg:px-6 z-30 transition-colors duration-300">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex items-center gap-2 lg:gap-3">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="relative p-2.5 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-300 hover:scale-105 active:scale-95 min-w-[44px] min-h-[44px]"
              title={isDark ? t('lightMode') : t('darkMode')}
            >
              <Sun className={`w-5 h-5 absolute inset-0 m-auto transition-all duration-300 ${isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'}`} />
              <Moon className={`w-5 h-5 transition-all duration-300 ${isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'}`} />
            </button>

            {/* Language Toggle */}
            <button
              onClick={toggleLocale}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-300 hover:scale-105 active:scale-95 min-w-[44px] min-h-[44px]"
              title={t('language')}
            >
              <Languages className="w-4 h-4" />
              <span className="hidden sm:inline">{locale === 'ar' ? 'EN' : 'عربي'}</span>
            </button>

            {/* WebSocket connection indicator */}
            <div className="relative" title={isConnected ? (locale === 'ar' ? 'متصل' : 'Connected') : (locale === 'ar' ? 'غير متصل' : 'Disconnected')}>
              <span className={`block w-2 h-2 rounded-full transition-colors duration-300 ${isConnected ? 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.5)]' : 'bg-gray-400'}`} />
            </div>

            {/* Notification bell */}
            <div className="relative">
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-300 hover:scale-105 active:scale-95 min-w-[44px] min-h-[44px]"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -left-0.5 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-bounce-subtle shadow-lg">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notifications dropdown */}
              {notifOpen && (
                <div className={`absolute ${isRTL ? 'left-0' : 'right-0'} top-full mt-2 w-80 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden animate-fade-in-down`}>
                  <div className="flex items-center justify-between px-4 py-3 border-b-2 border-accent-500/30 dark:border-accent-500/20 bg-gray-50 dark:bg-gray-800/80">
                    <h4 className="font-semibold text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                      <Bell className="w-4 h-4" /> {t('notifications')}
                    </h4>
                    {unreadCount > 0 && (
                      <button
                        onClick={async () => {
                          try {
                            await notificationsAPI.markAllRead();
                            setUnreadCount(0);
                            setNotifications(notifications.map(n => ({ ...n, is_read: true })));
                          } catch { /* silent */ }
                        }}
                        className="text-xs text-accent-500 hover:text-accent-600 font-medium flex items-center gap-1"
                      >
                        <Check className="w-3 h-3" /> {t('markAllRead')}
                      </button>
                    )}
                  </div>
                  <div className="max-h-72 overflow-y-auto divide-y divide-gray-50 dark:divide-gray-700/50">
                    {notifications.length > 0 ? notifications.map((notif, i) => (
                      <div
                        key={notif.id || i}
                        className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer ${!notif.is_read ? 'bg-riadah-50/50 dark:bg-riadah-900/10' : ''}`}
                        onClick={async () => {
                          if (!notif.is_read) {
                            try {
                              await notificationsAPI.markRead(notif.id);
                              setUnreadCount(prev => Math.max(0, prev - 1));
                              setNotifications(notifications.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
                            } catch { /* silent */ }
                          }
                        }}
                      >
                        <div className="flex items-start gap-2">
                          {!notif.is_read && <div className="w-2 h-2 rounded-full bg-riadah-500 flex-shrink-0 mt-1.5 animate-pulse-soft" />}
                          <div className={!notif.is_read ? (isRTL ? 'mr-4' : 'ml-4') : ''}>
                            <p className={`text-sm ${notif.is_read ? 'text-gray-600 dark:text-gray-400' : 'font-medium text-gray-900 dark:text-gray-100'}`}>
                              {notif.title || notif.message || ''}
                            </p>
                            <p className="text-xs text-gray-400 mt-0.5">{notif.created_at}</p>
                          </div>
                        </div>
                      </div>
                    )) : (
                      <div className="p-6 text-center">
                        <BellOff className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                        <p className="text-sm text-gray-400 dark:text-gray-500">{t('noNotifications')}</p>
                      </div>
                    )}
                  </div>
                  <div className="border-t border-gray-100 dark:border-gray-700 px-4 py-2">
                    <Link
                      to="/notifications"
                      onClick={() => setNotifOpen(false)}
                      className="flex items-center justify-center gap-1.5 text-sm text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 font-medium py-1 transition-colors"
                    >
                      {t('viewAll')}
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Date display */}
            <div className="hidden md:block text-sm text-gray-500 dark:text-gray-400 px-2">
              {new Date().toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
              })}
            </div>
          </div>
        </header>

        {/* Page content with animation */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 pb-20 md:pb-6 bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
          <div key={location.pathname} className="animate-page-enter">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation - Role-based */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-[0_-2px_10px_rgba(0,0,0,0.08)] dark:shadow-[0_-2px_10px_rgba(0,0,0,0.3)]">
        <div className="flex items-center justify-around px-1 py-1">
          {[
            { name: t('dashboard'), path: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
            { name: t('products'), path: '/products', icon: Package, roles: ['admin', 'warehouse', 'sales', 'accountant'] },
            { name: t('salesOrders'), path: '/orders', icon: ShoppingCart, roles: ['admin', 'warehouse', 'sales', 'accountant'] },
            { name: t('purchases'), path: '/purchases', icon: Truck, roles: ['admin', 'warehouse', 'sales', 'accountant', 'purchasing'] },
            { name: t('warehouse'), path: '/warehouse', icon: WarehouseIcon, roles: ['admin', 'warehouse'] },
            { name: t('employees'), path: '/employees', icon: UserCog, roles: ['admin', 'hr'] },
            { name: t('projects'), path: '/projects', icon: FolderKanban, roles: ['admin', 'sales', 'accountant', 'project_manager'] },
            { name: t('profile'), path: '/profile', icon: User, roles: ['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager'] },
          ].filter(item => item.roles.includes(user?.role)).slice(0, 5).map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center min-w-[56px] py-1.5 rounded-xl text-[10px] font-medium transition-colors ${
                  active
                    ? 'text-accent-500 dark:text-accent-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-accent-500 dark:text-accent-400' : ''}`} />
                <span className="mt-0.5 truncate max-w-[64px] text-center leading-tight">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
