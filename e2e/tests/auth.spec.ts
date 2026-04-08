import { test, expect } from '../fixtures.ts';
import { loginUser, registerUser } from '../helpers/auth.ts';

let counter = 0;
function uid(): string {
  return (++counter).toString(36) + Date.now().toString(36).slice(-4);
}

test.describe('Authentication', () => {
  test('register new user and redirect to lobby', async ({ page }) => {
    const username = `reg_${uid()}`;
    await registerUser(page, username, 'TestPass123!');

    await expect(page).toHaveURL('/');
    await expect(page.locator('.player-name')).toHaveText(username);
  });

  test('login existing user', async ({ page }) => {
    const username = `log_${uid()}`;
    // Register first
    await registerUser(page, username, 'TestPass123!');
    // Logout
    await page.locator('.logout-btn').click();
    await expect(page).toHaveURL('/login');
    // Login
    await loginUser(page, username, 'TestPass123!');

    await expect(page).toHaveURL('/');
    await expect(page.locator('.player-name')).toHaveText(username);
  });

  test('logout redirects to login', async ({ page }) => {
    const username = `out_${uid()}`;
    await registerUser(page, username, 'TestPass123!');

    await page.locator('.logout-btn').click();

    await expect(page).toHaveURL('/login');
    await expect(page.locator('.player-name')).not.toBeVisible();
  });

  test('auth guard redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL('/login');
  });

  test('register shows validation errors for short username', async ({ page }) => {
    await page.goto('/register');
    await page.locator('input[autocomplete="username"]').fill('ab');
    await page.locator('input[autocomplete="new-password"]').fill('TestPass123!');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('.field-error')).toBeVisible();
  });

  test('register duplicate username shows server error', async ({ page }) => {
    const username = `dup_${uid()}`;
    await registerUser(page, username, 'TestPass123!');
    await page.locator('.logout-btn').click();

    // Try to register again with same username
    await page.goto('/register');
    await page.locator('input[autocomplete="username"]').fill(username);
    await page.locator('input[autocomplete="new-password"]').fill('TestPass123!');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('.server-error')).toBeVisible();
  });

  test('login with wrong password shows error', async ({ page }) => {
    const username = `wpw_${uid()}`;
    await registerUser(page, username, 'TestPass123!');
    await page.locator('.logout-btn').click();

    await page.goto('/login');
    await page.locator('input[autocomplete="username"]').fill(username);
    await page.locator('input[autocomplete="current-password"]').fill('WrongPassword!');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('.server-error')).toBeVisible();
  });
});
