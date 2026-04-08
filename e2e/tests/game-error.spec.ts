import { test, expect } from '../fixtures.ts';
import { playMoves } from '../helpers/game.ts';

/** Helper: player1 creates a game, player2 joins via URL, both see the board. */
async function setupGame(
  player1: { page: import('@playwright/test').Page },
  player2: { page: import('@playwright/test').Page },
) {
  await player1.page.locator('button:has-text("New Game")').click();
  await expect(player1.page).toHaveURL(/\/games\/.+/);
  await expect(player1.page.locator('.waiting-view')).toBeVisible();

  const gameUrl = player1.page.url();
  await player2.page.goto(gameUrl);
  await player2.page.locator('button:has-text("Join Game")').waitFor({ timeout: 5_000 });
  await player2.page.locator('button:has-text("Join Game")').click();

  await expect(player1.page.locator('[role="grid"]')).toBeVisible({ timeout: 5_000 });
  await expect(player2.page.locator('[role="grid"]')).toBeVisible({ timeout: 5_000 });
}

test.describe('Game errors', () => {
  test('full column has disabled cells', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // Fill column 1 with 6 pieces (alternating players)
    await playMoves(player1.page, player2.page, [1, 1, 1, 1, 1, 1]);

    // It's player1's turn. Column 1 cells should all be disabled (column full).
    const col1Cells = player1.page.locator('[aria-label="Column 1"]');
    for (let i = 0; i < 6; i++) {
      await expect(col1Cells.nth(i)).toBeDisabled();
    }

    // But other columns should still be enabled
    await expect(player1.page.locator('[aria-label="Column 2"]').first()).toBeEnabled();
  });

  test('board is disabled after game is over', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // Play to a vertical win for player1
    await playMoves(player1.page, player2.page, [1, 2, 1, 2, 1, 2, 1]);

    await expect(player1.page.locator('.status-badge')).toHaveText('You won', { timeout: 5_000 });
    await expect(player2.page.locator('.status-badge')).toHaveText('You lost', { timeout: 5_000 });

    // Both players' boards should be fully disabled
    await expect(player1.page.locator('[aria-label="Column 1"]').first()).toBeDisabled();
    await expect(player2.page.locator('[aria-label="Column 1"]').first()).toBeDisabled();
  });

  test('game not found for invalid game ID', async ({ player1 }) => {
    await player1.page.goto('/games/nonexistent-game-id');

    // Should show "Game not found" error message
    await expect(player1.page.locator('p.error')).toContainText('not found', { ignoreCase: true, timeout: 5_000 });
  });
});
