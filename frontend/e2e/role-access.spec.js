/**
 * Role-Based Access E2E Tests
 * Tests: admin access, unauthorized redirects, sidebar filtering by role.
 * Uses admin credentials; tests verify admin can access all pages
 * and that unauthorized navigation is handled correctly.
 */

const { test, expect } = require('@playwright/test');

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

test.describe('Role-Based Access Control', () => {

  test.beforeEach(async ({ page }) => {
    await performLogin(page);
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });
  });

  // ─── Admin Can Access All Pages ────────────────────────────────────

  test('admin should access dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access products page', async ({ page }) => {
    await page.goto('/products');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إدارة المنتجات' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access sales orders page', async ({ page }) => {
    await page.goto('/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إدارة أوامر البيع' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access create order page', async ({ page }) => {
    await page.goto('/orders/create');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إنشاء أمر بيع' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access customers page', async ({ page }) => {
    await page.goto('/customers');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إدارة العملاء' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access chart of accounts page', async ({ page }) => {
    await page.goto('/accounts');
    await page.waitForLoadState('networkidle');
    // The page should load without redirecting to dashboard
    await expect(page).toHaveURL(/\/accounts/, { timeout: 10000 });
  });

  test('admin should access employees page', async ({ page }) => {
    await page.goto('/employees');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إدارة الموظفين' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access users management page', async ({ page }) => {
    await page.goto('/users');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'إدارة المستخدمين' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access warehouse page', async ({ page }) => {
    await page.goto('/warehouse');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/warehouse/, { timeout: 10000 });
  });

  test('admin should access profile page', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'الملف الشخصي' })).toBeVisible({ timeout: 10000 });
  });

  test('admin should access system settings page', async ({ page }) => {
    await page.goto('/system-settings');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/system-settings/, { timeout: 10000 });
  });

  // ─── Sidebar Filtering by Role ─────────────────────────────────────

  test('sidebar should show role-appropriate navigation items for admin', async ({ page }) => {
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();

    // These sections should be visible to admin
    const adminVisibleSections = [
      { text: 'الرئيسية', check: true },
      { text: 'المبيعات', check: true },
      { text: 'المحاسبة', check: true },
      { text: 'الموارد البشرية', check: true },
      { text: 'المشتريات والمشاريع', check: true },
      { text: 'المالية والتحصيلات', check: true },
      { text: 'المخزون والمستودعات', check: true },
      { text: 'الإدارة', check: true },
      { text: 'النظام', check: true },
      { text: 'التشغيل والصيانة', check: true },
    ];

    for (const section of adminVisibleSections) {
      if (section.check) {
        // Section titles are small uppercase text in sidebar
        const sectionEl = sidebar.locator('p', { hasText: section.text });
        const isVisible = await sectionEl.isVisible().catch(() => false);
        expect(isVisible).toBeTruthy();
      }
    }
  });

  test('sidebar should include navigation links for all admin-accessible pages', async ({ page }) => {
    const sidebar = page.locator('aside');

    // Verify key navigation links are present for admin
    const navLinks = [
      'لوحة التحكم',
      'أوامر البيع',
      'العملاء',
      'الدليل المحاسبي',
      'قيود اليومية',
      'التقارير المالية',
      'إدارة الموظفين',
      'الحضور والإجازات',
      'الرواتب',
      'المشتريات',
      'المشاريع',
      'المستندات',
      'العقود',
      'الفواتير',
      'المدفوعات',
      'الأصول الثابتة',
      'إدارة المنتجات',
      'المستودعات',
      'نقاط البيع',
      'التقرير الشامل',
      'إدارة المستخدمين',
    ];

    for (const link of navLinks) {
      const linkEl = sidebar.getByText(link);
      const isVisible = await linkEl.isVisible().catch(() => false);
      // Admin should see all these items
      expect(isVisible).toBeTruthy();
    }
  });

  // ─── Unauthenticated Redirect ──────────────────────────────────────

  test.describe('Unauthenticated Access', () => {

    test.beforeEach(async ({ page }) => {
      // Clear auth before each test
      await page.goto('/login');
      await page.evaluate(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      });
    });

    test('should redirect to login when accessing protected route without auth', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });

    test('should redirect to login when accessing admin-only route without auth', async ({ page }) => {
      await page.goto('/users');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });

    test('should redirect to login when accessing orders without auth', async ({ page }) => {
      await page.goto('/orders');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });
  });

  // ─── Direct URL Access After Logout ────────────────────────────────

  test('should redirect to dashboard for restricted pages when cleared auth', async ({ page }) => {
    // First login and verify dashboard
    await performLogin(page);
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });

    // Clear auth tokens
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });

    // Try to navigate to a protected page
    await page.goto('/products');
    await page.waitForLoadState('networkidle');

    // Should redirect to login since we cleared tokens
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });
});
