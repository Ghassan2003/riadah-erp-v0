/**
 * Main application component with routing, providers, and lazy loading.
 * All routes are protected by role-based and permission-based access control.
 */

import { useAuth } from './context/AuthContext';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Suspense, lazy } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { I18nProvider } from './i18n/I18nContext';
import MainLayout from './components/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';
import AccessDeniedPage from './pages/AccessDeniedPage';

// Lazy-loaded pages for performance
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const AcceptInvitationPage = lazy(() => import('./pages/AcceptInvitationPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const SalesDashboard = lazy(() => import('./pages/SalesDashboard'));

const AccountantDashboard = lazy(() => import('./pages/AccountantDashboard'));
const HRDashboard = lazy(() => import('./pages/HRDashboard'));
const PurchasingDashboard = lazy(() => import('./pages/PurchasingDashboard'));
const ProjectManagerDashboard = lazy(() => import('./pages/ProjectManagerDashboard'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const UsersPage = lazy(() => import('./pages/UsersPage'));

const CustomersPage = lazy(() => import('./pages/CustomersPage'));
const SalesOrdersPage = lazy(() => import('./pages/SalesOrdersPage'));
const CreateOrderPage = lazy(() => import('./pages/CreateOrderPage'));
const OrderDetailPage = lazy(() => import('./pages/OrderDetailPage'));
const ChartOfAccountsPage = lazy(() => import('./pages/ChartOfAccountsPage'));
const JournalEntriesPage = lazy(() => import('./pages/JournalEntriesPage'));
const FinancialReportsPage = lazy(() => import('./pages/FinancialReportsPage'));
const FiscalClosurePage = lazy(() => import('./pages/FiscalClosurePage'));
const BranchesPage = lazy(() => import('./pages/BranchesPage'));
const CurrenciesPage = lazy(() => import('./pages/CurrenciesPage'));
const CostAllocationPage = lazy(() => import('./pages/CostAllocationPage'));
const EmployeesPage = lazy(() => import('./pages/EmployeesPage'));
const AttendanceLeavesPage = lazy(() => import('./pages/AttendanceLeavesPage'));
const DepartmentsPage = lazy(() => import('./pages/DepartmentsPage'));
const ShiftsPage = lazy(() => import('./pages/ShiftsPage'));
const PerformancePage = lazy(() => import('./pages/PerformancePage'));
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

const PaymentsPage = lazy(() => import('./pages/PaymentsPage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));
const AdvancedReportsPage = lazy(() => import('./pages/AdvancedReportsPage'));
const TendersPage = lazy(() => import('./pages/TendersPage'));
const ImportExportPage = lazy(() => import('./pages/ImportExportPage'));
const EquipMaintPage = lazy(() => import('./pages/EquipMaintPage'));
const CRMPage = lazy(() => import('./pages/CRMPage'));
const CRMPipelinePage = lazy(() => import('./pages/CRMPipelinePage'));
const LeadDetailPage = lazy(() => import('./pages/LeadDetailPage'));
const CRMAnalyticsPage = lazy(() => import('./pages/CRMAnalyticsPage'));
const ProjectsRiskPage = lazy(() => import('./pages/ProjectsRiskPage'));
const ProjectsBudgetPage = lazy(() => import('./pages/ProjectsBudgetPage'));
const CRMTicketsPage = lazy(() => import('./pages/CRMTicketsPage'));
const CRMQuotationsPage = lazy(() => import('./pages/CRMQuotationsPage'));
const POSManagementPage = lazy(() => import('./pages/POSManagementPage'));
const EmployeeSelfServicePage = lazy(() => import('./pages/EmployeeSelfServicePage'));
const HolidayCalendarPage = lazy(() => import('./pages/HolidayCalendarPage'));
const PayslipsPage = lazy(() => import('./pages/PayslipsPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const ForecastingPage = lazy(() => import('./pages/ForecastingPage'));
const AnomalyDetectionPage = lazy(() => import('./pages/AnomalyDetectionPage'));
const CustomerInsightsPage = lazy(() => import('./pages/CustomerInsightsPage'));
const FounderDashboardPage = lazy(() => import('./pages/FounderDashboardPage'));
const HRRecruitmentPage = lazy(() => import('./pages/HRRecruitmentPage'));
const HRTrainingPage = lazy(() => import('./pages/HRTrainingPage'));
const HROrgChartPage = lazy(() => import('./pages/HROrgChartPage'));

/* Role-based dashboard router */
function RoleDashboard() {
  const { user } = useAuth();
  const role = user?.role;
  switch (role) {
    case 'sales': return <SalesDashboard />;
    case 'accountant': return <AccountantDashboard />;
    case 'hr': return <HRDashboard />;
    case 'purchasing': return <PurchasingDashboard />;
    case 'project_manager': return <ProjectManagerDashboard />;
    default: return <DashboardPage />; // admin → sees everything
  }
}

/**
 * مكون التوجيه الذكي - يوجه المستخدم لصفحته الرئيسية حسب دوره
 * عند زيارة /dashboard مباشرة
 */
function SmartDashboardRedirect() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const role = user?.role;

  const roleMap = {
    sales: '/orders',
    accountant: '/accounts',
    hr: '/employees',
    purchasing: '/purchases',
    project_manager: '/projects',
  };

  // المدير يرى لوحة التحكم الشاملة
  // باقي الأدوار يمكنهم اختيار لوحة التحكم أو صفحتهم الرئيسية
  // نعرض لوحة التحكم الخاصة بهم
  return <RoleDashboard />;
}

function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<LoadingSpinner />}>
              <Routes>
                {/* Public routes */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/accept-invitation/:token" element={<AcceptInvitationPage />} />
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
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <RoleDashboard />
                    </ProtectedRoute>
                  } />

                  {/* ===== المبيعات ===== */}
                  <Route path="/orders" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
                      <SalesOrdersPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/orders/create" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
                      <CreateOrderPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/orders/:id" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant']}>
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
                  <Route path="/fiscal-closure" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <FiscalClosurePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/branches" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <BranchesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/currencies" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <CurrenciesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/cost-allocation" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <CostAllocationPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الموارد البشرية ===== */}
                  <Route path="/employees" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <EmployeesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/departments" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <DepartmentsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/attendance" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <AttendanceLeavesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/shifts" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <ShiftsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/performance" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <PerformancePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/payroll" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'hr']}>
                      <PayrollPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/recruitment" element={<ProtectedRoute roles={['admin', 'hr']}><HRRecruitmentPage /></ProtectedRoute>} />
                  <Route path="/training" element={<ProtectedRoute roles={['admin', 'hr']}><HRTrainingPage /></ProtectedRoute>} />
                  <Route path="/org-chart" element={<ProtectedRoute roles={['admin', 'hr', 'sales', 'project_manager']}><HROrgChartPage /></ProtectedRoute>} />

                  {/* ===== المشتريات والمشاريع ===== */}
                  <Route path="/purchases" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'purchasing']}>
                      <PurchasesPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/documents" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <DocumentsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/projects" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'project_manager']}>
                      <ProjectsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/projects/risks" element={
                    <ProtectedRoute roles={['admin', 'project_manager', 'accountant']}>
                      <ProjectsRiskPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/projects/budget" element={
                    <ProtectedRoute roles={['admin', 'project_manager', 'accountant']}>
                      <ProjectsBudgetPage />
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


                  {/* ===== نقاط البيع ===== */}
                  <Route path="/pos" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <POSPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/pos/management" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <POSManagementPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الميزانيات والمناقصات ===== */}
                  <Route path="/tenders" element={
                    <ProtectedRoute roles={['admin', 'project_manager']}>
                      <TendersPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الاستيراد والتصدير ===== */}
                  <Route path="/import-export" element={
                    <ProtectedRoute roles={['admin', 'purchasing']}>
                      <ImportExportPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== إدارة العملاء CRM ===== */}
                  <Route path="/crm" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/crm/tickets" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMTicketsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/crm/quotations" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMQuotationsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/crm/pipeline" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMPipelinePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/crm/leads/:id" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <LeadDetailPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/crm/analytics" element={
                    <ProtectedRoute roles={['admin', 'sales']}>
                      <CRMAnalyticsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/self-service" element={
                    <ProtectedRoute roles={['admin', 'hr', 'sales', 'accountant', 'purchasing', 'project_manager']}>
                      <EmployeeSelfServicePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/holidays" element={
                    <ProtectedRoute roles={['admin', 'hr']}>
                      <HolidayCalendarPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/payslips" element={
                    <ProtectedRoute roles={['admin', 'hr', 'accountant']}>
                      <PayslipsPage />
                    </ProtectedRoute>
                  } />



                  {/* ===== صيانة المعدات ===== */}
                  <Route path="/equip-maint" element={
                    <ProtectedRoute roles={['admin']}>
                      <EquipMaintPage />
                    </ProtectedRoute>
                  } />



                  {/* ===== التحليلات المتقدمة ===== */}
                  <Route path="/analytics" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <AnalyticsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/analytics/forecasting" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <ForecastingPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/analytics/anomalies" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <AnomalyDetectionPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/analytics/customers" element={
                    <ProtectedRoute roles={['admin', 'accountant', 'sales']}>
                      <CustomerInsightsPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== التقارير ===== */}
                  <Route path="/final-report" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <FinalReportPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== تمويل الشركات الناشئة / Startup Finance ===== */}
                  <Route path="/founder-dashboard" element={
                    <ProtectedRoute roles={['admin', 'accountant']}>
                      <FounderDashboardPage />
                    </ProtectedRoute>
                  } />

                  {/* ===== الإدارة (Admin) ===== */}
                  <Route path="/notifications" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <NotificationsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/video-instructions" element={
                    <ProtectedRoute roles={['admin', 'sales', 'accountant', 'hr', 'purchasing', 'project_manager']}>
                      <VideoInstructionsPage />
                    </ProtectedRoute>
                  } />
                  <Route
                    path="/users"
                    element={
                      <ProtectedRoute roles={['admin', 'hr']}>
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
                <Route path="*" element={<Navigate to="/" replace />} />
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
