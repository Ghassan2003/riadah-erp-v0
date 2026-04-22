/**
 * Dashboard E2E Tests
 * Tests: dashboard loads, stats visible, navigation items, mobile bottom nav.
 * Requires authenticated admin session.
 */

const { test, expect } = require('@playwright/test');

// ─── Authenticated Project Config ─────────────────────────────────────
// These tests require authentication. We login at the start of each test.

const VALID_USERNAME = 'admin';
const VALID_PASSWORD = 'admin123';

async function performLogin(page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.locator('#username').fill(VALID_USERNAME);
  await page.locator('#password').fill(VALID_PASSWORD);
  await page.getByRole('button', { name: 'تسجيل الدخول' }).click();
  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await page.waitForLoadState('networkidle');
}

test.describe('Dashboard', () => {

  test.beforeEach(async ({ page }) => {
    await performLogin(page);
    // Verify we landed on dashboard
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });
  });

  // ─── Dashboard Loads ────────────────────────────────────────────────

  test('should load the dashboard with correct heading and subtitle', async ({ page }) => {
    // Verify main heading
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible();

    // Verify subtitle
    await expect(page.getByText('نظرة عامة شاملة')).toBeVisible();
  });

  test('should display KPI stat cards for admin', async ({ page }) => {
    // Wait for dashboard data to load (API calls to settle)
    await page.waitForLoadState('networkidle');

    // The dashboard shows multiple stat cards. Look for expected Arabic labels:
    const expectedLabels = [
      'إجمالي المنتجات',
      'أوامر البيع',
      'صافي الربح',
      'عدد الموظفين',
    ];

    for (const label of expectedLabels) {
      // At least one stat card should contain this label
      const card = page.locator('text=' + label).first();
      await expect(card).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display chart sections', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Verify at least one chart heading is visible
    const chartHeadings = [
      'المبيعات الشهرية',
      'توزيع الإيرادات والمصروفات',
      'توزيع حالات أوامر البيع',
    ];

    // At least the monthly sales chart should be visible
    const monthlySales = page.getByText('المبيعات الشهرية');
    await expect(monthlySales).toBeVisible({ timeout: 10000 });
  });

  test('should display quick access section', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Verify quick access heading
    await expect(page.getByText('وصول سريع')).toBeVisible({ timeout: 10000 });

    // Verify some quick action buttons exist
    // Quick actions include products, orders, customers, etc.
    const quickActions = page.locator('text=وصول سريع').locator('..');
    await expect(quickActions.locator('button').first()).toBeVisible();
  });

  test('should display recent orders section or empty state', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Either "آخر الأوامر" heading should be visible
    const recentOrders = page.getByText('آخر الأوامر');
    const noRecentOrders = page.getByText('لا توجد أوامر حديثة');

    const hasRecent = await recentOrders.isVisible().catch(() => false);
    const hasEmpty = await noRecentOrders.isVisible().catch(() => false);

    expect(hasRecent || hasEmpty).toBeTruthy();
  });

  // ─── System Status Footer ───────────────────────────────────────────

  test('should show system status in footer', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for "النظام يعمل" (System is online) indicator
    const systemOnline = page.getByText('النظام يعمل');
    await expect(systemOnline).toBeVisible({ timeout: 10000 });

    // Verify version info
    await expect(page.getByText('v5.0')).toBeVisible();
  });

  // ─── Sidebar Navigation Items ───────────────────────────────────────

  test('should show all admin navigation items in sidebar', async ({ page }) => {
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();

    // Verify main navigation sections visible to admin
    const expectedNavItems = [
      'لوحة التحكم',       // Dashboard
      'أوامر البيع',       // Sales Orders
      'العملاء',            // Customers
      'إدارة المنتجات',    // Products
      'إدارة المستخدمين',  // Users (admin only)
      'الملف الشخصي',      // Profile
    ];

    for (const item of expectedNavItems) {
      await expect(sidebar.getByText(item)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show admin-only navigation items', async ({ page }) => {
    const sidebar = page.locator('aside');

    // Admin-specific navigation items
    const adminOnlyItems = [
      'إدارة المستخدمين',     // Users management
      'سجل الأخطاء',          // Error log
      'إعدادات النظام',       // System settings
      'المهام المجدولة',      // Cron jobs
    ];

    for (const item of adminOnlyItems) {
      await expect(sidebar.getByText(item)).toBeVisible({ timeout: 5000 });
    }
  });

  // ─── Sidebar Navigation ─────────────────────────────────────────────

  test('should navigate to products page via sidebar', async ({ page }) => {
    const sidebar = page.locator('aside');

    // Click on products link
    await sidebar.getByText('إدارة المنتجات').click();
    await page.waitForLoadState('networkidle');

    // Verify products page loaded
    await expect(page.getByRole('heading', { name: 'إدارة المنتجات' })).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveURL(/\/products/);
  });

  test('should navigate to orders page via sidebar', async ({ page }) => {
    const sidebar = page.locator('aside');

    await sidebar.getByText('أوامر البيع').click();
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'إدارة أوامر البيع' })).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveURL(/\/orders/);
  });

  // ─── Mobile Bottom Navigation ───────────────────────────────────────

  test('should show mobile bottom navigation on small viewport', async ({ browser }) => {
    // Create a mobile-sized context
    const context = await browser.newContext({
      viewport: { width: 375, height: 812 },
      locale: 'ar',
    });
    const page = await context.newPage();

    await performLogin(page);
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });

    // Wait for page to fully render
    await page.waitForLoadState('networkidle');

    // Verify mobile bottom nav is visible
    const mobileNav = page.locator('nav.fixed.bottom-0');
    await expect(mobileNav).toBeVisible({ timeout: 5000 });

    // Verify expected items in mobile nav for admin
    // Admin should see: لوحة التحكم, إدارة المنتجات, أوامر البيع, المشتريات, المستودعات
    const expectedMobileItems = [
      'لوحة التحكم',
      'إدارة المنتجات',
    ];

    for (const item of expectedMobileItems) {
      await expect(mobileNav.getByText(item)).toBeVisible({ timeout: 5000 });
    }

    await context.close();
  });

  test('should navigate using mobile bottom nav', async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 375, height: 812 },
      locale: 'ar',
    });
    const page = await context.newPage();

    await performLogin(page);
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Tap on products in mobile nav
    const mobileNav = page.locator('nav.fixed.bottom-0');
    await mobileNav.getByText('إدارة المنتجات').click();
    await page.waitForLoadState('networkidle');

    // Verify navigation
    await expect(page).toHaveURL(/\/products/, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'إدارة المنتجات' })).toBeVisible({ timeout: 10000 });

    await context.close();
  });

  // ─── Date Filter ───────────────────────────────────────────────────

  test('should display date filter controls on dashboard', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for date inputs on the dashboard
    const dateInputs = page.locator('input[type="date"]');
    const count = await dateInputs.count();

    // Dashboard should have at least 2 date inputs (from/to)
    expect(count).toBeGreaterThanOrEqual(2);
  });
});
