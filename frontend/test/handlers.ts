import type { RequestHandler } from 'msw'

// Default handlers for API mocking in tests.
// Add handlers here for routes that most tests need.
// Override per-test with `server.use(...)`.
export const handlers: RequestHandler[] = []
