import { test, expect } from '../fixtures.ts';
import { playMove, playMoves } from '../helpers/game.ts';

/** Helper: player1 creates a game, player2 joins via URL, both see the board. */
async function setupGame(
  player1: { page: import('@playwright/test').Page },
  player2: { page: import('@playwright/test').Page },
) {
  // Player1 creates a game
  await player1.page.locator('button:has-text("New Game")').click();
  await expect(player1.page).toHaveURL(/\/games\/.+/);
  await expect(player1.page.locator('.waiting-view')).toBeVisible();

  // Get game URL
  const gameUrl = player1.page.url();

  // Player2 navigates to the game URL and joins
  await player2.page.goto(gameUrl);
  await player2.page.locator('button:has-text("Join Game")').waitFor({ timeout: 5_000 });
  await player2.page.locator('button:has-text("Join Game")').click();

  // Wait for both boards to be ready
  await expect(player1.page.locator('[role="grid"]')).toBeVisible({ timeout: 5_000 });
  await expect(player2.page.locator('[role="grid"]')).toBeVisible({ timeout: 5_000 });
}

test.describe('Two-player game', () => {
  test('SSE: player joined transitions creator from waiting to board', async ({ player1, player2 }) => {
    // Player1 creates a game
    await player1.page.locator('button:has-text("New Game")').click();
    await expect(player1.page).toHaveURL(/\/games\/.+/);
    await expect(player1.page.locator('.waiting-view')).toBeVisible();

    const gameUrl = player1.page.url();

    // Player2 navigates to the game and joins
    await player2.page.goto(gameUrl);
    await player2.page.locator('button:has-text("Join Game")').waitFor({ timeout: 5_000 });
    await player2.page.locator('button:has-text("Join Game")').click();

    // Player1 should auto-transition to board via SSE (no refresh)
    await expect(player1.page.locator('[role="grid"]')).toBeVisible({ timeout: 5_000 });
    await expect(player1.page.locator('.waiting-view')).not.toBeVisible();
  });

  test('SSE: move propagation between players', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // Player1 plays column 4
    await playMove(player1.page, 4);

    // Player2 should see the move via SSE
    await expect(player2.page.locator('.move-entry').first()).toBeVisible({ timeout: 5_000 });

    // Player2's status should show "Your turn"
    await expect(player2.page.locator('.status-badge')).toHaveText('Your turn');
  });

  test('full game to vertical win', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // Player1 stacks column 1, Player2 plays column 2
    // Moves: P1:1, P2:2, P1:1, P2:2, P1:1, P2:2, P1:1 (player1 wins vertical)
    await playMoves(player1.page, player2.page, [1, 2, 1, 2, 1, 2, 1]);

    // Player1 should see "You won"
    await expect(player1.page.locator('.status-badge')).toHaveText('You won', { timeout: 5_000 });

    // Player2 should see "You lost"
    await expect(player2.page.locator('.status-badge')).toHaveText('You lost', { timeout: 5_000 });

    // Winning cells should be highlighted
    await expect(player1.page.locator('.piece.win').first()).toBeVisible();
  });

  test('turn enforcement: board is disabled on opponents turn', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // It's player1's turn. Player2's board cells should be disabled.
    await expect(player2.page.locator('[aria-label="Column 4"]').first()).toBeDisabled();
    await expect(player2.page.locator('.status-badge')).toHaveText('Their turn');

    // Player1's board cells should be enabled
    await expect(player1.page.locator('[aria-label="Column 4"]').first()).toBeEnabled();
    await expect(player1.page.locator('.status-badge')).toHaveText('Your turn');
  });

  test('horizontal win with highlights', async ({ player1, player2 }) => {
    await setupGame(player1, player2);

    // Player1: cols 1,2,3,4. Player2: cols 1,2,3 (stacking on top of P1's pieces)
    await playMoves(player1.page, player2.page, [1, 1, 2, 2, 3, 3, 4]);

    await expect(player1.page.locator('.status-badge')).toHaveText('You won', { timeout: 5_000 });

    // 4 winning cells highlighted
    const winPieces = player1.page.locator('.piece.win');
    await expect(winPieces).toHaveCount(4);

    // Non-winning pieces should be dimmed
    await expect(player1.page.locator('.piece.dimmed').first()).toBeVisible();
  });
});
