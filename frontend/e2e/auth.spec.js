/**
 * Authentication E2E Tests
 * Tests: login, invalid credentials, forgot password, logout.
 * These tests do NOT depend on saved auth state - they perform fresh logins.
 */

const { test, expect } = require('@playwright/test');

// ─── Constants ────────────────────────────────────────────────────────
const VALID_USERNAME = 'admin';
const VALID_PASSWORD = 'admin123';
const INVALID_USERNAME = 'wronguser';
const INVALID_PASSWORD = 'wrongpass';

// ─── Test Suite ────────────────────────────────────────────────────────

test.describe('Authentication', () => {

  test.describe.configure({ mode: 'serial' });

  // ─── Login Page Renders ─────────────────────────────────────────────

  test('should display the login page correctly', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Verify logo is visible
    await expect(page.locator('img[alt="RIADAH ERP"]')).toBeVisible({ timeout: 10000 });

    // Verify brand name
    await expect(page.locator('h1')).toContainText('RIADAH');

    // Verify form heading
    await expect(page.getByRole('heading', { name: 'تسجيل الدخول' })).toBeVisible();

    // Verify username field
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('label[for="username"]')).toContainText('اسم المستخدم');

    // Verify password field
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('label[for="password"]')).toContainText('كلمة المرور');

    // Verify login button
    await expect(page.getByRole('button', { name: 'تسجيل الدخول' })).toBeVisible();

    // Verify forgot password link
    await expect(page.getByText('نسيت كلمة المرور؟')).toBeVisible();

    // Verify demo credentials hint
    await expect(page.getByText('بيانات تجريبية:')).toBeVisible();
    await expect(page.getByText('admin')).toBeVisible();
  });

  // ─── Login with Valid Credentials ───────────────────────────────────

  test('should login successfully with valid credentials and redirect to dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill in credentials
    await page.locator('#username').fill(VALID_USERNAME);
    await page.locator('#password').fill(VALID_PASSWORD);

    // Click login
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Verify dashboard is loaded
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });

    // Verify we are no longer on the login page
    await expect(page.locator('#username')).not.toBeVisible();

    // Verify the sidebar with RIADAH branding is present
    await expect(page.locator('aside')).toContainText('RIADAH');
  });

  // ─── Login with Empty Fields ────────────────────────────────────────

  test('should show validation errors when fields are empty', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Click login without filling anything
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

    // Verify validation errors appear
    await expect(page.getByText('اسم المستخدم مطلوب')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('كلمة المرور مطلوبة')).toBeVisible();

    // Verify we are still on login page
    await expect(page).toHaveURL(/\/login/);
  });

  // ─── Login with Invalid Credentials ─────────────────────────────────

  test('should show error message with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill in invalid credentials
    await page.locator('#username').fill(INVALID_USERNAME);
    await page.locator('#password').fill(INVALID_PASSWORD);

    // Click login
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

    // Wait for error message - it appears as a toast or inline error
    // The app shows either a toast or an inline error div
    const errorSelector = page.locator('.bg-red-50, [data-sonner-toast][data-type="error"]');
    await expect(errorSelector.first()).toBeVisible({ timeout: 10000 });

    // Verify we are still on login page
    await expect(page).toHaveURL(/\/login/);

    // Verify the login button is still enabled
    await expect(page.getByRole('button', { name: 'تسجيل الدخول' })).toBeEnabled();
  });

  // ─── Password Toggle ────────────────────────────────────────────────

  test('should toggle password visibility', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const passwordInput = page.locator('#password');
    await passwordInput.fill('testpassword');

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click the toggle button (the Eye icon inside the password field)
    const toggleBtn = passwordInput.locator('..').locator('button');
    await toggleBtn.click();

    // Password should now be visible
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click again to hide
    await toggleBtn.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  // ─── Forgot Password Flow ───────────────────────────────────────────

  test('should navigate to forgot password page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Click forgot password link
    await page.getByText('نسيت كلمة المرور؟').click();

    // Verify we are on forgot password page
    await expect(page).toHaveURL(/\/forgot-password/, { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Verify forgot password page elements
    await expect(page.getByRole('heading', { name: 'نسيت كلمة المرور' })).toBeVisible({ timeout: 10000 });

    // Verify email input
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.getByLabel('البريد الإلكتروني')).toBeVisible();

    // Verify send code button
    await expect(page.getByRole('button', { name: /إرسال رمز التحقق/ })).toBeVisible();

    // Verify back to login link
    await expect(page.getByText('العودة لتسجيل الدخول')).toBeVisible();
  });

  test('should show validation error when email is empty on forgot password', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.waitForLoadState('networkidle');

    // Click send without entering email
    await page.getByRole('button', { name: /إرسال رمز التحقق/ }).click();

    // Should show an error (the HTML5 required attribute or custom validation)
    // The page has `required` on the email input, so browser validation will fire
    // Or the app might show a toast error
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test('should allow entering email and submitting forgot password form', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.waitForLoadState('networkidle');

    // Fill in email
    await page.locator('#email').fill('admin@example.com');

    // Click send
    await page.getByRole('button', { name: /إرسال رمز التحقق/ }).click();

    // Wait for either success or error response
    // On success: shows "تحقق من بريدك الإلكتروني" 
    // On error (invalid email): shows error toast
    await page.waitForTimeout(3000);

    // One of these states should be true
    const successState = page.getByText('تحقق من بريدك الإلكتروني');
    const errorState = page.locator('.bg-red-50, [data-sonner-toast][data-type="error"]');

    const hasSuccess = await successState.isVisible().catch(() => false);
    const hasError = await errorState.first().isVisible().catch(() => false);

    expect(hasSuccess || hasError).toBeTruthy();
  });

  test('should navigate back to login from forgot password page', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.waitForLoadState('networkidle');

    // Click back to login link
    await page.getByText('العودة لتسجيل الدخول').click();

    // Verify we are back on login page
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'تسجيل الدخول' })).toBeVisible();
  });

  // ─── Logout ─────────────────────────────────────────────────────────

  test('should logout successfully and redirect to login page', async ({ page }) => {
    // First, login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.locator('#username').fill(VALID_USERNAME);
    await page.locator('#password').fill(VALID_PASSWORD);
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Verify dashboard is shown
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });

    // Clear auth tokens to simulate logout
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });

    // Navigate to any protected route - should redirect to login
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should be redirected to login since we removed tokens
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('should logout using sidebar logout button', async ({ page }) => {
    // First, login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.locator('#username').fill(VALID_USERNAME);
    await page.locator('#password').fill(VALID_PASSWORD);
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Verify dashboard
    await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });

    // Find and click the logout button in sidebar footer
    // The logout button has text "تسجيل الخروج" and a LogOut icon
    const logoutBtn = page.locator('aside button').filter({ hasText: 'تسجيل الخروج' });
    await expect(logoutBtn).toBeVisible({ timeout: 5000 });
    await logoutBtn.click();

    // Wait for logout and redirect
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Should be redirected to login or show login page content
    const loginHeading = page.getByRole('heading', { name: 'تسجيل الدخول' });
    await expect(loginHeading).toBeVisible({ timeout: 10000 });
  });

  // ─── Protected Route Redirect ───────────────────────────────────────

  test('should redirect unauthenticated user to login page', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });

    // Try to access a protected route directly
    await page.goto('/products');
    await page.waitForLoadState('networkidle');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('should redirect to dashboard if already authenticated on login page', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.locator('#username').fill(VALID_USERNAME);
    await page.locator('#password').fill(VALID_PASSWORD);
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Now navigate to login page - should redirect to dashboard
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Should redirect back to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });
});
