import { test as base, expect } from '@playwright/test';
import type { BrowserContext, Page } from '@playwright/test';
import { registerUser } from './helpers/auth.ts';
import { truncateTables } from './helpers/db.ts';

let fixtureCounter = 0;

/** Short unique suffix that fits within the 20-char username limit. */
function uniqueId(): string {
  return (++fixtureCounter).toString(36) + Date.now().toString(36).slice(-4);
}

interface PlayerFixture {
  page: Page;
  context: BrowserContext;
  username: string;
  password: string;
}

export const test = base.extend<{
  dbCleanup: void;
  player1: PlayerFixture;
  player2: PlayerFixture;
}>({
  // Truncate tables before each test (auto-fixture)
  dbCleanup: [async ({}, use) => {
    await truncateTables();
    await use();
  }, { auto: true }],

  player1: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const username = `p1_${uniqueId()}`;
    const password = 'TestPass123!';
    await registerUser(page, username, password);
    await use({ page, context, username, password });
    await context.close();
  },

  player2: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const username = `p2_${uniqueId()}`;
    const password = 'TestPass123!';
    await registerUser(page, username, password);
    await use({ page, context, username, password });
    await context.close();
  },
});

export { expect };
