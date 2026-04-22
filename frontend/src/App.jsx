/**
 * Main application component with routing, providers, and lazy loading.
 * All routes are protected by role-based and permission-based access control.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Suspense, lazy } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { I18nProvider } from './i18n/I18nContext';
import MainLayout from './components/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy-loaded pages for performance
const LoginPage = lazy(() => import('./pages/LoginPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const UsersPage = lazy(() => import('./pages/UsersPage'));
const ProductsPage = lazy(() => import('./pages/ProductsPage'));
const CustomersPage = lazy(() => import('./pages/CustomersPage'));
const SalesOrdersPage = lazy(() => import('./pages/SalesOrdersPage'));
const CreateOrderPage = lazy(() => import('./pages/CreateOrderPage'));
const OrderDetailPage = lazy(() => import('./pages/OrderDetailPage'));
const ChartOfAccountsPage = lazy(() => import('./pages/ChartOfAccountsPage'));
const JournalEntriesPage = lazy(() => import('./pages/JournalEntriesPage'));
const FinancialReportsPage = lazy(() => import('./pages/FinancialReportsPage'));
const EmployeesPage = lazy(() => import('./pages/EmployeesPage'));
const AttendanceLeavesPage = lazy(() => import('./pages/AttendanceLeavesPage'));
const FinalReportPage = lazy(() => import('./pages/FinalReportPage'));
const PurchasesPage = lazy(() => import('./pages/PurchasesPage'));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'));
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
const AuditLogPage = lazy(() => import('./pages/AuditLogPage'));
const PermissionsPage = lazy(() => import('./pages/PermissionsPage'));
const ReportsCenterPage = lazy(() => import('./pages/ReportsCenterPage'));
const BackupPage = lazy(() => import('./pages/BackupPage'));
const ErrorLogPage = lazy(() => import('./pages/ErrorLogPage'));
const SystemSettingsPage = lazy(() => import('./pages/SystemSettingsPage'));
const CronJobsPage = lazy(() => import('./pages/CronJobsPage'));
const VideoInstructionsPage = lazy(() => import('./pages/VideoInstructionsPage'));
const PayrollPage = lazy(() => import('./pages/PayrollPage'));
const InvoicingPage = lazy(() => import('./pages/InvoicingPage'));
const POSPage = lazy(() => import('./pages/POSPage'));
const WarehousePage = lazy(() => import('./pages/WarehousePage'));
const AssetsPage = lazy(() => import('./pages/AssetsPage'));
const ContractsPage = lazy(() => import('./pages/ContractsPage'));
const PaymentsPage = lazy(() => import('./pages/PaymentsPage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));
const AdvancedReportsPage = lazy(() => import('./pages/AdvancedReportsPage'));
const BudgetPage = lazy(() => import('./pages/BudgetPage'));
const TendersPage = lazy(() => import('./pages/TendersPage'));
const ManufacturingPage = lazy(() => import('./pages/ManufacturingPage'));
const ShippingPage = lazy(() => import('./pages/ShippingPage'));
const InsurancePage = lazy(() => import('./pages/InsurancePage'));
const ImportExportPage = lazy(() => import('./pages/ImportExportPage'));
const EquipMaintPage = lazy(() => import('./pages/EquipMaintPage'));
const CRMPage = lazy(() => import('./pages/CRMPage'));
const InternalAuditPage = lazy(() => import('./pages/InternalAuditPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));

function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<LoadingSpinner />}>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />

                {/* Protected routes with main layout */}
                <Route
                  element={
                    <ProtectedRoute>
                      <MainLayout />
                    </ProtectedRoute>
                  }
                >
                  {/* ===== القسم الرئيسي ===== */}
                  <Route path="/dashboard" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <DashboardPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== المبيعات ===== */}
                  <Route path="/orders" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant']}>
                      <SalesOrdersPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/orders/create" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
                      <CreateOrderPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/orders/:id" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant']}>
                      <OrderDetailPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/customers" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
                      <CustomersPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== المحاسبة ===== */}
                  <Route path="/accounts" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <ChartOfAccountsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/journal-entries" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <JournalEntriesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/reports" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <FinancialReportsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الموارد البشرية ===== */}
                  <Route path="/employees" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <EmployeesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/attendance" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <AttendanceLeavesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/payroll" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'hr']}>
                      <PayrollPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== المشتريات والمشاريع ===== */}
                  <Route path="/purchases" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant', 'purchasing']}>
                      <PurchasesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/documents" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <DocumentsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/projects" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'project_manager']}>
                      <ProjectsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/contracts" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
                      <ContractsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== المالية ===== */}
                  <Route path="/invoicing" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <InvoicingPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/payments" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <PaymentsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/assets" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <AssetsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== المخزون والمستودعات ===== */}
                  <Route path="/products" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant']}>
                      <ProductsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/warehouse" element={
                    <ProtectedRoute roles={['admin', 'warehouse']}>
                      <WarehousePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/pos" element={
                    <ProtectedRoute roles={['admin', 'sales', 'warehouse']}>
                      <POSPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التصنيع والعمليات ===== */}
                  <Route path="/manufacturing" element={
                    <ProtectedRoute roles={['admin', 'warehouse']}>
                      <ManufacturingPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/shipping" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales']}>
                      <ShippingPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الميزانية والعقود ===== */}
                  <Route path="/budget" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'project_manager']}>
                      <BudgetPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/tenders" element={
                    <ProtectedRoute roles={['admin', 'project_manager']}>
                      <TendersPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الاستيراد والتصدير ===== */}
                  <Route path="/import-export" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'purchasing']}>
                      <ImportExportPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== إدارة العملاء CRM ===== */}
                  <Route path="/crm" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التأمين ===== */}
                  <Route path="/insurance" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <InsurancePage />
                    </ProtectedRoute>
                  } />

                  {/* ===== صيانة المعدات ===== */}
                  <Route path="/equip-maint" element={
                    <ProtectedRoute roles={['admin', 'warehouse']}>
                      <EquipMaintPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التدقيق الداخلي ===== */}
                  <Route path="/internal-audit" element={
                    <ProtectedRoute roles={['admin']}>
                      <InternalAuditPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التحليلات المتقدمة ===== */}
                  <Route path="/analytics" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <AnalyticsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التقارير ===== */}
                  <Route path="/final-report" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <FinalReportPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الإدارة (Admin) ===== */}
                  <Route path="/notifications" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <NotificationsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/video-instructions" element={
                    <ProtectedRoute roles={['admin', 'warehouse', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <VideoInstructionsPage />
                    </ProtectedRoute>
                  } />
                  <Route
                    path="/users"
                    element={
                      <ProtectedRoute roles={['admin']}>
                        <UsersPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* ===== النظام (System) - with permission checks ===== */}
                  <Route path="/audit-log" element={
                    <ProtectedRoute roles={['admin']} permission="auditlog_view">
                      <AuditLogPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/permissions" element={
                    <ProtectedRoute roles={['admin']} permission="permissions_view">
                      <PermissionsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/reports-center" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']} permission="reports_view">
                      <ReportsCenterPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/advanced-reports" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <AdvancedReportsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الصيانة (Maintenance) ===== */}
                  <Route path="/backup" element={
                    <ProtectedRoute roles={['admin']} permission="backup_manage">
                      <BackupPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/error-log" element={
                    <ProtectedRoute roles={['admin']}>
                      <ErrorLogPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/system-settings" element={
                    <ProtectedRoute roles={['admin']}>
                      <SystemSettingsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/cron-jobs" element={
                    <ProtectedRoute roles={['admin']}>
                      <CronJobsPage />
                    </ProtectedRoute>
                  } />
                </Route>

                {/* Default redirect */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>

            {/* Toast notifications */}
            <Toaster
              position="top-center"
              toastOptions={{
                duration: 3000,
                style: {
                  fontFamily: 'Cairo, Amiri, sans-serif',
                  borderRadius: '12px',
                  padding: '12px 16px',
                  fontSize: '14px',
                },
                success: {
                  iconTheme: { primary: '#059669', secondary: '#fff' },
                },
                error: {
                  iconTheme: { primary: '#dc2626', secondary: '#fff' },
                },
              }}
            />
          </BrowserRouter>
        </AuthProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}

export default App;
