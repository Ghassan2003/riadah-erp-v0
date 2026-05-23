/**
 * E2E Test Setup - Authentication state management.
 * Login once and reuse the session across all tests for speed.
 */

const { test: setup, expect } = require('@playwright/test');

// ─── Authentication Helpers ────────────────────────────────────────────

/**
 * Perform a fresh login with the given credentials.
 * Returns the storage state that can be reused.
 */
async function authenticate(page, username = 'admin', password = 'admin123') {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // Fill username
  const usernameInput = page.locator('#username');
  await usernameInput.waitFor({ state: 'visible', timeout: 10000 });
  await usernameInput.fill(username);

  // Fill password
  const passwordInput = page.locator('#password');
  await passwordInput.fill(password);

  // Click login button
  const loginBtn = page.getByRole('button', { name: 'تسجيل الدخول' });
  await loginBtn.click();

  // Wait for navigation to dashboard
  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await page.waitForLoadState('networkidle');

  // Verify we're on the dashboard
  await expect(page.getByRole('heading', { name: 'لوحة التحكم' })).toBeVisible({ timeout: 10000 });
}

/**
 * Save authentication state to a file for reuse.
 */
async function globalSetup() {
  const { chromium } = require('@playwright/test');
  const browser = await chromium.launch();
  const context = await browser.newContext({ locale: 'ar' });
  const page = await context.newPage();

  try {
    await authenticate(page);
    // Save storage state (cookies, localStorage)
    await context.storageState({ path: './e2e/.auth/admin.json' });
    console.log('✅ Authentication state saved to e2e/.auth/admin.json');
  } catch (error) {
    console.error('❌ Failed to save authentication state:', error.message);
    // Create an empty auth state so tests don't crash
    await context.storageState({ path: './e2e/.auth/admin.json' });
  } finally {
    await browser.close();
  }
}

/**
 * Project-specific setup to create storage state before tests.
 */
async function setupAuthState() {
  const { chromium } = require('@playwright/test');
  const fs = require('fs');
  const path = require('path');

  const authDir = path.join(__dirname, '.auth');
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({ locale: 'ar' });
  const page = await context.newPage();

  try {
    await authenticate(page);
    await context.storageState({ path: path.join(authDir, 'admin.json' });
  } catch (error) {
    console.warn(`⚠️ Warning: Could not save auth state: ${error.message}`);
    // Create minimal state so tests using it fail gracefully
    await context.storageState({ path: path.join(authDir, 'admin.json' });
  } finally {
    await browser.close();
  }
}

// ─── Test Utilities ────────────────────────────────────────────────────

/**
 * Utility: Perform login and return authenticated page.
 * Use this for tests that need their own auth context.
 */
async function loginAs(page, username = 'admin', password = 'admin123') {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  await page.locator('#username').fill(username);
  await page.locator('#password').fill(password);
  await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

  // Handle potential 2FA screen - if present, skip
  try {
    await page.waitForSelector('text=المصادقة الثنائية', { timeout: 3000 });
    // 2FA is required - tests using this should handle it
    console.warn('⚠️ 2FA is enabled for this user. Tests may need adjustment.');
  } catch {
    // No 2FA - good, continue
  }

  await page.waitForURL('**/dashboard', { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle');
  return page;
}

/**
 * Utility: Clear all stored auth data.
 */
async function clearAuth(page) {
  await page.goto('/login');
  await page.evaluate(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  });
  await page.reload();
  await page.waitForLoadState('networkidle');
}

/**
 * Utility: Wait for API calls to settle.
 */
async function waitForApiSettle(page, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}

// Export for use in test files
module.exports = {
  authenticate,
  loginAs,
  clearAuth,
  waitForApiSettle,
  setupAuthState,
};
