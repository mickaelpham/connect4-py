import type { Page } from '@playwright/test';

export async function registerUser(page: Page, username: string, password: string): Promise<void> {
  await page.goto('/register');
  await page.locator('input[autocomplete="username"]').fill(username);
  await page.locator('input[autocomplete="new-password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('/');
}

export async function loginUser(page: Page, username: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.locator('input[autocomplete="username"]').fill(username);
  await page.locator('input[autocomplete="current-password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('/');
}
