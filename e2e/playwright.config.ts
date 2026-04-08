import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(import.meta.dirname, '.env.test') });

const projectRoot = path.resolve(import.meta.dirname, '..');

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  retries: 0,
  globalSetup: './global-setup.ts',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'uv run uvicorn connect4.api.app:app --host 127.0.0.1 --port 8000',
      port: 8000,
      cwd: projectRoot,
      env: {
        ...process.env,
        POSTGRES_DB: 'connect4_test',
        DISABLE_RATE_LIMIT: '1',
        COOKIE_SECURE: '0',
      },
      reuseExistingServer: !process.env.CI,
      timeout: 15_000,
    },
    {
      command: 'npm run dev',
      port: 5173,
      cwd: path.resolve(projectRoot, 'frontend'),
      reuseExistingServer: !process.env.CI,
      timeout: 15_000,
    },
  ],
});
